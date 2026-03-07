# Tech Stack

## 🏗️ Core Architecture
- **Language**: Python 3.10+
- **HTTP**: requests + BeautifulSoup4（suncolor.com.tw 為純靜態 HTML，無需 playwright）
- **Excel 輸出**: openpyxl
- **平台**: Windows / macOS（跨平台，無 native interop）
- **Native Interop**: 無

## 🧩 Key Modules

- **models/book.py**: `Book` dataclass，含定價/ISBN/書名驗證邏輯
- **utils/http_client.py**: retry + exponential backoff + random delay（1-3s）+ User-Agent
- **utils/logger.py**: 統一 logging 設定，輸出至 stdout + .log 檔
- **scrapers/suncolor.py**: 目錄分頁巡覽 + 書籍詳情頁解析 + 庫存狀態過濾
- **output/excel_writer.py**: openpyxl 寫入，ISBN 強制文字格式，標題列粗體
- **main.py**: 入口點，整合所有模組

## 🌐 網站結構（suncolor.com.tw）

| 項目 | 結果 |
|------|------|
| JS 渲染需求 | ❌ 不需要，純 ASP.NET server-side HTML |
| 缺書標記 | schema.org JSON-LD `"availability"` 欄位；備援：按鈕文字 |
| 目錄分頁 URL | 一般：`BookList.aspx?knd=0&knd2=XX` <br> 童書分齡推薦：`KidsBookList.aspx?knd=XX&knd2=XXXX` |
| 書籍詳情 URL | `BookPage.aspx?bokno=XXXXXXXXXX` |
| robots.txt | `/BookList.aspx`、`/KidsBookList.aspx`、`/BookPage.aspx` 均合法 |

## ⚠️ Known Gotchas & Solutions

- **ISBN 科學記號問題**:
    - Description: Excel 預設將 13 碼數字轉為科學記號
    - **Solution**: openpyxl 寫入時設定 cell.data_type = 's'，強制文字格式

- **定價解析**:
    - Description: 頁面同時有「定價」與「優惠價」
    - **Solution**: 以正則解析「定價：NNN元」，忽略優惠價欄位

- **側欄暢銷榜重複書籍**（2026-03-07 發現）:
    - Description: 目錄頁側欄含「全站暢銷榜」，每頁固定重複出現相同 bokno，導致爬蟲不斷進入詳情頁發請求再才判斷重複，嚴重浪費時間
    - **Solution 1**: CSS selector 改為 `a.product-image`（僅主商品格），排除側欄連結
    - **Solution 2**: `_seen_boknos: set` — 在發出詳情頁請求前即過濾已見過的 bokno
    - 驗證腳本: `scripts/verify_selector.py`
