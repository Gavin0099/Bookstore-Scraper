# 🚀 治理架構整合部署指南

> **版本**: v1.0  
> **最後更新**: 2025-02-25  
> **目的**: 指導如何將新增的記憶管理與 Linear 整合工具部署到現有治理架構中

---

## 📦 交付清單

本次整合新增以下檔案:

| 檔案 | 類型 | 優先級 | 用途 |
|------|------|--------|------|
| `SYSTEM_PROMPT_v5.2.md` | 治理文件 | Priority 1 | 核心意識 (含記憶掃除機制) |
| `governance_tools/memory_janitor.py` | 自動化工具 | Priority 8 | 記憶掃除執行器 |
| `governance_tools/linear_integrator.py` | 自動化工具 | Priority 9 | Linear API 整合 |
| `INTEGRATION_GUIDE.md` | 說明文件 | - | 本文件 |

---

## 🔧 部署步驟

### Step 1: 更新 SYSTEM_PROMPT.md

**選項 A: 完整替換 (推薦)**
```bash
# 備份現有版本
cp memory/governance/SYSTEM_PROMPT.md memory/governance/SYSTEM_PROMPT_v5.1_backup.md

# 部署新版本
cp SYSTEM_PROMPT_v5.2.md memory/governance/SYSTEM_PROMPT.md
```

**選項 B: 手動合併** (如果您對現有版本有自訂修改)
- 參考 v5.2 的 §2.⑥ 和 §6.4
- 手動加入記憶壓力檢測邏輯
- 更新 §8.1 目錄結構,新增 `governance_tools/`

---

### Step 2: 部署自動化工具

工具已經建立在 `governance_tools/` 目錄中,無需額外操作。

驗證:
```bash
ls -lh governance_tools/
# 預期輸出:
# memory_janitor.py
# linear_integrator.py
```

---

### Step 3: 設定 Linear API (選擇性)

**僅在需要使用 Linear 整合時執行此步驟**

1. 取得 Linear API Key:
   - 前往 Linear Settings → API → Personal API Keys
   - 建立新的 API Key

2. 設定環境變數:
   ```bash
   # 加入到 ~/.bashrc 或 ~/.zshrc
   export LINEAR_API_KEY="lin_api_xxxxxxxxxxxxxxxxxxxxxxxxxx"
   
   # 套用設定
   source ~/.bashrc
   ```

3. 驗證設定:
   ```bash
   python governance_tools/linear_integrator.py --list-teams
   ```

---

## 🎯 使用方式

### 記憶掃除工具

#### 檢查狀態
```bash
python governance_tools/memory_janitor.py --check
```

#### 產出掃除計畫
```bash
python governance_tools/memory_janitor.py --plan
```

#### 執行掃除
```bash
# 先模擬
python governance_tools/memory_janitor.py --execute --dry-run

# 正式執行
python governance_tools/memory_janitor.py --execute
```

---

### Linear 整合工具

#### 列出 Teams
```bash
python governance_tools/linear_integrator.py --list-teams
```

#### 同步任務
```bash
python governance_tools/linear_integrator.py \
  --sync \
  --team-id <your-team-id> \
  --priority 2
```

---

## 🤖 AI 自動化行為

AI 會在每次回應前自動檢測 `memory/01_active_task.md` 行數:

| 行數 | 行為 |
|------|------|
| 0-179 | 正常運作 |
| 180-199 | 顯示警告 |
| 200-249 | 建議執行掃除 |
| 250+ | **立即停止任務** |

**重要**: AI 僅會建議,不會自動執行掃除。

---

## 🛡️ 驗收測試

```bash
# 測試記憶工具
python governance_tools/memory_janitor.py --check

# 測試掃除計畫
python governance_tools/memory_janitor.py --plan

# 測試 Linear (需 API Key)
python governance_tools/linear_integrator.py --list-teams
```

---

## 📊 完整優先級結構

| 優先級 | 文件/工具 |
|--------|-----------|
| 1 | SYSTEM_PROMPT.md (v5.2) |
| 2 | HUMAN-OVERSIGHT.md |
| 3 | REVIEW_CRITERIA.md |
| 4 | AGENT.md |
| 5 | ARCHITECTURE.md |
| 6 | TESTING.md |
| 7 | NATIVE-INTEROP.md |
| **8** | **memory_janitor.py** |
| **9** | **linear_integrator.py** |

---

## 🆘 故障排除

### Python 版本過舊
```bash
python3 --version  # 需 >= 3.4
```

### Linear API 401 錯誤
```bash
echo $LINEAR_API_KEY  # 確認已設定
```

### AI 未檢測記憶壓力
確認 `memory/governance/SYSTEM_PROMPT.md` 包含 v5.2 的 §6.4 內容。

---

## 🧭 最終原則

> **工具是為了減少認知負擔,而非增加複雜度**
>
> **人永遠是治理的最終裁決者**
