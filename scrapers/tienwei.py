"""小魯閱讀網（tienwei.com.tw）爬蟲實作。

DOM 結構（2026-03-07 確認）：
  分類列表     : /product/include_product_index_list.php?bid=XX&page=N
                 → AJAX 端點，但直接 GET 即可取得 HTML，不需要 JS
  詳情頁       : /product/detailXXXX（SSR）
  書名         : <h1> 標籤
  定價         : 「定價：$NNN」文字
  ISBN         : 「ISBN：978-XXX-XXX-XXX-X」（含連字號，移除後取 13 碼）
  庫存         : 「缺貨」關鍵字出現時視為不可購買
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


class TienweiScraper(BaseScraper):
    def __init__(self, config: dict, client: HttpClient) -> None:
        super().__init__(config, client)
        cfg = config["tienwei"]
        self.base_url: str = cfg["base_url"]
        self.categories: list[dict] = cfg["categories"]
        self._list_url = f"{self.base_url}/product/include_product_index_list.php"

    # ------------------------------------------------------------------ #
    # 公開介面
    # ------------------------------------------------------------------ #

    def scrape_all(self) -> Generator[tuple[str, Generator[Book, None, None]], None, None]:
        for cat in self.categories:
            yield cat["name"], self._scrape_category(cat["bid"], cat["name"])

    # ------------------------------------------------------------------ #
    # 分類巡覽
    # ------------------------------------------------------------------ #

    def _scrape_category(self, bid: str, name: str) -> Generator[Book, None, None]:
        page = 1
        while True:
            urls = self._fetch_listing_page(bid, page)
            if not urls:
                break
            self.stats["pages"] += 1
            logger.info("bid=%s [%s] 第%d頁：取得 %d 個連結", bid, name, page, len(urls))
            for url in urls:
                book = self._fetch_book(url, category=name)
                if book is not None:
                    yield book
            page += 1

    def _fetch_listing_page(self, bid: str, page: int) -> list[str]:
        """取得分類列表頁的詳情頁 URL 列表。"""
        resp = self.client.get(
            self._list_url,
            params={"bid": bid, "skey": "", "type": "", "brand_id": "",
                    "gprice_from": "", "gprice_to": "", "page": page},
        )
        if resp is None:
            logger.error("列表頁請求失敗：bid=%s page=%d", bid, page)
            return []
        try:
            soup = BeautifulSoup(resp.text, "lxml")
            links: list[str] = []
            for a in soup.find_all("a", href=re.compile(r"/product/detail\d+")):
                href = a["href"]
                url = href if href.startswith("http") else f"{self.base_url}{href}"
                if url not in links:
                    links.append(url)
            return links
        except Exception as exc:
            logger.error("列表頁解析失敗：bid=%s page=%d — %s", bid, page, exc)
            return []

    # ------------------------------------------------------------------ #
    # 解析方法
    # ------------------------------------------------------------------ #

    def _is_available(self, soup: BeautifulSoup) -> bool:
        page_text = soup.get_text()
        for kw in self.exclude_keywords:
            if kw in page_text:
                return False
        # 若購物車按鈕不存在且出現「缺貨」則排除；否則視為可售
        return True

    def _parse_title(self, soup: BeautifulSoup) -> Optional[str]:
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True) or None
        return None

    def _parse_price(self, soup: BeautifulSoup) -> Optional[int]:
        m = re.search(r"定價[：:]\s*\$\s*(\d+)", soup.get_text())
        if m:
            return int(m.group(1))
        return None

    def _parse_isbn(self, soup: BeautifulSoup) -> Optional[str]:
        """ISBN 含連字號（978-XXX-XXX-XXX-X），移除後取 13 碼。"""
        text = soup.get_text()
        # 先嘗試含連字號格式
        m = re.search(r"ISBN[：:]\s*([\d-]{13,17})", text)
        if m:
            isbn = m.group(1).replace("-", "")
            if len(isbn) == 13 and isbn.isdigit():
                return isbn
        # 備援：父類別的純數字格式
        return super()._parse_isbn(soup)
