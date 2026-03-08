"""格林文化（grimmpress.com.tw）爬蟲實作。

DOM 結構（2026-03-07 確認）：
  分類列表     : /index.php?route=product/category&path=X_Y&page=N（SSR，9筆/頁）
                 ⚠️  父分類（path=59）無產品；需用子分類（path=59_60）才有 product-thumb
  詳情頁       : /product/{product_id}/{path}（SSR）
  書名         : <h1> 標籤（列表頁用 <h4><a>）
  定價         : 「原價：NNN元」（.price-old class；正式定價非特價）
  ISBN         : 「ISBN： 978-XXX-XXX-XXX-X」（含連字號，移除後取 13 碼）
  庫存         : id=button-cart 按鈕文字 = 「加入購物車」為可售；「缺貨」=不可售
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


class GrimmScraper(BaseScraper):
    def __init__(self, config: dict, client: HttpClient) -> None:
        super().__init__(config, client)
        cfg = config["grimm"]
        self.base_url: str = cfg["base_url"]
        self.categories: list[dict] = cfg["categories"]

    # ------------------------------------------------------------------ #
    # 公開介面
    # ------------------------------------------------------------------ #

    def scrape_all(self) -> Generator[tuple[str, Generator[Book, None, None]], None, None]:
        for cat in self.categories:
            yield cat["name"], self._scrape_category(cat["path"], cat["name"])

    # ------------------------------------------------------------------ #
    # 分類巡覽
    # ------------------------------------------------------------------ #

    def _scrape_category(self, path: str, name: str) -> Generator[Book, None, None]:
        page = 1
        while True:
            urls = self._fetch_listing_page(path, page)
            if not urls:
                break
            self.stats["pages"] += 1
            logger.info("path=%s [%s] 第%d頁：取得 %d 個連結", path, name, page, len(urls))
            for url in urls:
                book = self._fetch_book(url, category=name)
                if book is not None:
                    yield book
            page += 1

    def _fetch_listing_page(self, path: str, page: int) -> list[str]:
        """取得分類列表頁的詳情頁 URL 列表。"""
        url = f"{self.base_url}/index.php"
        resp = self.client.get(url, params={"route": "product/category", "path": path, "page": page})
        if resp is None:
            logger.error("列表頁請求失敗：path=%s page=%d", path, page)
            return []
        try:
            soup = BeautifulSoup(resp.content.decode("utf-8", errors="replace"), "html.parser")
            links: list[str] = []
            for thumb in soup.find_all("div", class_="product-thumb"):
                a = thumb.find("a", href=re.compile(r"/product/\d+"))
                if a and a["href"] not in links:
                    links.append(a["href"])
            return links
        except Exception as exc:
            logger.error("列表頁解析失敗：path=%s page=%d — %s", path, page, exc)
            return []

    # ------------------------------------------------------------------ #
    # 解析方法
    # ------------------------------------------------------------------ #

    def _is_available(self, soup: BeautifulSoup) -> bool:
        # 購物車按鈕
        btn = soup.find(id="button-cart")
        if btn:
            btn_text = btn.get_text(strip=True)
            if any(kw in btn_text for kw in self.exclude_keywords):
                return False
            return True
        # 備援：排除關鍵字掃描
        page_text = soup.get_text()
        for kw in self.exclude_keywords:
            if kw in page_text:
                return False
        return True

    def _parse_title(self, soup: BeautifulSoup) -> Optional[str]:
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True) or None
        return None

    def _parse_price(self, soup: BeautifulSoup) -> Optional[int]:
        # 優先取原價（定價）
        m = re.search(r"原價[：:]\s*(\d+)", soup.get_text())
        if m:
            return int(m.group(1))
        # 備援：定價
        m2 = re.search(r"定價[：:]\s*(\d+)", soup.get_text())
        if m2:
            return int(m2.group(1))
        return None

    def _parse_isbn(self, soup: BeautifulSoup) -> Optional[str]:
        """ISBN 含連字號（978-XXX-XXX-XXX-X），移除後取 13 碼。"""
        text = soup.get_text()
        m = re.search(r"ISBN[：:\s]*([\d-]{13,17})", text)
        if m:
            isbn = m.group(1).replace("-", "").strip()
            if len(isbn) == 13 and isbn.isdigit():
                return isbn
        return super()._parse_isbn(soup)
