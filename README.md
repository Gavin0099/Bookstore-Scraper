# Bookstore Scraper

自動抓取三采文化官網書籍資料，輸出 Excel 報表（書名、定價、ISBN）。

## 需求

- Python 3.10+

## 安裝

```bash
pip install -r requirements.txt
```

## 執行

```bash
python main.py
```

產出檔案（與執行目錄同層）：
- `suncolor_books_YYYYMMDD_HHMMSS.xlsx` — 書單
- `scraper_YYYYMMDD_HHMMSS.log` — 執行記錄

### 選項

```bash
python main.py --config config.yaml   # 指定設定檔（預設）
python main.py --output ./results     # 指定輸出目錄
```

## 設定（config.yaml）

```yaml
scraper:
  delay_min: 1.0      # 請求間隔下限（秒）
  delay_max: 3.0      # 請求間隔上限（秒）
  timeout: 15         # 單頁逾時（秒）
  max_retries: 3      # 最大重試次數
```

## 執行測試

```bash
python -m pytest tests/ -v
```

## 專案結構

```
├── main.py               # 入口點
├── config.yaml           # 設定檔
├── requirements.txt
├── scrapers/
│   └── suncolor.py       # 三采文化爬蟲
├── models/
│   └── book.py           # Book dataclass
├── output/
│   └── excel_writer.py   # Excel 輸出
├── utils/
│   ├── http_client.py    # HTTP client（retry + backoff）
│   └── logger.py         # Log 設定
└── tests/                # 單元測試
```
