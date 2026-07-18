"""Persist Search Helper settings beside the exe (%LOCALAPPDATA%\\JobPilot\\SearchHelper\\.env)."""

from __future__ import annotations

import os
from pathlib import Path

from worker.runtime_paths import worker_data_dir

DEFAULT_API_BASE = "http://43.98.197.132"
DEFAULT_MODEL = "qwen-plus"

_ENV_PATH = worker_data_dir() / ".env"

_KEYS = (
    ("jobpilot_api_base", "JOBPILOT_API_BASE"),
    ("worker_token", "WORKER_TOKEN"),
    ("dashscope_api_key", "DASHSCOPE_API_KEY"),
    ("qwen_model", "QWEN_MODEL"),
    ("qwen_base_url", "QWEN_BASE_URL"),
    ("browser_provider", "BROWSER_PROVIDER"),
    ("webbridge_url", "WEBBRIDGE_URL"),
    ("agent_mode", "AGENT_MODE"),
)


def env_path() -> Path:
    return _ENV_PATH


def normalize_api_base(url: str) -> str:
    """Strip whitespace and trailing slash; keep scheme + host (+ optional port)."""
    value = url.strip().rstrip("/")
    return value


def api_base_looks_valid(url: str) -> bool:
    value = normalize_api_base(url).lower()
    return value.startswith("http://") or value.startswith("https://")


def load_config() -> dict[str, str]:
    values = {
        "jobpilot_api_base": DEFAULT_API_BASE,
        "worker_token": "",
        "dashscope_api_key": "",
        "qwen_model": DEFAULT_MODEL,
        "qwen_base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        "browser_provider": "webbridge",
        "webbridge_url": "http://127.0.0.1:10086",
        "agent_mode": "cloud",
    }
    if not _ENV_PATH.is_file():
        return values
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, raw = line.partition("=")
        key = key.strip().lower()
        val = raw.strip()
        for field, env_name in _KEYS:
            if key == env_name.lower():
                values[field] = val
    values["jobpilot_api_base"] = (
        normalize_api_base(values.get("jobpilot_api_base", "") or DEFAULT_API_BASE)
        or DEFAULT_API_BASE
    )
    return values


def save_config(
    *,
    jobpilot_api_base: str,
    worker_token: str,
    dashscope_api_key: str = "",
    qwen_model: str = DEFAULT_MODEL,
    qwen_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    browser_provider: str = "webbridge",
    webbridge_url: str = "http://127.0.0.1:10086",
    agent_mode: str = "cloud",
) -> None:
    api_base = normalize_api_base(jobpilot_api_base) or DEFAULT_API_BASE
    mode = (agent_mode or "cloud").strip().lower()
    if mode not in ("local", "cloud"):
        mode = "cloud"
    lines = [
        f"JOBPILOT_API_BASE={api_base}",
        f"WORKER_TOKEN={worker_token.strip()}",
        f"DASHSCOPE_API_KEY={dashscope_api_key.strip()}",
        f"QWEN_BASE_URL={qwen_base_url.strip()}",
        f"QWEN_MODEL={qwen_model.strip() or DEFAULT_MODEL}",
        f"BROWSER_PROVIDER={browser_provider.strip()}",
        f"WEBBRIDGE_URL={webbridge_url.strip()}",
        f"AGENT_MODE={mode}",
        "POLL_INTERVAL_SECONDS=3",
        "AGENT_MAX_STEPS=40",
    ]
    _ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    _ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def apply_config_to_environ(cfg: dict[str, str]) -> None:
    for field, env_name in _KEYS:
        value = cfg.get(field, "").strip()
        if field == "jobpilot_api_base":
            value = normalize_api_base(value)
        if value:
            os.environ[env_name] = value
    os.environ["JOBPILOT_WORKER_DATA_DIR"] = str(worker_data_dir())
