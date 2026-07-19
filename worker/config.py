"""Search Helper configuration from worker/.env."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from worker.runtime_paths import worker_data_dir

WORKER_DIR = Path(__file__).resolve().parent
DATA_DIR = worker_data_dir()


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=DATA_DIR / ".env",
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
    # cloud = thin WebBridge executor (no local Dashscope); local = legacy ReAct on PC
    agent_mode: str = "cloud"
    agent_max_steps: int = 40
    save_snapshots: bool = True
    snapshot_dir: Path = DATA_DIR / "debug_snapshots"
    snapshot_max_chars: int = 12000


def get_settings() -> WorkerSettings:
    return WorkerSettings()
