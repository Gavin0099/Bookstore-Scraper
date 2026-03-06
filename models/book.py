from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Book:
    title: str
    price: int
    isbn: str
    source_url: str = field(default="", repr=False)

    # ------------------------------------------------------------------ #
    # 資料品質驗證（spec §2.3）
    # ------------------------------------------------------------------ #

    def validate(self) -> list[str]:
        """回傳錯誤訊息列表；空列表表示資料合法。"""
        errors: list[str] = []

        if not self.title or not self.title.strip():
            errors.append("書名為空")

        if self.price <= 0:
            errors.append(f"定價無效（{self.price}）")

        if not _is_valid_isbn(self.isbn):
            errors.append(f"ISBN 非 13 碼數字（{self.isbn!r}）")

        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0


def _is_valid_isbn(isbn: str) -> bool:
    """ISBN 必須為 13 碼純數字（spec §2.1）。"""
    return isinstance(isbn, str) and len(isbn) == 13 and isbn.isdigit()
