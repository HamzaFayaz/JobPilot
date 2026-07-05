"""Search Helper configuration from worker/.env."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

WORKER_DIR = Path(__file__).resolve().parent


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=WORKER_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    jobpilot_api_base: str = "http://localhost:8000"
    worker_token: str = ""

    dashscope_api_key: str = ""
    qwen_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-plus"

    # Kimi WebBridge (v1) — replaces Browser-Use
    browser_provider: str = "webbridge"
    webbridge_url: str = "http://127.0.0.1:10086"

    # Deprecated (Browser-Use only — remove after WebBridge E2E)
    browser_chrome_profile: str = "Default"
    browser_user_data_dir: str = ""
    poll_interval_seconds: float = 3.0


def default_browser_user_data_dir() -> Path:
    """Deprecated — Browser-Use persistent profile dir. Not used with WebBridge."""
    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    base = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
    return base / "JobPilot" / "browser-use-user-data-dir-jobpilot"


def get_settings() -> WorkerSettings:
    return WorkerSettings()
