"""Persist per-run search telemetry (steps, tokens, listings) for tuning."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

StopReason = Literal["completed_json", "exceeded_max_steps", "skipped"]


@dataclass
class LlmCallMetrics:
    step: int
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    input_chars: int = 0
    tools: list[str] = field(default_factory=list)


@dataclass
class PhaseMetrics:
    phase: str
    target: int
    max_steps: int
    steps_used: int
    stop_reason: StopReason
    listings_found: int
    session: str
    last_tool: str | None = None
    llm_calls: list[LlmCallMetrics] = field(default_factory=list)
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0

    def add_llm_call(self, call: LlmCallMetrics) -> None:
        self.llm_calls.append(call)
        self.total_prompt_tokens += call.prompt_tokens
        self.total_completion_tokens += call.completion_tokens
        self.total_tokens += call.total_tokens


@dataclass
class PhaseRunResult:
    raw_text: str
    metrics: PhaseMetrics


def save_run_summary(
    base_dir: Path,
    *,
    run_id: int,
    max_listings: int,
    role: str,
    platform: str,
    country: str,
    phases: list[PhaseMetrics],
    merged_listings: int,
    parallel: bool,
) -> Path | None:
    try:
        out_dir = base_dir / f"run-{run_id}"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "run-summary.json"
        payload: dict[str, Any] = {
            "runId": run_id,
            "role": role,
            "platform": platform,
            "country": country,
            "maxListings": max_listings,
            "parallelPhases": parallel,
            "mergedListings": merged_listings,
            "phases": [asdict(phase) for phase in phases],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Saved run telemetry: %s", path)
        return path
    except OSError as exc:
        logger.warning("Failed to save run telemetry: %s", exc)
        return None
