"""Application settings loaded from .env and config/llm.yaml."""

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Qwen / Dashscope
    dashscope_api_key: str = ""
    qwen_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen3.7-plus"
    profile_llm_model: str = ""

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    # GitHub OAuth
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "http://localhost:8000/auth/github/callback"

    # App
    frontend_url: str = "http://localhost:5173"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    app_env: str = "development"

    # Auth & encryption
    jwt_secret: str = ""
    jwt_expire_minutes: int = 10080  # 7 days
    data_encryption_key: str = ""

    # Search Helper / ECS orchestration (system settings — not user search prefs)
    browser_search_wait_timeout_seconds: int = 120
    worker_heartbeat_stale_seconds: int = 60

    # Paths
    data_dir: Path = ROOT / "data"
    uploads_dir: Path = ROOT / "data" / "uploads"
    db_path: Path = ROOT / "data" / "jobpilot.db"
    llm_config_path: Path = ROOT / "config" / "llm.yaml"

    @property
    def profile_model(self) -> str:
        if self.profile_llm_model:
            return self.profile_llm_model
        return self.llm_config.get("profile", {}).get("model", "qwen-turbo")

    @property
    def profile_temperature(self) -> float:
        return float(self.llm_config.get("profile", {}).get("temperature", 0.1))

    @property
    def profile_max_tokens(self) -> int:
        return int(self.llm_config.get("profile", {}).get("max_tokens", 2048))

    @property
    def evidence_model(self) -> str:
        return self.llm_config.get("evidence", {}).get("model", "qwen3.7-plus")

    @property
    def evidence_temperature(self) -> float:
        return float(self.llm_config.get("evidence", {}).get("temperature", 0.1))

    @property
    def evidence_max_tokens(self) -> int:
        return int(self.llm_config.get("evidence", {}).get("max_tokens", 4096))

    @property
    def llm_config(self) -> dict:
        return _load_llm_yaml(self.llm_config_path)

    @property
    def cookie_secure(self) -> bool:
        # Secure cookies only work over HTTPS; production hackathon deploy uses plain HTTP.
        return self.frontend_url.startswith("https://")

    def user_uploads_dir(self, user_id: int) -> Path:
        return self.uploads_dir / str(user_id)


@lru_cache
def _load_llm_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
