# Project: Bookstore Scraper

## Core Objectives
- [x] 自動抓取三采文化官網（suncolor.com.tw）書籍資料
- [x] 篩選有效在售品項（排除缺書/絕版/停售）
- [x] 輸出結構化 Excel 報表（書名、定價、ISBN）
- [x] 完整資料品質驗證與 log 記錄
- [ ] v2：多書商擴充（博客來、誠品、金石堂）— 待規劃

## Phase Plan

### Phase A: 環境建置與網站探索 (Status: Completed)
- [x] A1. 建立專案目錄結構（scrapers/, models/, output/, utils/）
- [x] A2. 建立 requirements.txt + config.yaml 骨架
- [x] A3. 確認 suncolor.com.tw JS 渲染需求（OQ-01：不需要）
- [x] A4. 確認缺書 HTML 標記（OQ-02：schema.org availability + 按鈕文字）
- [x] A5. robots.txt 確認（/BookList.aspx 及 /BookPage.aspx 均合法）
- [x] A6. 分頁 URL 規則文件化（BookList.aspx?knd=0&knd2=XX&p=N）

### Phase B: 核心爬蟲實作 (Status: Completed)
- [x] B1. models/book.py（Book dataclass + 驗證邏輯）
- [x] B2. utils/logger.py（logging 設定）
- [x] B3. utils/http_client.py（retry + exponential backoff）
- [x] B4. scrapers/suncolor.py（目錄分頁巡覽 + 詳情頁解析 + 庫存過濾）
- [x] B5. config.yaml 完整設定（delay 1-3s、retry 3、timeout 15s）

### Phase C: 輸出與整合 (Status: Completed)
- [x] C1. output/excel_writer.py（openpyxl, ISBN 文字格式, 標題粗體）
- [x] C2. main.py 入口點整合
- [x] C3. Log 格式（執行起訖、總頁數、筆數、跳過分類）
- [x] C4. End-to-end 執行驗證

### Phase D: 測試與驗收 (Status: Completed)
- [x] D1. Unit tests for Book dataclass validators
- [x] D2. Unit tests for excel_writer（ISBN 格式驗證）
- [x] D3. 完整驗收 AC-01 ~ AC-07（全部通過）
- [x] D4. README.md

### Phase E: v2 多書商擴充 (Status: Completed 2026-03-07)
架構：BaseScraper 抽象類別 + --publisher 參數

已完成書商：
- [x] 三采文化 (suncolor.com.tw) — ASP.NET SSR, schema.org availability
- [x] 華碩文化 (weesing123.com.tw) — Shopline SSR, .grid-box a, price-old class
- [x] 采實文化 (acmebook.com.tw) — PHP SSR, book.php?sn=, 無庫存標記

### Phase F: 信誼（hsinyishop.com）(Status: Completed 2026-03-07)
- [x] 爬蟲架構：sitemap.xml → /products/ URLs → app.value('product', JSON) 提取
- [x] 無需 Playwright（OQ-F1 解決：資料嵌於靜態 HTML script 標籤）
- [x] scrapers/hsinyi.py + config.yaml hsinyi 區段 + main.py PUBLISHER_MAP
