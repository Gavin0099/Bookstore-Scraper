# PLAN.md — Bookstore Scraper

> **專案類型**: 爬蟲工具 / 資料擷取
> **技術棧**: Python 3.10+ / requests + BeautifulSoup4 / openpyxl
> **複雜度**: L2
> **預計工期**: 2026/03/06 ~ 2026/03/27
> **最後更新**: 2026-03-06
> **Owner**: GavinWu
> **Freshness**: Sprint (7d)

---

## 📋 專案目標

自動抓取三采文化官網（suncolor.com.tw）的書籍資料，篩選有效在售品項，輸出結構化 Excel 報表供內部書單管理使用。

**Bounded Context**:
- 三采文化官網書籍目錄分頁巡覽
- 書籍詳情頁資料擷取（書名、定價、ISBN）
- 庫存狀態過濾（排除缺書/絕版/停售）
- 資料品質驗證與 log 記錄
- Excel (.xlsx) 報表輸出

**不負責**:
- 其他書商（博客來、誠品、金石堂）— v2+ Backlog
- 折扣價、電子書、有聲書
- 會員登入後的特殊價格
- 即時庫存數量（僅判斷有無缺書）
- 多書商比價

---

## 🏗️ 當前階段

```
階段進度:
├─ [✓] Phase A: 環境建置與網站探索   (2026/03/06 完成)
├─ [✓] Phase B: 核心爬蟲實作         (2026/03/06 完成)
├─ [✓] Phase C: 輸出與整合           (2026/03/06 完成)
└─ [🔄] Phase D: 測試與驗收           (進行中，預計 2026/03/09)
```

**當前 Phase**: **Phase D — 測試與驗收**

---

## 📦 Phase 詳細規劃

### Phase A: 環境建置與網站探索 (已完成 ✓)

**目標**: 確認執行環境、了解 suncolor.com.tw DOM 結構，回答所有 Open Questions。

**任務清單**:
```
├─ [✓] A1. 建立專案目錄結構（scrapers/, models/, output/, utils/）
└─ [✓] A2. 建立 requirements.txt + config.yaml 骨架
├─ [✓] A3. 人工確認 suncolor.com.tw 是否需要 JS 渲染（OQ-01）  ← 已完成 2026-03-06
├─ [✓] A4. 逆向確認缺書的 HTML 標記（OQ-02）                   ← 已完成 2026-03-06
├─ [✓] A5. 確認 robots.txt 並記錄結果                          ← 已完成 2026-03-06
└─ [✓] A6. 確認分頁 URL 規則（catalog pagination 結構）         ← 已完成 2026-03-06
```

**探索結果（2026-03-06 確認）**:

| 項目 | 結果 |
|------|------|
| OQ-01 JS 渲染 | ❌ 不需要。純 ASP.NET server-side HTML，requests+BeautifulSoup4 即可 |
| OQ-02 缺書標記 | ✅ 詳見下方 |
| robots.txt | `/BookList.aspx`、`/BookPage.aspx` 均未被 Disallow |
| 分頁 URL | `BookList.aspx?knd=0&knd2=XX&p=N&pagesize=18&sort=` |
| 書籍詳情 URL | `BookPage.aspx?bokno=XXXXXXXXXX` |
| 全分類入口 | `knd=0&knd2=` 共 20 個大分類（文學、童書、漫畫…等） |

**OQ-02 庫存狀態 HTML 標記**:
- **可購買**：頁面有「加入暫存清單」按鈕；schema.org JSON-LD `"availability": "https://schema.org/InStock"`
- **停售**：頁面顯示文字「停售無法購買」；schema.org `"availability": "https://schema.org/SoldOut"`
- **過濾策略**：優先使用 schema.org JSON-LD availability 欄位；備援方案：button/text 中有無「加入暫存清單」

**資料擷取 DOM 結構**:
- **書名**: `<h1>` 文字
- **定價**: 文字解析 `定價：NNN元` → 整數 NNN（注意：頁面也有「優惠價」，以「定價」為準）
- **ISBN**: 文字解析 `ISBN：XXXXXXXXXXXXX`（13 碼）
- **庫存**: schema.org JSON-LD `"availability"` 或按鈕文字

**Gate 條件**:
- [x] OQ-01（JS 渲染需求）有明確答案並記錄
- [x] OQ-02（缺書 HTML 標記）有明確答案並記錄
- [x] robots.txt 已確認，合法路徑已記錄
- [x] 分頁 URL 規則已文件化
- [x] requirements.txt 和 config.yaml 骨架已建立

---

### Phase B: 核心爬蟲實作 (已完成 ✓)

**目標**: 實作所有爬蟲模組，可完整跑一次取得資料（不含 Excel 輸出）。

**任務清單**:
```
├─ [⏳] B1. models/book.py（Book dataclass + 資料品質驗證邏輯）
├─ [⏳] B2. utils/logger.py（logging 設定）
├─ [⏳] B3. utils/http_client.py（retry + exponential backoff + User-Agent）
├─ [⏳] B4a. scrapers/suncolor.py — 目錄頁分頁巡覽
├─ [⏳] B4b. scrapers/suncolor.py — 書籍詳情頁解析（書名、定價、ISBN）
├─ [⏳] B4c. scrapers/suncolor.py — 庫存狀態過濾
└─ [⏳] B5. config.yaml 完整填寫（delay 1-3s、retry 3、timeout 15s）
```

**Gate 條件**:
- [ ] 可完整跑過所有目錄分頁（pagination 正確翻到最後一頁）
- [ ] 缺書品項（缺書/缺貨/絕版/停售/預購）正確被過濾
- [ ] 4 條資料品質規則（定價≤0、ISBN非13碼、書名空、重複ISBN）全部有對應 log
- [ ] HTTP 請求間隔符合 1–3 秒隨機（AC-06）
- [ ] 單頁失敗不中止程式（AC-05）

---

### Phase C: 輸出與整合 (已完成 ✓)

**目標**: Excel 輸出 + Log 輸出 + main.py 整合，產出可交付的執行檔。

**任務清單**:
```
├─ [⏳] C1. output/excel_writer.py（openpyxl, ISBN 強制文字格式, 標題列粗體）
├─ [⏳] C2. main.py 入口點整合
├─ [⏳] C3. Log 格式實作（執行起訖、總頁數、筆數、跳過原因分類）
└─ [⏳] C4. 完整 end-to-end 執行，產出實際 .xlsx + .log 確認
```

**Gate 條件**:
- [ ] AC-01: xlsx 含書名/定價/ISBN 三欄，第一列粗體標題
- [ ] AC-02: 缺書品項不出現在 Excel 中
- [ ] AC-03: ISBN 為文字格式（Excel 不轉成科學記號）
- [ ] AC-04: log 記錄跳過筆數與原因分類
- [ ] AC-05: 單頁錯誤時程式不中止

---

### Phase D: 測試與驗收 (待開始 ⏳)

**目標**: 補齊單元測試，驗收全部 7 條 AC，產出 README。

**任務清單**:
```
├─ [⏳] D1. Unit tests for Book dataclass validators
├─ [⏳] D2. Unit tests for excel_writer（ISBN 格式驗證）
├─ [⏳] D3. 完整驗收 AC-01 ~ AC-07
└─ [⏳] D4. README.md 撰寫（安裝步驟、執行方式、設定說明）
```

**Gate 條件**:
- [ ] AC-01 ~ AC-07 全部通過（見 spec §6）
- [ ] Unit test 覆蓋 Book 驗證邏輯（定價、ISBN、書名、重複）
- [ ] README 可讓新人照做在 10 分鐘內跑起來

---

## 🔥 本週聚焦 (Sprint 1)

**Sprint 1** (2026/03/06 - 2026/03/09)

**目標**: 完成環境建置，回答 OQ-01 / OQ-02，讓 Phase B 可以無阻礙開始。

**任務清單** (≤5 項):
- [ ] A1. 建立專案目錄結構（scrapers/, models/, output/, utils/）(1h)
- [ ] A2. 建立 requirements.txt + config.yaml 骨架 (1h)
- [ ] A3. 人工確認 suncolor.com.tw JS 渲染需求（OQ-01）(2h)
- [ ] A4. 逆向確認缺書 HTML 標記（OQ-02）(2h)
- [ ] A5+A6. robots.txt 確認 + 分頁 URL 規則文件化 (1h)

**下一步** (完成 Sprint 1 後):
1. 依 OQ-01 結果決定用 requests+BeautifulSoup4 還是 playwright
2. 開始 Phase B — B1 (models/book.py)

**當前阻礙**:
- ⚠️ OQ-01、OQ-02 未回答（Sprint 1 核心任務）

**需要決策**:
- ⚠️ OQ-01 答案將決定 Phase B 技術選型（requests vs playwright）

---

## 📊 待辦清單 (Backlog)

### 高優先 (P0)
- [ ] 解決 OQ-01: suncolor.com.tw 是否需要 JS 渲染
- [ ] 解決 OQ-02: 缺書的 HTML 標記為何

### 中優先 (P1)
- [ ] OQ-04: Excel 是否需要依分類/出版日期排序
- [ ] 完整 Phase B 爬蟲實作
- [ ] 完整 Phase C 輸出整合

### 低優先 (P2)
- [ ] OQ-03: 是否需要代理 IP Pool（視封鎖力度決定）
- [ ] 多書商擴充（博客來、誠品、金石堂）— v2
- [ ] 多書商比價功能 — v2
- [ ] 增量更新（僅抓新增/變動品項）— v2
- [ ] 排程自動執行（cron）— v2
- [ ] 輸出格式擴充（CSV、Google Sheets）— v2

---

## 🚫 不要做 (Anti-Goals)

❌ **Phase A 禁止**:
- 不要在 OQ-01/OQ-02 確認前就開始寫 scrapers/suncolor.py（可能白做）
- 不要在 Phase A 實作 Excel 輸出（Phase C 才做）
- 不要考慮多書商擴充（spec v1 明確 Out of Scope）
- 不要加代理 IP Pool（OQ-03 待觀察，Phase A 不做）
- 不要寫單元測試（Phase D 才做）

---

## 🤖 AI 協作規則

**AI 在實作任何功能前，必須確認**:

1. ✅ 這項任務在「本週聚焦」或「下一步」中嗎?
2. ✅ 是否符合當前 Phase A 的範圍?
3. ✅ 是否在「不要做」清單中?

**如果不符合上述條件**:
- 先詢問是否調整 PLAN
- 不要自行決定優先級
- 提供明確的選項 (A/B/C)

**範例**:
```
User: 幫我加博客來爬蟲
AI: 我看到 PLAN.md:
    - 當前 Phase A（環境建置與探索）
    - 多書商擴充在 Backlog P2（v2）
    - Phase A 禁止：不要考慮多書商擴充

    選項:
    A) 遵守計畫，v2 再處理
    B) 調整 PLAN，將多書商提前至新的 Phase E

    你希望如何處理?
```

---

## 🎯 Gate 與驗收標準

### Phase A Gate（進入 Phase B 的條件）

**探索完整性**:
- [ ] OQ-01 答案明確（需/不需 JS 渲染）
- [ ] OQ-02 答案明確（缺書 HTML class/text 確認）
- [ ] robots.txt 確認並記錄

**環境完整性**:
- [ ] 目錄結構建立完成（scrapers/, models/, output/, utils/）
- [ ] requirements.txt 有基本依賴
- [ ] config.yaml 有 delay/retry/timeout 設定骨架

---

### Phase D Gate（最終驗收，7 條 AC）

**功能驗收**:
- [ ] AC-01: 執行後產出 `.xlsx`，包含書名、定價、ISBN 三欄
- [ ] AC-02: 缺書品項不出現在 Excel 中
- [ ] AC-03: ISBN 格式正確（13 碼字串，不被 Excel 轉為科學記號）
- [ ] AC-04: 執行後產出 `.log`，記錄跳過筆數與原因
- [ ] AC-05: 單次執行遇到單頁錯誤時，程式不中止，繼續處理其餘頁
- [ ] AC-06: 請求間隔符合設定（1–3 秒隨機）
- [ ] AC-07: 重複 ISBN 僅保留一筆

**代碼品質**:
- [ ] Book dataclass 驗證邏輯有單元測試
- [ ] excel_writer ISBN 格式有單元測試

**文檔完整性**:
- [ ] README.md 可讓新人 10 分鐘內跑起來

---

## 📝 已知問題

| ID | 問題 | 嚴重程度 | 狀態 | 負責人 |
|---|---|---|---|---|
| OQ-01 | suncolor.com.tw 是否需要 JS 渲染？ | P0 | ✅ 不需要，純靜態 HTML | GavinWu |
| OQ-02 | 缺書的 HTML 標記為何？ | P0 | ✅ schema.org availability + 按鈕文字 | GavinWu |
| OQ-03 | 是否需要代理 IP Pool？ | P2 | ⏳ 待觀察 | TBD |
| OQ-04 | Excel 是否需要排序？ | P1 | ⏳ 待決策 | TBD |

---

## 🔧 技術債務追蹤

| ID | 債務描述 | 預計償還時間 | 優先級 |
|---|---|---|---|
| DEBT-001 | 若 Phase A 確認需要 playwright，Phase B 需調整所有 http_client 設計 | Phase B 開始前 | P0 |

---

## 📅 里程碑

| 里程碑 | 目標日期 | 狀態 | 交付物 |
|---|---|---|---|
| M1: 環境就緒 + DOM 探索完成 | 2026/03/09 | 🔄 | OQ-01/02 答案、目錄結構、requirements.txt |
| M2: 爬蟲核心可跑 | 2026/03/16 | ⏳ | 可取得完整資料（書名/定價/ISBN，無 Excel） |
| M3: 可交付執行版本 | 2026/03/20 | ⏳ | .xlsx + .log 輸出，AC-01~05 通過 |
| M4: 完整驗收通過 | 2026/03/27 | ⏳ | AC-01~07 全過 + 單元測試 + README |

---

## 🔄 變更歷史

| 日期 | 變更內容 | 原因 |
|---|---|---|
| 2026/03/06 | 建立 PLAN.md，啟動 Phase A | 依 bookstore-scraper-spec.md v1.0 初始化專案計畫 |
| 2026/03/06 | 完成 A3~A6：OQ-01/02 解答、robots.txt、分頁規則 | 直接查詢官網 HTML 確認 |
| 2026/03/06 | 完成 A1+A2：目錄結構、requirements.txt、config.yaml | Phase A Gate 全部通過，進入 Phase B |
| 2026/03/06 | 完成 Phase B：book.py、logger.py、http_client.py、suncolor.py | 核心爬蟲模組全部實作 |
| 2026/03/06 | 完成 Phase C：excel_writer.py、main.py | 輸出整合完成，進入 Phase D 驗收 |
