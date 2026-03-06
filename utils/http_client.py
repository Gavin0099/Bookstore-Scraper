import random
import time
from typing import Optional

import requests
from requests import Response

from utils.logger import get_logger

logger = get_logger()


class HttpClient:
    """帶有 retry、exponential backoff、隨機 delay 的 HTTP client（spec §4.2）。"""

    def __init__(
        self,
        user_agent: str,
        timeout: int = 15,
        max_retries: int = 3,
        backoff_factor: int = 2,
        delay_min: float = 1.0,
        delay_max: float = 3.0,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def get(self, url: str, **kwargs) -> Optional[Response]:
        """發送 GET 請求，失敗自動重試。

        回傳 Response 或 None（重試仍失敗時）。
        HTTP 4xx → 記 log，直接回傳 None（不重試）。
        HTTP 5xx / 逾時 → 最多重試 max_retries 次。
        """
        wait = 1.0
        for attempt in range(1, self.max_retries + 2):  # +1 for initial try
            try:
                resp = self.session.get(url, timeout=self.timeout, **kwargs)

                if 400 <= resp.status_code < 500:
                    logger.warning("HTTP %d（不重試）：%s", resp.status_code, url)
                    return None

                if resp.status_code >= 500:
                    raise requests.HTTPError(
                        f"HTTP {resp.status_code}", response=resp
                    )

                self._sleep()
                return resp

            except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
                if attempt > self.max_retries:
                    logger.error("請求失敗（已重試 %d 次）：%s — %s", self.max_retries, url, exc)
                    return None
                logger.warning(
                    "請求失敗（第 %d/%d 次），%.0f 秒後重試：%s — %s",
                    attempt, self.max_retries, wait, url, exc,
                )
                time.sleep(wait)
                wait *= self.backoff_factor

        return None  # unreachable, for type checker

    def _sleep(self) -> None:
        """請求間隨機等待（spec §4.2 要求 1–3 秒）。"""
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)
