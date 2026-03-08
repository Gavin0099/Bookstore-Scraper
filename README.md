# Bookstore Scraper

自動抓取多家出版社官網書籍資料，輸出 Excel 報表（ISBN、分類、書名、定價、簡介、圖片URL）。

## 支援書商

| 參數 | 出版社 | 網站 |
|------|--------|------|
| `suncolor` | 三采文化 | suncolor.com.tw |
| `weesing` | 華碩文化 | weesing123.com.tw |
| `acmebook` | 采實文化 | acmebook.com.tw |
| `hsinyi` | 信誼 | hsinyishop.com |
| `tienwei` | 小魯文化 | tienwei.com.tw |
| `grimm` | 格林文化 | grimmpress.com.tw |

## 需求

- Python 3.10+

## 安裝

```bash
pip install -r requirements.txt
```

## 執行

```bash
# 抓取特定書商（預設：suncolor）
python main.py --publisher suncolor
python main.py --publisher grimm
python main.py --publisher tienwei

# 指定輸出目錄
python main.py --publisher suncolor --output ./results

# 指定設定檔
python main.py --publisher suncolor --config config.yaml
```

產出檔案範例（以三采文化為例）：
- `三采文化_YYYYMMDD_HHMMSS.xlsx` — 書單
- `scraper_YYYYMMDD_HHMMSS.log` — 執行記錄

## Excel 欄位

| 欄位 | 說明 |
|------|------|
| ISBN | 13 碼，強制文字格式（避免科學記號） |
| 分類 | 書商分類名稱（如「繪本」「0-3歲適合閱讀」） |
| 書名 | 書籍標題 |
| 定價 | 原始定價（整數） |
| 簡介 | 內容簡介（前 500 字；部分書商不支援） |
| 圖片URL | 封面圖連結（部分書商不支援） |

> **注意**：簡介與圖片URL 目前僅三采文化（suncolor）完整支援，其他書商輸出空白。

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
├── main.py               # 入口點（--publisher 參數）
├── config.yaml           # 設定檔（各書商分類 URL）
├── requirements.txt
├── scrapers/
│   ├── base.py           # BaseScraper 抽象基底類別
│   ├── suncolor.py       # 三采文化（圖片+簡介已支援）
│   ├── weesing.py        # 華碩文化
│   ├── acmebook.py       # 采實文化
│   ├── hsinyi.py         # 信誼
│   ├── tienwei.py        # 小魯文化
│   └── grimm.py          # 格林文化
├── models/
│   └── book.py           # Book dataclass（含 image_url, description）
├── output/
│   └── excel_writer.py   # Excel 輸出（6 欄）
├── utils/
│   ├── http_client.py    # HTTP client（retry + backoff）
│   └── logger.py         # Log 設定
└── tests/                # 單元測試（32 項）
```
