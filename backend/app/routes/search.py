"""Search start API route."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from backend.app.db import get_connection
from backend.app.deps.auth import get_current_user
from backend.app.graph.runner import run_parent_graph
from backend.app.models.search import SearchStartResponse
from backend.app.services.profile_store import get_profile, get_search_preferences
from backend.app.services.search_store import user_has_active_search_run, user_run_number
from backend.app.services.worker_store import has_active_worker_device

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("", response_model=SearchStartResponse)
def start_search(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
) -> SearchStartResponse:
    if not has_active_worker_device(current_user["id"]):
        raise HTTPException(
            status_code=400,
            detail="Search Helper is not connected. Pair your computer on the Search page first.",
        )

    if user_has_active_search_run(current_user["id"]):
        raise HTTPException(
            status_code=409,
            detail="A search is already in progress. Open Applications to follow job analysis.",
        )

    profile = get_profile(current_user["id"])
    if profile.projects_indexing_status == "pending":
        raise HTTPException(
            status_code=409,
            detail="Your projects are still being prepared. Please wait a few minutes.",
        )

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

    run_id = int(cursor.lastrowid)
    background_tasks.add_task(run_parent_graph, run_id, current_user["id"])

    return SearchStartResponse(
        runId=run_id,
        runNumber=user_run_number(current_user["id"], run_id),
        status="pending",
    )
