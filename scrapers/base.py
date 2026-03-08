"""BaseScraper — 所有書商爬蟲的抽象基底類別。

共用邏輯：
  - stats 統計字典
  - ISBN 去重集合
  - _fetch_book()：詳情頁抓取流程（庫存過濾 → 欄位解析 → 品質驗證）
  - _parse_isbn()：通用 ISBN 文字解析
  - _is_available_schema()：schema.org JSON-LD 庫存解析輔助

各子類別必須實作：
  - scrape_all()
  - _is_available()
  - _parse_title()
  - _parse_price()
"""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Generator, Optional

from bs4 import BeautifulSoup

from models.book import Book
from utils.http_client import HttpClient
from utils.logger import get_logger

logger = get_logger()


class BaseScraper(ABC):
    def __init__(self, config: dict, client: HttpClient) -> None:
        self.available_status: str = config["filter"]["available_status"]
        self.exclude_keywords: tuple[str, ...] = tuple(
            config["filter"]["exclude_keywords"]
        )
        self.client = client
        self._seen_isbns: set[str] = set()
        self.stats = {
            "pages": 0,
            "processed": 0,
            "success": 0,
            "skipped_unavailable": 0,
            "skipped_no_isbn": 0,
            "skipped_invalid": 0,
            "skipped_duplicate": 0,
            "skipped_parse_error": 0,
        }

    # ------------------------------------------------------------------ #
    # 公開介面（子類別必須實作）
    # ------------------------------------------------------------------ #

    @abstractmethod
    def scrape_all(self) -> Generator[tuple[str, Generator[Book, None, None]], None, None]:
        """巡覽全部分類，yield (分類名稱, books_generator)。"""
        ...

    # ------------------------------------------------------------------ #
    # 詳情頁共用抓取流程
    # ------------------------------------------------------------------ #

    def _fetch_book(self, url: str, category: str = "") -> Optional[Book]:
        """共用詳情頁抓取流程。各步驟由子類別覆寫的解析方法完成。"""
        self.stats["processed"] += 1

        resp = self.client.get(url)
        if resp is None:
            logger.error("詳情頁請求失敗：%s", url)
            self.stats["skipped_parse_error"] += 1
            return None

        try:
            soup = BeautifulSoup(resp.text, "lxml")

            # 1. 庫存過濾
            if not self._is_available(soup):
                self.stats["skipped_unavailable"] += 1
                return None

            # 2. 擷取欄位
            title = self._parse_title(soup)
            price = self._parse_price(soup)
            isbn = self._parse_isbn(soup)

            # 3. ISBN 缺失
            if isbn is None:
                logger.warning("ISBN 缺失，跳過：%s", url)
                self.stats["skipped_no_isbn"] += 1
                return None

            # 4. 重複 ISBN
            if isbn in self._seen_isbns:
                logger.warning("重複 ISBN %s，跳過：%s", isbn, url)
                self.stats["skipped_duplicate"] += 1
                return None

            image_url = self._parse_image(soup) or ""
            description = self._parse_description(soup) or ""
            book = Book(title=title or "", price=price or 0, isbn=isbn,
                        source_url=url, category=category,
                        image_url=image_url, description=description)

            # 5. 資料品質驗證
            errors = book.validate()
            if errors:
                logger.warning("資料品質不合格（%s），跳過：%s", "；".join(errors), url)
                self.stats["skipped_invalid"] += 1
                return None

            self._seen_isbns.add(isbn)
            self.stats["success"] += 1
            return book

        except Exception as exc:
            logger.error("詳情頁解析例外：%s — %s", url, exc)
            self.stats["skipped_parse_error"] += 1
            return None

    # ------------------------------------------------------------------ #
    # 共用解析輔助
    # ------------------------------------------------------------------ #

    def _is_available_schema(self, soup: BeautifulSoup) -> Optional[bool]:
        """讀取 schema.org JSON-LD availability。找不到回傳 None。"""
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                availability = data.get("availability", "")
                if availability:
                    return availability == self.available_status
            except (json.JSONDecodeError, AttributeError):
                continue
        return None

    def _parse_isbn(self, soup: BeautifulSoup) -> Optional[str]:
        """解析「ISBN：XXXXXXXXXXXXX」→ 13 碼字串。"""
        text = soup.get_text()
        m = re.search(r"ISBN[：:]\s*(\d{13})", text)
        return m.group(1) if m else None

    # ------------------------------------------------------------------ #
    # 子類別必須實作的解析方法
    # ------------------------------------------------------------------ #

    @abstractmethod
    def _is_available(self, soup: BeautifulSoup) -> bool: ...

    @abstractmethod
    def _parse_title(self, soup: BeautifulSoup) -> Optional[str]: ...

    @abstractmethod
    def _parse_price(self, soup: BeautifulSoup) -> Optional[int]: ...

    def _parse_image(self, soup: BeautifulSoup) -> Optional[str]:
        """封面圖 URL；子類別可覆寫。預設回傳 None。"""
        return None

    def _parse_description(self, soup: BeautifulSoup) -> Optional[str]:
        """內容簡介；子類別可覆寫。預設回傳 None。"""
        return None
