"""
驗證 a.product-image selector 是否正確抓到主清單書籍（排除側欄）
執行：python scripts/verify_selector.py
"""
import re
import sys
import requests
from bs4 import BeautifulSoup

URL = "https://www.suncolor.com.tw/BookList.aspx?knd=0&knd2=14&p=1&pagesize=18&sort="
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def extract_boknos(soup, selector):
    links = soup.select(selector)
    boknos = []
    for a in links:
        href = a.get("href", "")
        m = re.search(r"bokno=(\w+)", href)
        if m and m.group(1) not in boknos:
            boknos.append(m.group(1))
    return boknos


def main():
    print(f"Fetching: {URL}")
    resp = requests.get(URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, "lxml")

    new_sel = "a.product-image"
    old_sel = "a[href*='bokno=']"

    new_boknos = extract_boknos(soup, new_sel)
    old_boknos = extract_boknos(soup, old_sel)

    print(f"\n新 selector ({new_sel}): {len(new_boknos)} 本")
    for b in new_boknos:
        print(f"  {b}")

    sidebar_extra = set(old_boknos) - set(new_boknos)
    print(f"\n舊 selector 比新的多出 {len(sidebar_extra)} 本（側欄/重複）: {sidebar_extra}")

    if len(new_boknos) >= 10:  # 每頁 18 本，至少要 10 本才算正常
        print("\n[PASS] selector 正常工作")
        sys.exit(0)
    else:
        print("\n[FAIL] 抓到的書籍太少，可能 selector 有誤")
        sys.exit(1)


if __name__ == "__main__":
    main()
