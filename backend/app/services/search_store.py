"""Search run persistence helpers for graph execution."""

import json
from datetime import datetime, timezone
from typing import Any

from backend.app.db import get_connection
from backend.app.models.browser import RawJobListing
from backend.app.models.search import RunStatus


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_search_run(run_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM search_runs WHERE id = ?",
            (run_id,),
        ).fetchone()
    return dict(row) if row else None


def get_latest_search_run(user_id: int) -> dict[str, Any] | None:
    """Most recent run for the user; in-progress runs take priority over finished ones."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, status, jobs_ready_count, error
            FROM search_runs
            WHERE user_id = ?
            ORDER BY
              CASE WHEN status IN ('pending', 'running') THEN 0 ELSE 1 END,
              id DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def update_search_run(
    run_id: int,
    *,
    status: RunStatus,
    error: str | None = None,
    finished: bool = False,
    jobs_ready_count: int | None = None,
) -> None:
    fields = ["status = ?", "updated_at = ?"]
    values: list[Any] = [status, _now_iso()]

    if error is not None:
        fields.append("error = ?")
        values.append(error)

    if finished:
        fields.append("finished_at = ?")
        values.append(_now_iso())

    if jobs_ready_count is not None:
        fields.append("jobs_ready_count = ?")
        values.append(jobs_ready_count)

    values.append(run_id)

    with get_connection() as conn:
        conn.execute(
            f"UPDATE search_runs SET {', '.join(fields)} WHERE id = ?",
            values,
        )
        conn.commit()


def save_raw_listings_as_packages(
    run_id: int,
    user_id: int,
    listings: list[RawJobListing],
) -> int:
    """Persist browser listings as minimal job packages for the current test slice."""
    with get_connection() as conn:
        for listing in listings:
            conn.execute(
                """
                INSERT INTO job_packages (
                    user_id, run_id, title, company, url, platform,
                    description_text, summary, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    run_id,
                    listing.title,
                    listing.company,
                    listing.url,
                    listing.source_platform,
                    listing.description_text,
                    "",
                    "ready",
                ),
            )

        count = len(listings)
        conn.execute(
            """
            UPDATE search_runs
            SET jobs_ready_count = ?, status = ?, finished_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (count, "completed", _now_iso(), _now_iso(), run_id),
        )
        conn.commit()

    return count


def upsert_job_package(
    *,
    run_id: int,
    user_id: int,
    job: dict[str, Any],
    package_key: str,
    analysis: dict[str, Any],
    status: str,
    summary: str = "",
    current_cv_score: int | None = None,
    suggested_cv_score: int | None = None,
    error: dict[str, Any] | None = None,
    model_name: str | None = None,
    prompt_version: str | None = None,
    profile_snapshot_hash: str | None = None,
) -> int:
    """Atomically insert or update the canonical package for one run/job."""
    now = _now_iso()
    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO job_packages (
                user_id, run_id, title, company, url, platform, description_text,
                summary, match_score, current_cv_score, suggested_cv_score,
                status, error, analysis_json, model_name, prompt_version,
                profile_snapshot_hash, package_key, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id, package_key)
            WHERE run_id IS NOT NULL AND package_key IS NOT NULL
            DO UPDATE SET
                title = excluded.title,
                company = excluded.company,
                url = excluded.url,
                platform = excluded.platform,
                description_text = excluded.description_text,
                summary = excluded.summary,
                match_score = excluded.match_score,
                current_cv_score = excluded.current_cv_score,
                suggested_cv_score = excluded.suggested_cv_score,
                status = excluded.status,
                error = excluded.error,
                analysis_json = excluded.analysis_json,
                model_name = excluded.model_name,
                prompt_version = excluded.prompt_version,
                profile_snapshot_hash = excluded.profile_snapshot_hash,
                updated_at = excluded.updated_at
            RETURNING id
            """,
            (
                user_id,
                run_id,
                job.get("title"),
                job.get("company"),
                job.get("url"),
                job.get("source_platform") or job.get("platform"),
                job.get("description_text") or "",
                summary,
                current_cv_score,
                current_cv_score,
                suggested_cv_score,
                status,
                json.dumps(error, ensure_ascii=False) if error else None,
                json.dumps(analysis, ensure_ascii=False, sort_keys=True),
                model_name,
                prompt_version,
                profile_snapshot_hash,
                package_key,
                now,
            ),
        ).fetchone()
        conn.commit()
    return int(row["id"])


def finalize_search_run(run_id: int) -> int:
    """Count ready packages and complete a run exactly once."""
    now = _now_iso()
    with get_connection() as conn:
        count_row = conn.execute(
            "SELECT COUNT(*) AS n FROM job_packages WHERE run_id = ? AND status = 'ready'",
            (run_id,),
        ).fetchone()
        ready_count = int(count_row["n"])
        conn.execute(
            """
            UPDATE search_runs
            SET jobs_ready_count = ?, status = 'completed',
                finished_at = COALESCE(finished_at, ?), updated_at = ?
            WHERE id = ? AND status IN ('pending', 'running')
            """,
            (ready_count, now, now, run_id),
        )
        conn.commit()
    return ready_count
