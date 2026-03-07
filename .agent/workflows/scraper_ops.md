---
description: 常用操作指令與爬蟲工作流程
---

# 三采文化爬蟲 操作 Workflow

## 一、啟動爬蟲（正常模式）
```powershell
cd d:\Bookstore-Scraper
python main.py
```

## 二、驗證 CSS selector 是否正確
```powershell
cd d:\Bookstore-Scraper
python scripts/verify_selector.py
```
- `[PASS]`：selector 正確；`[FAIL]`：需要修正 selector

## 三、從 log 恢復資料（程式被強制中止時使用）
```powershell
cd d:\Bookstore-Scraper
python recover_from_log.py
```
- 輸出：`suncolor_books_recovered_YYYYMMDD_HHMMSS.xlsx`

## 四、執行測試
```powershell
cd d:\Bookstore-Scraper
pytest tests/ -v
```

## 五、查看目前爬取進度（從 log）
```powershell
# 最後 20 行
powershell -Command "Get-Content scraper_YYYYMMDD_HHMMSS.log -Tail 20"

# 成功書籍數
python -c "import re; lines=open('scraper_YYYYMMDD_HHMMSS.log',encoding='utf-8').readlines(); print(f'Success: {len([l for l in lines if \"[DEBUG] \" in l])}')"
```

## 六、更換目標分類
編輯 `config.yaml` 中的 `categories` 區塊：
```yaml
categories:
  - {knd: "0", knd2: "13", name: "親子教養"}
  - {knd: "0", knd2: "14", name: "童書/青少年文學"}
```

## 七、驗證並重啟（最常用的組合指令）
// turbo-all
```powershell
cd d:\Bookstore-Scraper
python scripts/verify_selector.py && python main.py
```
