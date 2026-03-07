"""采實文化（acmebook.com.tw）爬蟲實作。

DOM 結構（2026-03-07 確認）：
  目錄頁  : book_list.php?page_num=N&bookType_sn1=XX&bookType_sn=0
  詳情頁  : book.php?sn=NNNN&bookType_sn=0
  商品連結: a[href*="book.php?sn="] → sn 參數即書籍 ID
  書名    : <title> tag（無 h1/h2），去掉「| 采實出版集團」後綴
            備援：<meta property="og:title">
  定價    : 文字「定價 <strong>NNN</strong> 元」
  ISBN    : 文字「ISBN：XXXXXXXXXXXXX」（13 碼）
  庫存    : 無 schema.org / 無購物車；純書目網站，
            所有列表書籍均視為可售，僅排除含缺書關鍵字之頁面
"""
from __future__ import annotations

import re
from typing import Generator, Optional

from bs4 import BeautifulSoup

from models.book import Book
from scrapers.base import BaseScraper
from utils.http_client import HttpClient
from utils.logger import get_logger

logger = get_logger()


class AcmebookScraper(BaseScraper):
    def __init__(self, config: dict, client: HttpClient) -> None:
        super().__init__(config, client)
        self.base_url: str = config["acmebook"]["base_url"]
        self.categories: list[dict] = config["acmebook"]["categories"]

        # 重複書籍 sn 追蹤
        self._seen_sns: set[str] = set()

    # ------------------------------------------------------------------ #
    # 公開介面
    # ------------------------------------------------------------------ #

    def scrape_all(self) -> Generator[tuple[str, Generator[Book, None, None]], None, None]:
        for cat in self.categories:
            yield cat["name"], self._scrape_category(cat)

    # ------------------------------------------------------------------ #
    # 分類 → 分頁
    # ------------------------------------------------------------------ #

    def _scrape_category(self, cat: dict) -> Generator[Book, None, None]:
        type_sn1, name = cat["type_sn1"], cat["name"]
        logger.info("分類：%s (type_sn1=%s)", name, type_sn1)

        page = 1
        while True:
            url = (
                f"{self.base_url}/book_list.php"
                f"?page_num={page}&bookType_sn1={type_sn1}&bookType_sn=0"
            )
            sns = self._fetch_catalog_page(url)

            if sns is None:  # 請求失敗
                break
            if not sns:      # 空頁 → 已到最後一頁
                break

            self.stats["pages"] += 1

            for sn in sns:
                if sn in self._seen_sns:
                    continue
                self._seen_sns.add(sn)

                detail_url = f"{self.base_url}/book.php?sn={sn}&bookType_sn=0"
                book = self._fetch_book(detail_url, category=name)
                if book is not None:
                    yield book

            page += 1

    # ------------------------------------------------------------------ #
    # 目錄頁解析
    # ------------------------------------------------------------------ #

    def _fetch_catalog_page(self, url: str) -> Optional[list[str]]:
        """回傳該頁的 book sn 列表；None 表示請求失敗。"""
        resp = self.client.get(url)
        if resp is None:
            logger.error("目錄頁請求失敗：%s", url)
            return None

        try:
            soup = BeautifulSoup(resp.text, "lxml")
            links = soup.select('a[href*="book.php?sn="]')
            sns: list[str] = []
            for a in links:
                href: str = a.get("href", "")
                m = re.search(r"sn=(\d+)", href)
                if m:
                    sn = m.group(1)
                    if sn not in sns:
                        sns.append(sn)
            return sns
        except Exception as exc:
            logger.error("目錄頁解析失敗：%s — %s", url, exc)
            return None

    # ------------------------------------------------------------------ #
    # 解析輔助
    # ------------------------------------------------------------------ #

    def _is_available(self, soup: BeautifulSoup) -> bool:
        """采實無庫存標記；含排除關鍵字則跳過，否則視為可售。"""
        page_text = soup.get_text()
        for kw in self.exclude_keywords:
            if kw in page_text:
                return False
        return True

    def _parse_title(self, soup: BeautifulSoup) -> Optional[str]:
        """從 <title> tag 取書名，去掉「| 采實出版集團」等後綴。"""
        title_tag = soup.find("title")
        if title_tag:
            raw = title_tag.get_text(strip=True)
            # 「書名 | 采實出版集團 ACME Publishing co.Ltd.」→ 只取 | 前
            title = raw.split("|")[0].strip()
            if title:
                return title

        # 備援：og:title
        og = soup.find("meta", property="og:title")
        if og:
            raw = og.get("content", "").strip()
            return raw.split("|")[0].strip() or None

        return None

    def _parse_price(self, soup: BeautifulSoup) -> Optional[int]:
        """解析「定價 NNN 元」→ 整數 NNN。"""
        text = soup.get_text()
        m = re.search(r"定價[：:]?\s*(\d+)\s*元", text)
        if m:
            return int(m.group(1))
        return None
