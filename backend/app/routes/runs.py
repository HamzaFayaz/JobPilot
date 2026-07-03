"""Search run polling API routes."""

from fastapi import APIRouter, Depends, HTTPException

from backend.app.db import get_connection
from backend.app.deps.auth import get_current_user
from backend.app.models.search import SearchRunStatusResponse

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.get("/{run_id}/status", response_model=SearchRunStatusResponse)
def get_run_status(
    run_id: int,
    current_user: dict = Depends(get_current_user),
) -> SearchRunStatusResponse:
    # Connection 2: frontend polls backend for the current run status.
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, status, jobs_ready_count, error
            FROM search_runs
            WHERE id = ? AND user_id = ?
            """,
            (run_id, current_user["id"]),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Search run not found")

    return SearchRunStatusResponse(
        runId=int(row["id"]),
        status=row["status"],
        jobsReadyCount=int(row["jobs_ready_count"] or 0),
        error=row["error"],
    )
