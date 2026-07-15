"""Persist raw WebBridge tool results for offline snapshot analysis."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def save_tool_result(
    base_dir: Path,
    *,
    run_id: int,
    phase: str,
    step: int,
    tool_name: str,
    args: dict[str, Any],
    result: Any,
    compressed_result: Any | None = None,
) -> Path | None:
    """Write tool output under run-{id}/{phase}/full/ and optional compressed/."""
    try:
        full_dir = base_dir / f"run-{run_id}" / phase / "full"
        full_dir.mkdir(parents=True, exist_ok=True)
        path = full_dir / f"step-{step:02d}-{tool_name}.json"
        payload = {
            "runId": run_id,
            "phase": phase,
            "step": step,
            "tool": tool_name,
            "args": args,
            "result": result,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Saved snapshot debug file: %s", path)

        if tool_name == "snapshot" and compressed_result is not None:
            compressed_dir = base_dir / f"run-{run_id}" / phase / "compressed"
            compressed_dir.mkdir(parents=True, exist_ok=True)
            compressed_path = compressed_dir / f"step-{step:02d}-snapshot.json"
            compressed_payload = {
                "runId": run_id,
                "phase": phase,
                "step": step,
                "tool": "snapshot",
                "compressed": compressed_result,
            }
            compressed_path.write_text(
                json.dumps(compressed_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.info("Saved compressed snapshot debug file: %s", compressed_path)

        return path
    except OSError as exc:
        logger.warning("Failed to save snapshot debug file: %s", exc)
        return None


def save_job_enrich_result(
    base_dir: Path,
    *,
    run_id: int,
    job_id: str,
    tool_name: str,
    args: dict[str, Any],
    result: Any,
    compressed_result: Any | None = None,
) -> Path | None:
    """Persist worker-owned job view page captures under jobs/enrich/job-{id}/."""
    try:
        job_dir = base_dir / f"run-{run_id}" / "jobs" / "enrich" / f"job-{job_id}"
        job_dir.mkdir(parents=True, exist_ok=True)
        path = job_dir / f"{tool_name}.json"
        payload: dict[str, Any] = {
            "runId": run_id,
            "jobId": job_id,
            "tool": tool_name,
            "args": args,
            "result": result,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Saved job enrich debug file: %s", path)

        if tool_name == "snapshot" and compressed_result is not None:
            compressed_path = job_dir / "snapshot-compressed.json"
            compressed_path.write_text(
                json.dumps(
                    {
                        "runId": run_id,
                        "jobId": job_id,
                        "compressed": compressed_result,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            logger.info("Saved job enrich compressed file: %s", compressed_path)

        return path
    except OSError as exc:
        logger.warning("Failed to save job enrich debug file: %s", exc)
        return None
