from __future__ import annotations

import os
from typing import Any

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options


def _normalize_base_url_v1(raw_value: Any, fallback: str) -> str:
    clean_value = str(raw_value or "").strip().rstrip("/")
    return clean_value or fallback.rstrip("/")


INTERNAL_APP_BASE_URL = _normalize_base_url_v1(
    os.getenv("APP_BASE_URL"),
    "http://web:8000",
)
EXTERNAL_APP_BASE_URL = _normalize_base_url_v1(
    os.getenv("APP_EXTERNAL_BASE_URL"),
    "http://127.0.0.1:8000",
)
SELENIUM_REMOTE_URL = str(os.getenv("SELENIUM_REMOTE_URL") or "").strip()


def _rewrite_base_url_v1(raw_url: Any, *, source_base_url: str, target_base_url: str) -> str:
    clean_url = str(raw_url or "").strip()
    if not clean_url:
        return ""

    normalized_sources = {
        source_base_url.rstrip("/"),
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    }
    normalized_target = target_base_url.rstrip("/")
    for normalized_source in normalized_sources:
        if normalized_source and clean_url.startswith(normalized_source):
            return normalized_target + clean_url[len(normalized_source) :]
    return clean_url


class BrowserDriverProxy:
    def __init__(self, driver: Any) -> None:
        self._driver = driver

    def get(self, url: str) -> Any:
        return self._driver.get(
            _rewrite_base_url_v1(
                url,
                source_base_url=EXTERNAL_APP_BASE_URL,
                target_base_url=INTERNAL_APP_BASE_URL,
            )
        )

    @property
    def current_url(self) -> str:
        return _rewrite_base_url_v1(
            self._driver.current_url,
            source_base_url=INTERNAL_APP_BASE_URL,
            target_base_url=EXTERNAL_APP_BASE_URL,
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._driver, name)

    def get_log(self, log_type: str) -> list[dict[str, Any]]:
        if hasattr(self._driver, "get_log"):
            return self._driver.get_log(log_type)
        return []

    def quit(self) -> Any:
        return self._driver.quit()


def _build_chrome_options_v1(options: Options | None = None) -> Options:
    browser_options = options or webdriver.ChromeOptions()
    browser_options.add_argument("--headless=new")
    browser_options.add_argument("--window-size=1440,1200")
    browser_options.add_argument("--disable-gpu")
    browser_options.add_argument("--no-sandbox")
    browser_options.add_argument("--disable-dev-shm-usage")
    return browser_options


def build_browser_driver_v1(*args: Any, **kwargs: Any) -> BrowserDriverProxy:
    options = kwargs.pop("options", None)
    browser_options = _build_chrome_options_v1(options)

    try:
        if SELENIUM_REMOTE_URL:
            remote_driver = webdriver.Remote(
                command_executor=SELENIUM_REMOTE_URL,
                options=browser_options,
            )
            return BrowserDriverProxy(remote_driver)

        local_driver = webdriver.Chrome(*args, options=browser_options, **kwargs)
        return BrowserDriverProxy(local_driver)
    except WebDriverException:
        raise
    except Exception as exc:  # pragma: no cover - bridge para falhas do driver remoto
        raise WebDriverException(str(exc)) from exc


def patch_webdriver_chrome_v1() -> None:
    webdriver.Chrome = build_browser_driver_v1  # type: ignore[assignment]
