"""Search start API route."""

from fastapi import APIRouter, Depends, HTTPException

from backend.app.db import get_connection
from backend.app.deps.auth import get_current_user
from backend.app.models.search import SearchStartResponse
from backend.app.services.profile_store import get_search_preferences

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("", response_model=SearchStartResponse)
def start_search(current_user: dict = Depends(get_current_user)) -> SearchStartResponse:
    prefs = get_search_preferences(current_user["id"])
    if not prefs.role:
        raise HTTPException(
            status_code=400,
            detail="No saved search role. Add a target role first.",
        )
    if not prefs.country:
        raise HTTPException(
            status_code=400,
            detail="No saved search country. Set a country in search preferences first.",
        )

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO search_runs (
                user_id, role, platform, country, work_mode, max_listings, job_age, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                current_user["id"],
                prefs.role,
                prefs.platform,
                prefs.country,
                prefs.work_mode,
                prefs.max_listings,
                prefs.job_age,
                "pending",
            ),
        )
        conn.commit()

    return SearchStartResponse(runId=int(cursor.lastrowid), status="pending")
