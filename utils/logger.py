import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logger(output_dir: str = ".", prefix: str = "scraper") -> logging.Logger:
    """建立同時輸出到 console 和 .log 檔案的 logger。

    log 檔名格式：{prefix}_YYYYMMDD_HHMMSS.log（spec §3.3）
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = Path(output_dir) / f"{prefix}_{timestamp}.log"

    logger = logging.getLogger("bookstore_scraper")
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    # File handler
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    logger.addHandler(ch)
    logger.addHandler(fh)

    logger.info("Log 檔案：%s", log_path)
    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger("bookstore_scraper")
