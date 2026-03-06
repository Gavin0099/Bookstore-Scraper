"""Bookstore Scraper — 三采文化書籍資料擷取工具

使用方式：
    python main.py
    python main.py --config config.yaml
    python main.py --output ./results
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import yaml

from models.book import Book
from output.excel_writer import write_excel
from scrapers.suncolor import SuncolorScraper
from utils.http_client import HttpClient
from utils.logger import get_logger, setup_logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="三采文化書籍爬蟲")
    parser.add_argument(
        "--config", default="config.yaml", help="設定檔路徑（預設：config.yaml）"
    )
    parser.add_argument(
        "--output", default=".", help="輸出目錄（預設：當前目錄）"
    )
    return parser.parse_args()


def load_config(path: str) -> dict:
    config_path = Path(path)
    if not config_path.exists():
        print(f"[ERROR] 找不到設定檔：{path}", file=sys.stderr)
        sys.exit(1)
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    args = parse_args()
    config = load_config(args.config)

    # 初始化 logger（spec §3.3）
    log_prefix = config.get("output", {}).get("log_prefix", "scraper")
    logger = setup_logger(output_dir=args.output, prefix=log_prefix)

    start_time = datetime.now()
    logger.info("=== 三采文化書籍爬蟲 啟動 ===")
    logger.info("設定檔：%s", args.config)
    logger.info("輸出目錄：%s", args.output)

    # 確認 robots.txt 合法（已於 Phase A 人工確認，此處記 log）
    logger.info("robots.txt 確認：/BookList.aspx 和 /BookPage.aspx 均未被 Disallow")

    # 初始化 HTTP client
    scraper_cfg = config["scraper"]
    client = HttpClient(
        user_agent=scraper_cfg["user_agent"],
        timeout=scraper_cfg["timeout"],
        max_retries=scraper_cfg["max_retries"],
        backoff_factor=scraper_cfg["backoff_factor"],
        delay_min=scraper_cfg["delay_min"],
        delay_max=scraper_cfg["delay_max"],
    )

    # 執行爬蟲
    scraper = SuncolorScraper(config=config, client=client)
    books: list[Book] = []

    try:
        for book in scraper.scrape_all():
            books.append(book)
            logger.debug("✓ %s | %d | %s", book.isbn, book.price, book.title[:30])
    except KeyboardInterrupt:
        logger.warning("使用者中斷執行")

    # 輸出 Excel
    excel_path = write_excel(books, output_dir=args.output)
    logger.info("Excel 輸出：%s（%d 筆）", excel_path, len(books))

    # 執行摘要 log（spec §3.3）
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()
    st = scraper.stats

    logger.info("=== 執行摘要 ===")
    logger.info("執行時間：%s → %s（%.1f 秒）", start_time.strftime("%H:%M:%S"), end_time.strftime("%H:%M:%S"), elapsed)
    logger.info("總抓取頁數：%d", st["pages"])
    logger.info("總處理筆數：%d", st["processed"])
    logger.info("成功輸出：%d", st["success"])
    logger.info("跳過（不可購買）：%d", st["skipped_unavailable"])
    logger.info("跳過（ISBN 缺失）：%d", st["skipped_no_isbn"])
    logger.info("跳過（資料不合格）：%d", st["skipped_invalid"])
    logger.info("跳過（重複 ISBN）：%d", st["skipped_duplicate"])
    logger.info("跳過（解析失敗）：%d", st["skipped_parse_error"])
    logger.info("=== 完成 ===")


if __name__ == "__main__":
    main()
