"""三采文化（suncolor.com.tw）爬蟲實作。

DOM 結構（2026-03-06 確認）：
  目錄頁  : BookList.aspx?knd=0&knd2=XX&p=N&pagesize=18&sort=
  詳情頁  : BookPage.aspx?bokno=XXXXXXXXXX
  書名    : <h1> 文字
  定價    : 文字「定價：NNN元」
  ISBN    : 文字「ISBN：XXXXXXXXXXXXX」（13 碼）
  庫存    : schema.org JSON-LD "availability"
              InStock  → 可購買
              SoldOut  → 停售/缺書
            備援：按鈕文字「加入暫存清單」
"""
from __future__ import annotations

import re
from typing import Generator, Optional
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from models.book import Book
from scrapers.base import BaseScraper
from utils.http_client import HttpClient
from utils.logger import get_logger

logger = get_logger()


class SuncolorScraper(BaseScraper):
    def __init__(self, config: dict, client: HttpClient) -> None:
        super().__init__(config, client)
        self.base_url: str = config["suncolor"]["base_url"]
        self.catalog_path: str = config["suncolor"]["catalog_path"]
        self.kids_catalog_path: str = config["suncolor"].get("kids_catalog_path", "KidsBookList.aspx")
        self.book_path: str = config["suncolor"]["book_path"]
        self.page_size: int = config["suncolor"]["page_size"]
        self.categories: list[dict] = config["suncolor"]["categories"]

        # 重複 bokno 追蹤（在發出詳情頁請求前就過濾，避免浪費網路時間）
        self._seen_boknos: set[str] = set()

    # ------------------------------------------------------------------ #
    # 公開介面
    # ------------------------------------------------------------------ #

    def scrape_all(self) -> Generator[tuple[str, Generator[Book, None, None]], None, None]:
        """巡覽全部分類，yield (分類名稱, books_generator)。"""
        for cat in self.categories:
            yield cat["name"], self._scrape_category(cat)

    # ------------------------------------------------------------------ #
    # 分類 → 分頁
    # ------------------------------------------------------------------ #

    def _scrape_category(self, cat: dict) -> Generator[Book, None, None]:
        knd, knd2, name = cat["knd"], cat["knd2"], cat["name"]
        # 根據 path 欄位選擇目錄 URL
        use_kids_path = cat.get("path", "") == "kids"
        logger.info("分類：%s (knd=%s knd2=%s, path=%s)", name, knd, knd2, "kids" if use_kids_path else "normal")

        page = 1
        while True:
            url = self._catalog_url(knd, knd2, page, kids=use_kids_path)
            bokno_list = self._fetch_catalog_page(url)

            if bokno_list is None:  # 請求失敗
                break
            if not bokno_list:     # 空頁 → 已到最後一頁
                break

            self.stats["pages"] += 1

            for bokno in bokno_list:
                # 若已抓過此 bokno，直接跳過，不發出網路請求
                if bokno in self._seen_boknos:
                    continue
                self._seen_boknos.add(bokno)

                detail_url = self._detail_url(bokno)
                book = self._fetch_book(detail_url, category=name)
                if book is not None:
                    yield book

            page += 1

    # ------------------------------------------------------------------ #
    # 目錄頁解析
    # ------------------------------------------------------------------ #

    def _fetch_catalog_page(self, url: str) -> Optional[list[str]]:
        """回傳該頁的 bokno 列表；None 表示請求失敗。"""
        resp = self.client.get(url)
        if resp is None:
            logger.error("目錄頁請求失敗：%s", url)
            return None

        try:
            soup = BeautifulSoup(resp.text, "lxml")
            # 只選主商品格的連結 (a.product-image)，排除側欄暢銷榜
            links = soup.select("a.product-image")
            bokno_list: list[str] = []
            for a in links:
                href: str = a.get("href", "")
                m = re.search(r"bokno=(\w+)", href)
                if m:
                    bokno = m.group(1)
                    # list 去重（同一目錄頁內）
                    if bokno not in bokno_list:
                        bokno_list.append(bokno)
            return bokno_list
        except Exception as exc:
            logger.error("目錄頁解析失敗：%s — %s", url, exc)
            return None

    # ------------------------------------------------------------------ #
    # 解析輔助
    # ------------------------------------------------------------------ #

    def _is_available(self, soup: BeautifulSoup) -> bool:
        """優先讀 schema.org JSON-LD；備援檢查頁面文字與按鈕。"""
        # 方法 1：schema.org JSON-LD（BaseScraper 共用輔助）
        result = self._is_available_schema(soup)
        if result is not None:
            return result

        # 方法 2：備援 — 頁面文字含排除關鍵字
        page_text = soup.get_text()
        for kw in self.exclude_keywords:
            if kw in page_text:
                return False

        # 方法 3：備援 — 有無「加入暫存清單」按鈕
        return bool(soup.find(string=re.compile("加入暫存清單")))

    def _parse_title(self, soup: BeautifulSoup) -> Optional[str]:
        h1 = soup.find("h1")
        return h1.get_text(strip=True) if h1 else None

    def _parse_price(self, soup: BeautifulSoup) -> Optional[int]:
        """解析「定價：NNN元」→ 整數 NNN。"""
        text = soup.get_text()
        m = re.search(r"定價[：:]\s*(\d+)\s*元", text)
        if m:
            return int(m.group(1))
        return None

    def _parse_image(self, soup: BeautifulSoup) -> Optional[str]:
        """取最大尺寸封面圖 URL（imageapi，w=775）。"""
        img = soup.find("img", src=re.compile(r"imageapi.*w=775"))
        if img:
            return img["src"]
        # 備援：任何 imageapi 圖片
        img = soup.find("img", src=re.compile(r"imageapi"))
        return img["src"] if img else None

    def _parse_description(self, soup: BeautifulSoup) -> Optional[str]:
        """取「內容簡介」段落文字（前 500 字）。"""
        for marker in soup.find_all(string=lambda s: s and s.strip() == "內容簡介"):
            sibling = marker.parent.find_next_sibling()
            if sibling:
                text = sibling.get_text(strip=True)
                if text:
                    return text[:500]
        return None

    # ------------------------------------------------------------------ #
    # URL 建構
    # ------------------------------------------------------------------ #

    def _catalog_url(self, knd: str, knd2: str, page: int, kids: bool = False) -> str:
        path = self.kids_catalog_path if kids else self.catalog_path
        params = urlencode({
            "knd": knd,
            "knd2": knd2,
            "p": page,
            "pagesize": self.page_size,
            "sort": "",
        })
        return f"{self.base_url}/{path}?{params}"

    def _detail_url(self, bokno: str) -> str:
        return f"{self.base_url}/{self.book_path}?bokno={bokno}"
