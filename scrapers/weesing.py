"""華碩文化（weesing123.com.tw）爬蟲實作。

DOM 結構（2026-03-07 確認）：
  目錄頁  : /{slug}?page=N（例：/sound-book?page=2）
  詳情頁  : /{product-code}（例：/S080）
  商品連結: .grid-box a[href] → 路徑即 product slug
  書名    : <h1> 文字
  定價    : class="price-old" 或 class="product-original-price" 中 $NNN
  ISBN    : 文字「ISBN：XXXXXXXXXXXXX」（13 碼）
  庫存    : schema.org JSON-LD "availability"
              InStock  → 可購買
              SoldOut  → 停售/缺書
            備援：排除關鍵字文字掃描
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


class WeesingsScraper(BaseScraper):
    def __init__(self, config: dict, client: HttpClient) -> None:
        super().__init__(config, client)
        self.base_url: str = config["weesing"]["base_url"]
        self.categories: list[dict] = config["weesing"]["categories"]

        # 重複 slug 追蹤（在發出詳情頁請求前過濾）
        self._seen_slugs: set[str] = set()

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
        slug, name = cat["slug"], cat["name"]
        logger.info("分類：%s (%s)", name, slug)

        page = 1
        while True:
            url = f"{self.base_url}/{slug}?page={page}"
            product_slugs = self._fetch_catalog_page(url)

            if product_slugs is None:  # 請求失敗
                break
            if not product_slugs:      # 空頁 → 已到最後一頁
                break

            self.stats["pages"] += 1

            for product_slug in product_slugs:
                if product_slug in self._seen_slugs:
                    continue
                self._seen_slugs.add(product_slug)

                detail_url = f"{self.base_url}/{product_slug}"
                book = self._fetch_book(detail_url, category=name)
                if book is not None:
                    yield book

            page += 1

    # ------------------------------------------------------------------ #
    # 目錄頁解析
    # ------------------------------------------------------------------ #

    def _fetch_catalog_page(self, url: str) -> Optional[list[str]]:
        """回傳該頁的 product slug 列表；None 表示請求失敗。"""
        resp = self.client.get(url)
        if resp is None:
            logger.error("目錄頁請求失敗：%s", url)
            return None

        try:
            soup = BeautifulSoup(resp.text, "lxml")
            links = soup.select(".grid-box a[href]")
            slugs: list[str] = []
            for a in links:
                href: str = a.get("href", "")
                # 只取站內簡短路徑（排除外部連結、錨點、空值）
                if not href or href.startswith("http") or href.startswith("#"):
                    continue
                product_slug = href.lstrip("/")
                if product_slug and product_slug not in slugs:
                    slugs.append(product_slug)
            return slugs
        except Exception as exc:
            logger.error("目錄頁解析失敗：%s — %s", url, exc)
            return None

    # ------------------------------------------------------------------ #
    # 解析輔助
    # ------------------------------------------------------------------ #

    def _is_available(self, soup: BeautifulSoup) -> bool:
        """優先讀 schema.org JSON-LD；備援檢查排除關鍵字。"""
        result = self._is_available_schema(soup)
        if result is not None:
            return result

        page_text = soup.get_text()
        for kw in self.exclude_keywords:
            if kw in page_text:
                return False

        return True  # 無明確停售訊號則視為可購買

    def _parse_title(self, soup: BeautifulSoup) -> Optional[str]:
        h1 = soup.find("h1")
        return h1.get_text(strip=True) if h1 else None

    def _parse_price(self, soup: BeautifulSoup) -> Optional[int]:
        """從 .price-old / .product-original-price 取原價（定價）。"""
        tag = soup.select_one(".price-old, .product-original-price")
        if tag:
            m = re.search(r"\$?\s*(\d+)", tag.get_text(strip=True))
            if m:
                return int(m.group(1))
        return None
