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

    browser_provider: str = "webbridge"
    webbridge_url: str = "http://127.0.0.1:10086"
    poll_interval_seconds: float = 3.0
    agent_max_steps: int = 40
    save_snapshots: bool = True
    snapshot_dir: Path = WORKER_DIR / "debug_snapshots"
    snapshot_max_chars: int = 12000


def get_settings() -> WorkerSettings:
    return WorkerSettings()
