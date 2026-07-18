"""Search run persistence helpers for graph execution."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from backend.app.db import get_connection
from backend.app.models.browser import RawJobListing
from backend.app.models.search import JobPackageStatus, RunStatus


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def package_key_for_job(job: dict[str, Any]) -> str:
    """Stable identity for one listing within a run (matches application package_out)."""
    identity = (
        f"{job.get('platform', '')}|{job.get('url', '')}".lower().strip()
        if job.get("url")
        else "|".join(
            str(job.get(key, "")).lower().strip()
            for key in ("title", "company", "description_text")
        )
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def user_has_active_search_run(user_id: int) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT 1
            FROM search_runs
            WHERE user_id = ? AND status IN ('pending', 'running')
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
    return row is not None


def seed_analyzing_packages(
    run_id: int,
    user_id: int,
    jobs: list[dict[str, Any]],
) -> int:
    """Insert analyzing rows as soon as matched jobs are known (UI can list them)."""
    count = 0
    for job in jobs:
        upsert_job_package(
            run_id=run_id,
            user_id=user_id,
            job=job,
            package_key=package_key_for_job(job),
            analysis={},
            status="analyzing",
            summary="",
            current_cv_score=None,
            suggested_cv_score=None,
            error=None,
        )
        count += 1
    return count


def set_job_package_decision(
    *,
    package_id: int,
    user_id: int,
    decision: JobPackageStatus,
) -> dict[str, Any] | None:
    """Mark a ready package as applied or skipped. Returns the updated row dict."""
    if decision not in {"applied", "skipped"}:
        raise ValueError("decision must be applied or skipped")
    now = _now_iso()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, status
            FROM job_packages
            WHERE id = ? AND user_id = ?
            """,
            (package_id, user_id),
        ).fetchone()
        if row is None:
            return None
        if row["status"] != "ready":
            return {"id": int(row["id"]), "status": row["status"], "ok": False}
        conn.execute(
            """
            UPDATE job_packages
            SET status = ?, updated_at = ?
            WHERE id = ? AND user_id = ? AND status = 'ready'
            """,
            (decision, now, package_id, user_id),
        )
        conn.commit()
        updated = conn.execute(
            "SELECT * FROM job_packages WHERE id = ? AND user_id = ?",
            (package_id, user_id),
        ).fetchone()
    return dict(updated) if updated else None


def get_search_run(run_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM search_runs WHERE id = ?",
            (run_id,),
        ).fetchone()
    return dict(row) if row else None


def user_run_number(user_id: int, run_id: int) -> int:
    """1-based sequence of this run among the user's own searches (for UI only)."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM search_runs
            WHERE user_id = ? AND id <= ?
            """,
            (user_id, run_id),
        ).fetchone()
    return int(row["n"] or 0)


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
                    description_text, display_description_text, summary, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    run_id,
                    listing.title,
                    listing.company,
                    listing.url,
                    listing.source_platform,
                    listing.description_text,
                    listing.display_description_text or "",
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
                display_description_text, summary, match_score, current_cv_score,
                suggested_cv_score, status, error, analysis_json, model_name,
                prompt_version, profile_snapshot_hash, package_key, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id, package_key)
            WHERE run_id IS NOT NULL AND package_key IS NOT NULL
            DO UPDATE SET
                title = excluded.title,
                company = excluded.company,
                url = excluded.url,
                platform = excluded.platform,
                description_text = excluded.description_text,
                display_description_text = CASE
                    WHEN excluded.display_description_text != ''
                        THEN excluded.display_description_text
                    ELSE job_packages.display_description_text
                END,
                summary = CASE
                    WHEN excluded.summary != '' THEN excluded.summary
                    ELSE job_packages.summary
                END,
                match_score = COALESCE(excluded.match_score, job_packages.match_score),
                current_cv_score = COALESCE(
                    excluded.current_cv_score, job_packages.current_cv_score
                ),
                suggested_cv_score = COALESCE(
                    excluded.suggested_cv_score, job_packages.suggested_cv_score
                ),
                status = CASE
                    WHEN job_packages.status IN ('applied', 'skipped')
                        THEN job_packages.status
                    ELSE excluded.status
                END,
                error = excluded.error,
                analysis_json = CASE
                    WHEN excluded.analysis_json IS NOT NULL
                        AND excluded.analysis_json != '{}'
                        THEN excluded.analysis_json
                    ELSE job_packages.analysis_json
                END,
                model_name = COALESCE(excluded.model_name, job_packages.model_name),
                prompt_version = COALESCE(
                    excluded.prompt_version, job_packages.prompt_version
                ),
                profile_snapshot_hash = COALESCE(
                    excluded.profile_snapshot_hash, job_packages.profile_snapshot_hash
                ),
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
                job.get("display_description_text") or "",
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
