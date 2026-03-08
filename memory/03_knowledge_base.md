# Knowledge Base

## 📚 Common Commands

- **安裝依賴**: `pip install -r requirements.txt`
- **執行爬蟲**: `python main.py`
- **執行測試**: `python -m pytest tests/ -v`

## 🐛 Troubleshooting

### 1. suncolor.com.tw JS 渲染需求確認 (2026-03-06) [Status: ✅ Fixed]
**Problem**: 不確定 suncolor.com.tw 是否需要 playwright 才能取得資料
**Root Cause**: 網站為 ASP.NET server-side rendering，不依賴前端 JS
**Solution**: 使用 requests + BeautifulSoup4 即可，無需 playwright
**Verification**: 以 requests.get 直接取得 BookPage.aspx，HTML 含完整書籍資料

### 2. ISBN Excel 格式問題 (2026-03-06) [Status: ✅ Fixed]
**Problem**: 13 碼 ISBN 在 Excel 中被自動轉為科學記號
**Root Cause**: openpyxl 預設將純數字字串判定為 numeric type
**Solution**: 寫入時明確設定 `cell.number_format = '@'` 或 `data_type = 's'`
**Verification**: test_excel_writer.py 中的 ISBN 格式單元測試

## 📖 各書商技術特徵（2026-03-07 確認）

| 書商 | URL | 渲染 | 分頁規則 | 定價解析 | 庫存判斷 |
|------|-----|------|---------|---------|---------|
| 三采文化 | suncolor.com.tw | ASP.NET SSR | BookList.aspx?knd=X&p=N | 「定價：NNN元」文字 | schema.org + 按鈕文字 |
| 華碩文化 | weesing123.com.tw | Shopline SSR | /{slug}?page=N | .price-old class | schema.org + 關鍵字 |
| 采實文化 | acmebook.com.tw | PHP SSR | book_list.php?page_num=N&bookType_sn1=XX | 「定價 NNN 元」 | 無標記，全部視為可售 |
| 信誼 | hsinyishop.com | Shopline Angular SPA | sitemap.xml → /products/hXXXX | product["price"]["dollars"] | product["sold_out"] |
| 小魯文化 | tienwei.com.tw | PHP SSR + AJAX 列表 | /product/include_product_index_list.php?bid=XX&page=N | 「定價：$NNN」 | 「缺貨」關鍵字 |
| 格林文化 | grimmpress.com.tw | OpenCart SSR（子分類） | ?route=product/category&path=59_XX&page=N | 「原價：NNN元」(.price-old) | id=button-cart 按鈕文字 |

### 信誼技術細節（OQ-F1 已解決 2026-03-07）
- 雖然是 Angular SPA，但商品資料以 `app.value('product', {...})` 嵌在靜態 HTML 的 `<script>` 標籤中
- **不需要 Playwright**：requests 即可取得，用 `json.JSONDecoder.raw_decode()` 提取 JSON
- 商品 URL 來源：`/sitemap.xml` 的 `<loc>` 標籤，約 500+ 個 /products/ URL
- ISBN：`product["gtin"]`（若 13 碼採用）；備援：頁面文字掃描
- 注意：gtin 可能是 12 位 EAN 而非 13 位 ISBN，此時 isbn 欄位會走備援方案

### 小魯文化技術細節（OQ-G1 已解決 2026-03-07）
- 分類頁面（`/product/39` 等）雖用 JS `getProduct()` 載入，但實際 AJAX 端點可直接 GET
- **AJAX URL**: `https://www.tienwei.com.tw/product/include_product_index_list.php?bid=XX&page=N`
- 每頁 20 筆，繪本(bid=39)共 886 筆 / 45 頁（其他分類數量各異）
- 詳情頁 `/product/detailXXXX` 為 SSR，書名在 `<h1>`，定價「定價：$NNN」，ISBN 含連字號
- ISBN 格式：`978-XXX-XXX-XXX-X` → `.replace("-", "")` → 13 碼
- 格林文化（grimmpress.com.tw）：OQ-H1 解決，見下方

### 格林文化技術細節（OQ-H1 已解決 2026-03-07）
- **關鍵陷阱**：WebFetch/curl 父分類（`path=59`）看不到產品；需用**子分類** `path=59_60` 格式才有靜態 HTML 產品列表
- 每頁 9 筆；子分類 0-3歲(59_60)=69筆/8頁；4-6歲(59_61)=234筆；7-9歲(59_62)=202筆
- 產品 URL：SEO 格式 `/product/{id}/{path}`（非標準 `?route=product/product&product_id=X`）
- 書名在詳情頁 `<h1>`，原價「原價：NNN元」（.price-old class），ISBN 含連字號
- 庫存：`id=button-cart` 按鈕存在且非缺貨關鍵字 = 可售；備援：關鍵字掃描

## 🚫 Anti-Patterns

### 1. 在 OQ 未確認前開始實作爬蟲 (2026-03-06)
**What was done wrong**: 若不先確認 JS 渲染需求，可能寫出無法使用的 playwright-based 爬蟲
**Why it's dangerous**: Phase B 全部實作可能需要推倒重來（技術選型錯誤）
**Correct approach**: Phase A 必須先確認 OQ-01/OQ-02，再進入 Phase B
**Reference**: Troubleshooting #1
