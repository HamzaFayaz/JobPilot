"""Search run persistence helpers for graph execution."""

from datetime import datetime, timezone
from typing import Any

from backend.app.db import get_connection
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
) -> None:
    fields = ["status = ?", "updated_at = ?"]
    values: list[Any] = [status, _now_iso()]

    if error is not None:
        fields.append("error = ?")
        values.append(error)

    if finished:
        fields.append("finished_at = ?")
        values.append(_now_iso())

    values.append(run_id)

    with get_connection() as conn:
        conn.execute(
            f"UPDATE search_runs SET {', '.join(fields)} WHERE id = ?",
            values,
        )
        conn.commit()
