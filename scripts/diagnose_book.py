"""
診斷特定書籍未被爬取的原因。
用法：python scripts/diagnose_book.py "書名關鍵字"
"""
import json
import re
import sys
import requests
from bs4 import BeautifulSoup

SEARCH_URL = "https://www.suncolor.com.tw/Search.aspx"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def check_book_page(url: str) -> dict:
    """進入書籍詳情頁，回傳診斷結果。"""
    resp = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, "lxml")

    result = {"url": url}

    # 書名
    h1 = soup.find("h1")
    result["title"] = h1.get_text(strip=True) if h1 else "(未找到)"

    # ISBN
    m = re.search(r"ISBN[：:]\s*(\d+)", soup.get_text())
    result["isbn"] = m.group(1) if m else "(未找到)"

    # 定價
    mp = re.search(r"定價[：:]\s*(\d+)\s*元", soup.get_text())
    result["price"] = mp.group(1) if mp else "(未找到)"

    # 庫存狀態
    availability = "(未找到)"
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            av = data.get("availability", "")
            if av:
                availability = av
                break
        except Exception:
            continue
    result["availability"] = availability

    # 是否可購買
    instock = availability == "https://schema.org/InStock"
    result["is_available"] = instock

    # 分類（從 breadcrumb 讀）
    breadcrumb = soup.select("ol.breadcrumb li, .breadcrumb li")
    result["breadcrumb"] = " > ".join(li.get_text(strip=True) for li in breadcrumb)

    return result


def search_book(keyword: str) -> list[dict]:
    """搜尋書名關鍵字，回傳命中的書籍列表資訊。"""
    url = f"https://www.suncolor.com.tw/Search.aspx?keyword={keyword}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, "lxml")

    results = []
    # 搜尋結果頁的書籍連結
    links = soup.select("a.product-image, a[href*='BookPage.aspx?bokno=']")
    seen = set()
    for a in links:
        href = a.get("href", "")
        m = re.search(r"bokno=(\w+)", href)
        if m and m.group(1) not in seen:
            bokno = m.group(1)
            seen.add(bokno)
            results.append(f"https://www.suncolor.com.tw/BookPage.aspx?bokno={bokno}")

    return results


def main():
    books_to_check = [
        "露露愛數字",
        "我們都學會了！生活認知繪本套書",
    ]
    if len(sys.argv) > 1:
        books_to_check = sys.argv[1:]

    for keyword in books_to_check:
        print(f"\n{'='*60}")
        print(f"搜尋: {keyword}")
        print(f"{'='*60}")

        urls = search_book(keyword)
        if not urls:
            print("  ❌ 搜尋結果為空（可能下架或關鍵字不符）")
            # 嘗試直接用 BookList API 搜尋
            continue

        for url in urls[:3]:
            info = check_book_page(url)
            print(f"\n  書名   : {info['title']}")
            print(f"  ISBN   : {info['isbn']}")
            print(f"  定價   : {info['price']}")
            print(f"  庫存   : {info['availability']}")
            print(f"  可購買 : {'✓' if info['is_available'] else '✗ 不可購買（這是被跳過的原因！）'}")
            print(f"  麵包屑 : {info['breadcrumb']}")
            print(f"  URL    : {url}")


if __name__ == "__main__":
    main()
