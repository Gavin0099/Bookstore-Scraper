"""
檢查 JSON-LD 解析 Bug 與測試一本應在架的書
"""
import json
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# 一本確定在販售的書（用剛才爬到的）
# bokno 102020101059 = 9786263588257 曾出現在 log，這是個在架上的書
BOKNOS = {
    "112080301008": "露露愛數字（疑似停售）",
    "112080210011": "生活認知繪本套書（疑似停售）",
    "102020101059": "從 log 成功收錄的書（應在架）",
}

print("=== JSON-LD offers.availability 解析測試 ===\n")

for bokno, label in BOKNOS.items():
    url = f"https://www.suncolor.com.tw/BookPage.aspx?bokno={bokno}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, "lxml")

    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else "(無)"
    availability_top = "(無)"
    availability_offers = "(無)"

    for sc in soup.find_all("script", type="application/ld+json"):
        try:
            d = json.loads(sc.string or "")
            # 現有邏輯（讀頂層）
            av = d.get("availability", "")
            if av:
                availability_top = av
            # 正確邏輯（讀 offers 子物件）
            offers = d.get("offers", {})
            if isinstance(offers, dict):
                av2 = offers.get("availability", "")
                if av2:
                    availability_offers = av2
        except Exception:
            pass

    stop_kws = ["缺書", "缺貨", "絕版", "停售"]
    found_stop = [kw for kw in stop_kws if kw in resp.text]
    has_temp = "加入暫存清單" in resp.text

    # 現有 _is_available() 行為
    if availability_top and availability_top != "(無)":
        current_result = availability_top == "https://schema.org/InStock"
        current_method = f"頂層availability={availability_top}"
    elif found_stop:
        current_result = False
        current_method = f"排除詞={found_stop}"
    else:
        current_result = has_temp
        current_method = f"加入暫存清單={has_temp}"

    # 修正後的行為（優先讀 offers.availability）
    av_to_check = availability_offers if availability_offers != "(無)" else availability_top
    if av_to_check and av_to_check != "(無)":
        fixed_result = av_to_check == "https://schema.org/InStock"
        fixed_method = f"offers.availability={av_to_check}"
    elif found_stop:
        fixed_result = False
        fixed_method = f"排除詞={found_stop}"
    else:
        fixed_result = has_temp
        fixed_method = f"加入暫存清單={has_temp}"

    print(f"[{label}]")
    print(f"  書名: {title}")
    print(f"  頂層 availability: {availability_top}")
    print(f"  offers.availability: {availability_offers}")
    print(f"  停售詞: {found_stop}")
    print(f"  現有邏輯: {'收錄' if current_result else '跳過'} ({current_method})")
    print(f"  修正後  : {'收錄' if fixed_result else '跳過'} ({fixed_method})")
    print()
