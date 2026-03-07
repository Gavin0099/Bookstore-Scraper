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

## 🚫 Anti-Patterns

### 1. 在 OQ 未確認前開始實作爬蟲 (2026-03-06)
**What was done wrong**: 若不先確認 JS 渲染需求，可能寫出無法使用的 playwright-based 爬蟲
**Why it's dangerous**: Phase B 全部實作可能需要推倒重來（技術選型錯誤）
**Correct approach**: Phase A 必須先確認 OQ-01/OQ-02，再進入 Phase B
**Reference**: Troubleshooting #1
