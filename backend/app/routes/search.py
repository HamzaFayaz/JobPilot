"""Search start API route."""

from fastapi import APIRouter, Depends, HTTPException

from backend.app.db import get_connection
from backend.app.deps.auth import get_current_user
from backend.app.models.search import SearchStartResponse
from backend.app.services.profile_store import get_search_preferences

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("", response_model=SearchStartResponse)
def start_search(current_user: dict = Depends(get_current_user)) -> SearchStartResponse:
    # Connection 1: frontend asks backend to create a new search run.
    role, platform = get_search_preferences(current_user["id"])
    if not role:
        raise HTTPException(
            status_code=400,
            detail="No saved search role. Add a target role first.",
        )

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO search_runs (user_id, role, platform, status)
            VALUES (?, ?, ?, ?)
            """,
            (current_user["id"], role, platform, "pending"),
        )
        conn.commit()

    return SearchStartResponse(runId=int(cursor.lastrowid), status="pending")
