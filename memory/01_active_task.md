# Current Task: Bookstore Scraper — 效能優化完成

## Progress
- [x] Phase A: 環境建置與網站探索（2026-03-06 完成）
- [x] Phase B: 核心爬蟲實作（2026-03-06 完成）
- [x] Phase C: 輸出與整合（2026-03-06 完成）
- [x] Phase D: 測試與驗收（2026-03-06 完成，32 tests 全過）
- [x] 建立 memory/ 目錄（2026-03-06）
- [x] 爬蟲效能優化（2026-03-07 完成）
  - [x] 縮限分類至「親子教養」＋「童書/青少年文學」
  - [x] tqdm 進度條整合
  - [x] Excel 欄位順序修正為 ISBN → 書名 → 定價
  - [x] CSS selector 改為 `a.product-image`（排除側欄暢銷榜）
  - [x] `_seen_boknos` 預先過濾（發請求前跳過重複 bokno）
  - [x] `scripts/verify_selector.py` 驗證腳本
  - [x] `recover_from_log.py` log 還原腳本
  - [x] `.agent/workflows/scraper_ops.md` 操作手冊

## Context
- **Recent achievements**: 效能優化大幅改善抓取速度；2 分鐘完成 3 頁 / 32 筆（舊版相同量需數小時）
- **Root cause fixed**: 舊版 selector 抓到側欄暢銷榜，每遇重複書都浪費 1~3 秒網路請求
- **Next steps**: 等待 User 決定是否啟動 Phase E（v2 多書商）
