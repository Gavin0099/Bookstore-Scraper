"""
直接印出書籍詳情頁的 JSON-LD 完整結構
"""
import json
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# 露露愛數字
BOKNOS = ["112080301008", "112080210011"]

for bokno in BOKNOS:
    url = f"https://www.suncolor.com.tw/BookPage.aspx?bokno={bokno}"
    print(f"\n{'='*60}")
    print(f"bokno={bokno}: {url}")
    resp = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, "lxml")

    h1 = soup.find("h1")
    print(f"書名: {h1.get_text(strip=True) if h1 else '(無)'}")

    scripts = soup.find_all("script", type="application/ld+json")
    print(f"JSON-LD 數量: {len(scripts)}")
    for i, s in enumerate(scripts):
        try:
            data = json.loads(s.string or "")
            print(f"  [{i}] type={data.get('@type','?')} keys={list(data.keys())}")
            print(f"       availability={data.get('availability', '(無此欄位)')}")
            print(f"       offers={data.get('offers', '(無此欄位)')}")
        except Exception as e:
            print(f"  [{i}] parse error: {e} raw={repr(s.string[:100])}")

    # 購物車按鈕
    for kw in ["加入購物車", "加入暫存清單", "InStock", "SoldOut", "缺書", "停售"]:
        found = kw in resp.text
        print(f"  {'✓' if found else '✗'} {kw}")
