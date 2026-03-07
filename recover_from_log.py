"""
從 log 中解析成功書籍紀錄，輸出 Excel。
Log 格式: [DEBUG] ✓ {ISBN} | {price} | {title}
"""
import re
import sys
from pathlib import Path

# 動態引入 write_excel
sys.path.insert(0, str(Path(__file__).parent))
from output.excel_writer import write_excel
from models.book import Book


def recover(log_path: str) -> list[Book]:
    books = []
    seen_isbns = set()
    pattern = re.compile(r"\[DEBUG\] ✓ (\d{13}) \| (\d+) \| (.+)")

    with open(log_path, encoding="utf-8") as f:
        for line in f:
            m = pattern.search(line)
            if m:
                isbn = m.group(1)
                if isbn in seen_isbns:
                    continue
                seen_isbns.add(isbn)
                price = int(m.group(2))
                # 書名可能被截斷（tqdm 同一行覆寫），取 | 前的部分並 strip
                title_raw = m.group(3)
                # 去除 tqdm 殘留字元或多餘空白
                title = re.sub(r"\s+", " ", title_raw).strip()
                books.append(Book(title=title, price=price, isbn=isbn, source_url=""))
    return books


if __name__ == "__main__":
    log_path = "scraper_20260306_215003.log"
    books = recover(log_path)
    print(f"從 log 恢復書籍數量：{len(books)}")
    if books:
        out = write_excel(books, output_dir=".", prefix="suncolor_books_recovered")
        print(f"Excel 輸出：{out}")
    else:
        print("沒有找到任何成功書籍記錄。")
