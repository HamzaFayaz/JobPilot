"""Search run persistence helpers for graph execution."""

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
