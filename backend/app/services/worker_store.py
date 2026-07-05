"""Worker device pairing and browser task queue persistence."""

import hashlib
import json
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Literal

from backend.app.config import settings
from backend.app.db import get_connection
from backend.app.models.browser import BrowserHealth, Platform
from backend.app.models.search_prefs import JobAgePreset, WorkMode, job_age_to_days

WorkerTaskStatus = Literal["pending", "claimed", "completed", "failed"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_worker_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_worker_token() -> str:
    return secrets.token_urlsafe(32)


def create_worker_device(user_id: int, *, label: str = "Search Helper") -> str:
    """Pair a Search Helper device and return the one-time plain token."""
    token = generate_worker_token()
    token_hash = hash_worker_token(token)
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO worker_devices (user_id, token_hash, label, browser_health, last_seen_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, token_hash, label, BrowserHealth.NOT_INSTALLED.value, _now_iso()),
        )
        conn.commit()
    return token


def revoke_worker_devices(user_id: int) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE worker_devices
            SET revoked_at = ?
            WHERE user_id = ? AND revoked_at IS NULL
            """,
            (_now_iso(), user_id),
        )
        conn.commit()
        return cursor.rowcount


def get_worker_device_by_token(token: str) -> dict[str, Any] | None:
    token_hash = hash_worker_token(token)
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM worker_devices
            WHERE token_hash = ? AND revoked_at IS NULL
            """,
            (token_hash,),
        ).fetchone()
    return dict(row) if row else None


def has_active_worker_device(user_id: int) -> bool:
    device = get_active_worker_device(user_id)
    return device is not None


def get_active_worker_device(user_id: int) -> dict[str, Any] | None:
    stale_before = _stale_cutoff_iso()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM worker_devices
            WHERE user_id = ?
              AND revoked_at IS NULL
              AND last_seen_at IS NOT NULL
              AND last_seen_at >= ?
            ORDER BY last_seen_at DESC
            LIMIT 1
            """,
            (user_id, stale_before),
        ).fetchone()
    return dict(row) if row else None


def update_worker_heartbeat(
    device_id: int,
    *,
    browser_health: BrowserHealth,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE worker_devices
            SET browser_health = ?, last_seen_at = ?
            WHERE id = ?
            """,
            (browser_health.value, _now_iso(), device_id),
        )
        conn.commit()


def _stale_cutoff_iso() -> str:
    cutoff = datetime.now(timezone.utc).timestamp() - settings.worker_heartbeat_stale_seconds
    return datetime.fromtimestamp(cutoff, tz=timezone.utc).isoformat()


def create_worker_task(
    *,
    task_id: str,
    user_id: int,
    run_id: int,
    payload: dict[str, Any],
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO worker_tasks (
                id, user_id, run_id, type, status, payload_json, created_at
            )
            VALUES (?, ?, ?, 'browser_search', 'pending', ?, ?)
            """,
            (task_id, user_id, run_id, json.dumps(payload), _now_iso()),
        )
        conn.commit()


def get_worker_task(task_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM worker_tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
    return dict(row) if row else None


def claim_next_worker_task(user_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM worker_tasks
            WHERE user_id = ? AND status = 'pending'
            ORDER BY created_at ASC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        if not row:
            return None

        task = dict(row)
        conn.execute(
            """
            UPDATE worker_tasks
            SET status = 'claimed', claimed_at = ?
            WHERE id = ? AND status = 'pending'
            """,
            (_now_iso(), task["id"]),
        )
        conn.commit()
        task["status"] = "claimed"
        task["claimed_at"] = _now_iso()
        return task


def complete_worker_task(
    task_id: str,
    *,
    user_id: int,
    listings: list[dict[str, Any]],
    warnings: list[str],
) -> bool:
    result_json = json.dumps({"listings": listings, "warnings": warnings})
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE worker_tasks
            SET status = 'completed',
                result_json = ?,
                warnings_json = ?,
                completed_at = ?
            WHERE id = ? AND user_id = ? AND status IN ('pending', 'claimed')
            """,
            (
                result_json,
                json.dumps(warnings),
                _now_iso(),
                task_id,
                user_id,
            ),
        )
        conn.commit()
        return cursor.rowcount > 0


def fail_worker_task(
    task_id: str,
    *,
    user_id: int,
    error: str,
    code: str,
) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE worker_tasks
            SET status = 'failed',
                error = ?,
                error_code = ?,
                completed_at = ?
            WHERE id = ? AND user_id = ? AND status IN ('pending', 'claimed')
            """,
            (error, code, _now_iso(), task_id, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def mark_worker_task_timed_out(task_id: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE worker_tasks
            SET status = 'failed',
                error = 'Search timed out waiting for Search Helper.',
                error_code = 'search_timeout',
                completed_at = ?
            WHERE id = ? AND status IN ('pending', 'claimed')
            """,
            (_now_iso(), task_id),
        )
        conn.commit()


def wait_for_worker_task_result(
    task_id: str,
    *,
    timeout_seconds: int | None = None,
    poll_interval_seconds: float = 1.0,
) -> dict[str, Any]:
    """Poll worker_tasks until completed, failed, or timeout."""
    timeout = timeout_seconds or settings.browser_search_wait_timeout_seconds
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        task = get_worker_task(task_id)
        if not task:
            return {
                "status": "failed",
                "error": f"Worker task {task_id} was not found.",
                "code": "search_task_missing",
            }

        if task["status"] == "completed":
            return {
                "status": "completed",
                "result": json.loads(task["result_json"] or "{}"),
                "warnings": json.loads(task["warnings_json"] or "[]"),
            }

        if task["status"] == "failed":
            return {
                "status": "failed",
                "error": task["error"] or "Worker task failed.",
                "code": task["error_code"] or "worker_task_failed",
            }

        time.sleep(poll_interval_seconds)

    mark_worker_task_timed_out(task_id)
    return {
        "status": "failed",
        "error": "Search timed out waiting for Search Helper.",
        "code": "search_timeout",
    }


def build_task_payload(
    *,
    task_id: str,
    run_id: int,
    role: str,
    platform: Platform,
    country: str,
    work_mode: WorkMode,
    max_listings: int,
    job_age: JobAgePreset,
    skills_summary: str,
) -> dict[str, Any]:
    return {
        "taskId": task_id,
        "runId": run_id,
        "role": role,
        "platform": platform,
        "country": country,
        "workMode": work_mode,
        "maxListings": max_listings,
        "jobAge": job_age,
        "maxJobAgeDays": job_age_to_days(job_age),
        "skillsSummary": skills_summary,
    }
