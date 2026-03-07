"""
診斷特定書籍為何未被爬取
執行：python scripts/deep_diagnose.py
"""
import json
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
KEYWORDS = ["露露愛數字", "生活認知繪本套書 內褲"]


def search_boknos(keyword: str) -> list[str]:
    url = f"https://www.suncolor.com.tw/Search.aspx?keyword={keyword}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, "lxml")
    links = soup.select("a[href*=bokno]")
    seen, boknos = set(), []
    for a in links:
        m = re.search(r"bokno=(\w+)", a.get("href", ""))
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            boknos.append(m.group(1))
    return boknos


def diagnose_bokno(bokno: str) -> dict:
    url = f"https://www.suncolor.com.tw/BookPage.aspx?bokno={bokno}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, "lxml")
    text = resp.text

    # 書名
    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else "(無)"

    # ISBN
    m_isbn = re.search(r"ISBN[：:]\s*(\d+)", soup.get_text())
    isbn = m_isbn.group(1) if m_isbn else "(無)"

    # JSON-LD availability
    availability = "(無 JSON-LD)"
    json_ld_count = 0
    for sc in soup.find_all("script", type="application/ld+json"):
        json_ld_count += 1
        try:
            d = json.loads(sc.string or "")
            av = d.get("availability", "")
            if av:
                availability = av
        except Exception:
            pass

    # 備援關鍵字
    has_cart = "加入購物車" in text
    has_temp = "加入暫存清單" in text
    exclude_kws = ["缺書", "缺貨", "絕版", "停售"]
    found_exclude = [kw for kw in exclude_kws if kw in text]

    # is_available 邏輯
    if availability and availability != "(無 JSON-LD)":
        is_available = (availability == "https://schema.org/InStock")
        method = "JSON-LD"
    elif found_exclude:
        is_available = False
        method = f"備援排除詞({found_exclude})"
    else:
        is_available = has_temp
        method = f"備援-加入暫存清單={has_temp}"

    return {
        "bokno": bokno,
        "title": title,
        "isbn": isbn,
        "json_ld_count": json_ld_count,
        "availability": availability,
        "has_cart": has_cart,
        "has_temp_list": has_temp,
        "found_exclude_kws": found_exclude,
        "is_available": is_available,
        "decision_method": method,
        "url": url,
    }


def main():
    for kw in KEYWORDS:
        print(f"\n{'='*60}")
        print(f"搜尋: {kw}")
        print(f"{'='*60}")
        boknos = search_boknos(kw)
        if not boknos:
            print("  ❌ 搜尋無結果")
            continue
        print(f"  找到 bokno: {boknos[:5]}")
        for bokno in boknos[:3]:
            d = diagnose_bokno(bokno)
            scraper_decision = "✅ 會被收錄" if d["is_available"] else "❌ 被跳過（不可購買）"
            print(f"\n  [{scraper_decision}]")
            print(f"    書名     : {d['title']}")
            print(f"    ISBN     : {d['isbn']}")
            print(f"    JSON-LD  : {d['json_ld_count']} 個，availability={d['availability']}")
            print(f"    購物車   : cart={d['has_cart']}, 暫存清單={d['has_temp_list']}")
            print(f"    排除詞   : {d['found_exclude_kws']}")
            print(f"    判斷依據 : {d['decision_method']}")
            print(f"    URL      : {d['url']}")


if __name__ == "__main__":
    main()
