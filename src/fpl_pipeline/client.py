"""Thin HTTP client for the FPL API with retries, timeouts and polite pacing."""

import logging
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import config

log = logging.getLogger(__name__)


class FPLClient:
    def __init__(
        self,
        base_url: str = config.BASE_URL,
        timeout: float = config.REQUEST_TIMEOUT_SECONDS,
        delay: float = config.REQUEST_DELAY_SECONDS,
        max_retries: int = config.MAX_RETRIES,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        self.delay = delay

        self.session = requests.Session()
        self.session.headers["User-Agent"] = config.USER_AGENT

        # Retry transient failures with exponential backoff (1s, 2s, 4s, ...).
        # The FPL API often returns 503 while it updates after a gameweek.
        retry = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
            respect_retry_after_header=True,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """GET a path relative to the base URL and return the decoded JSON."""
        url = self.base_url + path.lstrip("/")
        log.info("GET %s params=%s", url, params)
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        time.sleep(self.delay)
        return response.json()
