# 🛡️ Memory 治理架構 v5.2 - 部署包

## 📦 這是什麼?

這是一個**完整的 memory/ 層治理架構**,包含:
- 治理規則 (SYSTEM_PROMPT.md v5.2)
- 自動化工具 (記憶掃除 + Linear 整合)
- 整合文件

**特點**: 開箱即用,直接整合到任何專案的 `memory/` 目錄。

---

## 🗂️ 目錄結構

```
memory/
├── governance/
│   └── SYSTEM_PROMPT.md (v5.2)     ← 更新後的核心意識
│
├── governance_tools/               ← 自動化工具
│   ├── README.md                   ← 工具使用說明
│   ├── memory_janitor.py
│   └── linear_integrator.py
│
├── docs/                           ← 治理文件
│   └── INTEGRATION_GUIDE.md        ← 完整部署指南
│
└── archive/                        ← 歸檔目錄 (空白,供工具使用)
```

**注意**: 其他治理文件 (AGENT.md, ARCHITECTURE.md 等) 與狀態檔案 (00-03.md) 請從您原有的 memory/ 保留。

---

## 🚀 快速部署 (3 步驟)

### 方式 A: 手動部署

```bash
# 1. 解壓縮後,進入您的專案根目錄
cd <your-project>

# 2. 複製整個 memory/ 結構 (會保留現有檔案)
cp -r memory_architecture_v5.2/* memory/

# 3. 驗證
python memory/governance_tools/memory_janitor.py --check
```

---

### 方式 B: 使用自動化腳本 (推薦)

```bash
# 1. 複製部署腳本到專案根目錄
cp memory_architecture_v5.2/deploy_to_memory.sh ./

# 2. 執行部署 (會自動備份現有 SYSTEM_PROMPT.md)
bash deploy_to_memory.sh

# 3. 驗證
python memory/governance_tools/memory_janitor.py --check
```

---

## 📋 部署檢查清單

部署完成後,確認以下項目:

- [ ] `memory/governance/SYSTEM_PROMPT.md` 版本為 v5.2
- [ ] `memory/governance_tools/` 目錄已建立,包含 2 個 .py 檔案
- [ ] `memory/docs/INTEGRATION_GUIDE.md` 存在
- [ ] `memory/archive/` 目錄已建立
- [ ] 執行 `python memory/governance_tools/memory_janitor.py --check` 無錯誤

---

## 🔄 跨專案部署

這個架構設計為**可攜式**,您可以:

1. 將整個 `memory_architecture_v5.2/` 打包為 `.zip` 或 `.tar.gz`
2. 在任何新專案中解壓縮
3. 執行 `deploy_to_memory.sh` 即可完成部署

**範例**:
```bash
# 打包
tar -czf memory_governance_v5.2.tar.gz memory_architecture_v5.2/

# 在新專案中解壓縮
cd new-project/
tar -xzf memory_governance_v5.2.tar.gz
bash memory_architecture_v5.2/deploy_to_memory.sh
```

---

## 🛠️ 工具使用

### 記憶掃除
```bash
# 檢查狀態
python memory/governance_tools/memory_janitor.py --check

# 產出計畫
python memory/governance_tools/memory_janitor.py --plan

# 執行掃除
python memory/governance_tools/memory_janitor.py --execute
```

### Linear 整合
```bash
# 列出 Teams
python memory/governance_tools/linear_integrator.py --list-teams

# 同步任務
python memory/governance_tools/linear_integrator.py \
  --sync \
  --team-id <team-id> \
  --priority 2
```

---

## 📚 詳細文件

所有功能說明、故障排除請參閱:
- **memory/docs/INTEGRATION_GUIDE.md** (完整指南)
- **memory/governance_tools/README.md** (工具說明)

---

## 🆘 常見問題

### Q: 會覆蓋我現有的治理文件嗎?
**A**: 不會。此部署包僅更新 `SYSTEM_PROMPT.md`,其他 6 個文件 (AGENT.md 等) 不會被觸碰。

### Q: 會影響我的專案狀態檔案嗎?
**A**: 不會。`00_master_plan.md`, `01_active_task.md` 等檔案完全不受影響。

### Q: 如果我的專案沒有 memory/ 目錄怎麼辦?
**A**: 直接將 `memory_architecture_v5.2/` 重新命名為 `memory/`,然後補齊其他 6 個治理文件與 4 個狀態檔案。

---

**版本**: v5.2  
**最後更新**: 2025-02-25  
**相容性**: 向後相容 v5.1,可安全升級
