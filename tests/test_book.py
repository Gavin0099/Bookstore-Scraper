"""Unit tests for models/book.py — Book dataclass + validators（spec §2.3）"""
import pytest
from models.book import Book, _is_valid_isbn


# ------------------------------------------------------------------ #
# _is_valid_isbn
# ------------------------------------------------------------------ #

class TestIsValidIsbn:
    def test_valid_isbn(self):
        assert _is_valid_isbn("9789576589065") is True

    def test_valid_isbn_starting_with_978(self):
        assert _is_valid_isbn("9780000000002") is True

    def test_too_short(self):
        assert _is_valid_isbn("978957658906") is False      # 12 碼

    def test_too_long(self):
        assert _is_valid_isbn("97895765890650") is False    # 14 碼

    def test_contains_letters(self):
        assert _is_valid_isbn("978957658906X") is False

    def test_empty_string(self):
        assert _is_valid_isbn("") is False

    def test_none(self):
        assert _is_valid_isbn(None) is False                # type: ignore

    def test_with_hyphens(self):
        assert _is_valid_isbn("978-9-576-58906-5") is False  # 帶破折號不合格


# ------------------------------------------------------------------ #
# Book.validate() — 書名
# ------------------------------------------------------------------ #

class TestBookTitleValidation:
    def test_valid_title(self):
        book = Book(title="好書", price=300, isbn="9789576589065")
        assert book.validate() == []

    def test_empty_title(self):
        book = Book(title="", price=300, isbn="9789576589065")
        errors = book.validate()
        assert any("書名" in e for e in errors)

    def test_whitespace_only_title(self):
        book = Book(title="   ", price=300, isbn="9789576589065")
        errors = book.validate()
        assert any("書名" in e for e in errors)


# ------------------------------------------------------------------ #
# Book.validate() — 定價
# ------------------------------------------------------------------ #

class TestBookPriceValidation:
    def test_valid_price(self):
        book = Book(title="好書", price=350, isbn="9789576589065")
        assert book.validate() == []

    def test_zero_price(self):
        book = Book(title="好書", price=0, isbn="9789576589065")
        errors = book.validate()
        assert any("定價" in e for e in errors)

    def test_negative_price(self):
        book = Book(title="好書", price=-1, isbn="9789576589065")
        errors = book.validate()
        assert any("定價" in e for e in errors)

    def test_price_one(self):
        book = Book(title="好書", price=1, isbn="9789576589065")
        assert book.validate() == []


# ------------------------------------------------------------------ #
# Book.validate() — ISBN
# ------------------------------------------------------------------ #

class TestBookIsbnValidation:
    def test_valid_isbn(self):
        book = Book(title="好書", price=300, isbn="9789576589065")
        assert book.validate() == []

    def test_invalid_isbn_short(self):
        book = Book(title="好書", price=300, isbn="978957658906")
        errors = book.validate()
        assert any("ISBN" in e for e in errors)

    def test_invalid_isbn_with_letters(self):
        book = Book(title="好書", price=300, isbn="978957658906X")
        errors = book.validate()
        assert any("ISBN" in e for e in errors)

    def test_empty_isbn(self):
        book = Book(title="好書", price=300, isbn="")
        errors = book.validate()
        assert any("ISBN" in e for e in errors)


# ------------------------------------------------------------------ #
# Book.validate() — 多重錯誤
# ------------------------------------------------------------------ #

class TestBookMultipleErrors:
    def test_all_invalid(self):
        book = Book(title="", price=0, isbn="bad")
        errors = book.validate()
        assert len(errors) == 3

    def test_is_valid_true(self):
        book = Book(title="好書", price=300, isbn="9789576589065")
        assert book.is_valid() is True

    def test_is_valid_false(self):
        book = Book(title="", price=300, isbn="9789576589065")
        assert book.is_valid() is False
