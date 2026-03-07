"""信誼小太陽（hsinyishop.com）爬蟲實作。

DOM 結構（2026-03-07 確認）：
  商品 URL 來源 : /sitemap.xml → <loc> 內含 /products/hXXXXX URL
  詳情頁        : /products/hXXXXX
  資料位置      : <script> 標籤內 app.value('product', {...}) JSON 字串
                  → 不需要 JS 執行，靜態 HTML 即含完整資料
  書名          : product["title_translations"]["zh-hant"]
  定價          : product["price"]["dollars"]（原價）
  ISBN          : product["gtin"]（13碼時採用）；備援：頁面文字 ISBN：XXX
  庫存          : product["sold_out"] == False → 可售
"""
from __future__ import annotations

import json
import re
from typing import Generator, Optional

from bs4 import BeautifulSoup

from models.book import Book
from scrapers.base import BaseScraper
from utils.http_client import HttpClient
from utils.logger import get_logger

logger = get_logger()

_JSON_DECODER = json.JSONDecoder()


class HsinyiScraper(BaseScraper):
    def __init__(self, config: dict, client: HttpClient) -> None:
        super().__init__(config, client)
        self.base_url: str = config["hsinyi"]["base_url"]
        self._seen_product_ids: set[str] = set()

    # ------------------------------------------------------------------ #
    # 公開介面
    # ------------------------------------------------------------------ #

    def scrape_all(self) -> Generator[tuple[str, Generator[Book, None, None]], None, None]:
        """從 sitemap 取得全品項 URL，yield 單一分類。"""
        yield "全品項", self._scrape_from_sitemap()

    # ------------------------------------------------------------------ #
    # Sitemap 巡覽
    # ------------------------------------------------------------------ #

    def _scrape_from_sitemap(self) -> Generator[Book, None, None]:
        """解析 sitemap.xml，取得所有 /products/ URL 並逐一抓取。"""
        product_urls = self._fetch_sitemap_urls()
        if not product_urls:
            logger.error("Sitemap 無商品 URL，終止")
            return

        self.stats["pages"] += 1
        logger.info("Sitemap 取得 %d 個商品 URL", len(product_urls))

        for url in product_urls:
            product_id = url.rstrip("/").split("/")[-1]
            if product_id in self._seen_product_ids:
                continue
            self._seen_product_ids.add(product_id)

            book = self._fetch_book(url, category="全品項")
            if book is not None:
                yield book

    def _fetch_sitemap_urls(self) -> list[str]:
        """取得 sitemap.xml 中所有 /products/ URL。"""
        sitemap_url = f"{self.base_url}/sitemap.xml"
        resp = self.client.get(sitemap_url)
        if resp is None:
            logger.error("Sitemap 請求失敗：%s", sitemap_url)
            return []

        try:
            soup = BeautifulSoup(resp.text, "lxml-xml")

            # Sitemap index：若含 <sitemap> 子節點，需展開
            if soup.find("sitemapindex"):
                all_urls: list[str] = []
                for loc in soup.find_all("loc"):
                    sub_url = loc.get_text(strip=True)
                    if "sitemap" in sub_url:
                        all_urls.extend(self._fetch_sub_sitemap(sub_url))
                return all_urls

            # 一般 sitemap：直接讀 <loc>
            return [
                loc.get_text(strip=True)
                for loc in soup.find_all("loc")
                if "/products/" in loc.get_text()
            ]
        except Exception as exc:
            logger.error("Sitemap 解析失敗：%s", exc)
            return []

    def _fetch_sub_sitemap(self, url: str) -> list[str]:
        resp = self.client.get(url)
        if resp is None:
            return []
        try:
            soup = BeautifulSoup(resp.text, "lxml-xml")
            return [
                loc.get_text(strip=True)
                for loc in soup.find_all("loc")
                if "/products/" in loc.get_text()
            ]
        except Exception:
            return []

    # ------------------------------------------------------------------ #
    # 解析輔助
    # ------------------------------------------------------------------ #

    def _is_available(self, soup: BeautifulSoup) -> bool:
        """讀 JSON 的 sold_out 欄位；備援：排除關鍵字。"""
        product = self._extract_product_json(soup)
        if product is not None:
            return not product.get("sold_out", True)

        page_text = soup.get_text()
        for kw in self.exclude_keywords:
            if kw in page_text:
                return False
        return True

    def _parse_title(self, soup: BeautifulSoup) -> Optional[str]:
        product = self._extract_product_json(soup)
        if product is not None:
            trans = product.get("title_translations", {})
            return trans.get("zh-hant") or trans.get("en") or None
        return None

    def _parse_price(self, soup: BeautifulSoup) -> Optional[int]:
        product = self._extract_product_json(soup)
        if product is not None:
            price_data = product.get("price", {})
            dollars = price_data.get("dollars")
            if dollars is not None:
                return int(dollars)
        return None

    def _parse_isbn(self, soup: BeautifulSoup) -> Optional[str]:
        """優先用 JSON gtin（需 13 碼）；備援：頁面文字掃描。"""
        product = self._extract_product_json(soup)
        if product is not None:
            gtin = str(product.get("gtin", "")).strip()
            if len(gtin) == 13 and gtin.isdigit():
                return gtin

        # 備援：BaseScraper 的文字解析（ISBN：XXXXXXXXXXXXX）
        return super()._parse_isbn(soup)

    # ------------------------------------------------------------------ #
    # JSON 提取
    # ------------------------------------------------------------------ #

    def _extract_product_json(self, soup: BeautifulSoup) -> Optional[dict]:
        """從 <script> 標籤中提取 app.value('product', {...}) 的 JSON。"""
        for script in soup.find_all("script"):
            text = script.string or ""
            if "app.value('product'," not in text:
                continue
            m = re.search(r"app\.value\('product',\s*(\{)", text)
            if not m:
                continue
            try:
                product, _ = _JSON_DECODER.raw_decode(text[m.start(1):])
                return product
            except (json.JSONDecodeError, ValueError):
                continue
        return None
