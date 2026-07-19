"""Settings for the cloud Qwen ReAct browser agent."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.app.config import settings as app_settings


@dataclass
class BrowserAgentSettings:
    dashscope_api_key: str
    qwen_base_url: str
    qwen_model: str
    agent_max_steps: int = 40
    save_snapshots: bool = False
    snapshot_dir: Path = Path("data/browser_agent_snapshots")
    snapshot_max_chars: int = 12000

    @classmethod
    def from_app_settings(cls) -> BrowserAgentSettings:
        snapshot_dir = app_settings.data_dir / "browser_agent_snapshots"
        return cls(
            dashscope_api_key=app_settings.dashscope_api_key,
            qwen_base_url=app_settings.qwen_base_url,
            qwen_model=app_settings.qwen_model,
            agent_max_steps=app_settings.browser_agent_max_steps,
            save_snapshots=app_settings.browser_agent_save_snapshots,
            snapshot_dir=snapshot_dir,
            snapshot_max_chars=app_settings.browser_agent_snapshot_max_chars,
        )
