"""Search Helper configuration from worker/.env."""

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

    browser_chrome_profile: str = "Profile 1"
    poll_interval_seconds: float = 3.0


def get_settings() -> WorkerSettings:
    return WorkerSettings()
