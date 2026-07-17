"""Application settings loaded from .env and config/llm.yaml."""

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import Field
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

    # Observability and explicit evaluation runner (independent switches)
    logfire_enabled: bool = False
    pydantic_evals_enabled: bool = False
    logfire_token: str = ""
    logfire_project_name: str = "jobpilot"
    logfire_environment: str = "development"
    logfire_capture_content: bool = False
    eval_results_dir: Path = ROOT / "tests" / "complete-pipeline-test" / "results"
    eval_capture_full_payloads: bool = False

    # Optional environment overrides for config/llm.yaml.
    application_model_override: str = Field("", validation_alias="APPLICATION_MODEL")
    application_temperature_override: float | None = Field(
        None, validation_alias="APPLICATION_TEMPERATURE"
    )
    application_enable_thinking_override: bool | None = Field(
        None, validation_alias="APPLICATION_ENABLE_THINKING"
    )
    application_prompt_version_override: str = Field(
        "", validation_alias="APPLICATION_PROMPT_VERSION"
    )
    application_schema_version_override: str = Field(
        "", validation_alias="APPLICATION_SCHEMA_VERSION"
    )
    application_repair_retries_override: int | None = Field(
        None, validation_alias="APPLICATION_REPAIR_RETRIES"
    )
    application_fit_threshold_override: int | None = Field(
        None, validation_alias="APPLICATION_FIT_THRESHOLD"
    )
    eval_judge_model_override: str = Field("", validation_alias="EVAL_JUDGE_MODEL")
    eval_judge_temperature_override: float | None = Field(
        None, validation_alias="EVAL_JUDGE_TEMPERATURE"
    )
    eval_max_concurrency_override: int | None = Field(
        None, validation_alias="EVAL_MAX_CONCURRENCY"
    )

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
    faiss_dir: Path = ROOT / "data" / "faiss"
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
    def application_model(self) -> str:
        return self.application_model_override or self.llm_config.get(
            "application", {}
        ).get("model", "qwen3.7-plus-2026-05-26")

    @property
    def application_temperature(self) -> float:
        if self.application_temperature_override is not None:
            return self.application_temperature_override
        return float(self.llm_config.get("application", {}).get("temperature", 0.1))

    @property
    def application_enable_thinking(self) -> bool:
        if self.application_enable_thinking_override is not None:
            return self.application_enable_thinking_override
        return bool(
            self.llm_config.get("application", {}).get("enable_thinking", False)
        )

    @property
    def application_prompt_version(self) -> str:
        return self.application_prompt_version_override or self.llm_config.get(
            "application", {}
        ).get("prompt_version", "enrich_job_v1")

    @property
    def application_schema_version(self) -> str:
        return self.application_schema_version_override or self.llm_config.get(
            "application", {}
        ).get("schema_version", "enrich_job_result_v1")

    @property
    def application_repair_retries(self) -> int:
        if self.application_repair_retries_override is not None:
            return self.application_repair_retries_override
        return int(self.llm_config.get("application", {}).get("repair_retries", 1))

    @property
    def application_fit_threshold(self) -> int:
        if self.application_fit_threshold_override is not None:
            return self.application_fit_threshold_override
        return int(self.llm_config.get("application", {}).get("fit_threshold", 60))

    @property
    def eval_judge_model(self) -> str:
        return self.eval_judge_model_override or self.llm_config.get(
            "evaluation", {}
        ).get("judge_model", "qwen3.7-max-2026-06-08")

    @property
    def eval_judge_temperature(self) -> float:
        if self.eval_judge_temperature_override is not None:
            return self.eval_judge_temperature_override
        return float(self.llm_config.get("evaluation", {}).get("temperature", 0))

    @property
    def eval_max_concurrency(self) -> int:
        if self.eval_max_concurrency_override is not None:
            return self.eval_max_concurrency_override
        return int(self.llm_config.get("evaluation", {}).get("max_concurrency", 1))

    @property
    def embedding_config(self) -> dict:
        return self.llm_config.get("embedding", {})

    @property
    def embedding_model(self) -> str:
        return self.embedding_config.get("model", "text-embedding-v4")

    @property
    def embedding_fallback_model(self) -> str:
        return self.embedding_config.get("fallback_model", "text-embedding-v3")

    @property
    def embedding_dimensions(self) -> int:
        return int(self.embedding_config.get("dimensions", 1024))

    @property
    def embedding_batch_size(self) -> int:
        return int(self.embedding_config.get("batch_size", 10))

    @property
    def rerank_config(self) -> dict:
        return self.llm_config.get("rerank", {})

    @property
    def rerank_model(self) -> str:
        return self.rerank_config.get("model", "qwen3-rerank")

    @property
    def rerank_top_n(self) -> int:
        return int(self.rerank_config.get("top_n", 20))

    @property
    def rerank_candidate_pool(self) -> int:
        return int(self.rerank_config.get("candidate_pool", 25))

    @property
    def rerank_instruct(self) -> str:
        return self.rerank_config.get(
            "instruct",
            "Given a job posting, retrieve relevant project evidence passages "
            "that demonstrate the candidate's fit for the role.",
        )

    @property
    def chunking_config(self) -> dict:
        return self.llm_config.get("chunking", {})

    @property
    def retrieval_config(self) -> dict:
        return self.llm_config.get("retrieval", {})

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
