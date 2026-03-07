"""Excel 輸出模組（spec §3.1 / §3.2）。

輸出格式：
  檔名    : suncolor_books_YYYYMMDD_HHMMSS.xlsx
  工作表  : 書單
  欄位    : ISBN | 分類 | 書名 | 定價
  第一列  : 標題列（粗體）
  ISBN    : 強制文字格式（避免科學記號，spec AC-03）
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

from openpyxl import Workbook
from openpyxl.styles import Font

from models.book import Book


def write_excel(
    books: Iterable[Book],
    output_dir: str = ".",
    prefix: str = "suncolor_books",
) -> Path:
    """將書籍資料寫入 Excel，回傳實際寫入的檔案路徑。"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = Path(output_dir) / f"{prefix}_{timestamp}.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = "書單"

    # 標題列（粗體）
    headers = ["ISBN", "分類", "書名", "定價"]
    ws.append(headers)
    bold = Font(bold=True)
    for cell in ws[1]:
        cell.font = bold

    # 資料列
    for book in books:
        ws.append([
            _isbn_cell(book.isbn),  # 強制文字格式
            book.category,          # 分類名稱
            book.title,             # 文字，左對齊（Excel 預設）
            book.price,             # 數値，整數
        ])

    # ISBN 欄（A 欄）設為文字格式，防止科學記號
    for row in ws.iter_rows(min_row=2, min_col=1, max_col=1):
        for cell in row:
            cell.number_format = "@"

    wb.save(filepath)
    return filepath


def _isbn_cell(isbn: str) -> str:
    """回傳字串型別的 ISBN；openpyxl 寫入字串不會轉科學記號。"""
    return str(isbn)
