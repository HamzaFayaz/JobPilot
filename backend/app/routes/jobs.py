"""Job package polling API routes."""

from fastapi import APIRouter, Depends, Query

from backend.app.db import get_connection
from backend.app.deps.auth import get_current_user
from backend.app.models.search import JobPackageResponse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=list[JobPackageResponse])
def list_jobs(
    run_id: int = Query(..., alias="runId"),
    current_user: dict = Depends(get_current_user),
) -> list[JobPackageResponse]:
    # Connection 3: frontend fetches the current job packages for one run.
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                run_id,
                title,
                company,
                url,
                platform,
                description_text,
                summary,
                match_score,
                current_cv_score,
                suggested_cv_score,
                cv_decision,
                swap_out_project,
                swap_in_text,
                draft_email,
                status,
                error,
                created_at,
                updated_at
            FROM job_packages
            WHERE run_id = ? AND user_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (run_id, current_user["id"]),
        ).fetchall()

    return [
        JobPackageResponse(
            id=int(row["id"]),
            runId=row["run_id"],
            title=row["title"] or "",
            company=row["company"] or "",
            url=row["url"] or "",
            platform=row["platform"] or "linkedin",
            descriptionText=row["description_text"] or "",
            summary=row["summary"] or "",
            matchScore=row["match_score"],
            currentCvScore=row["current_cv_score"],
            suggestedCvScore=row["suggested_cv_score"],
            cvDecision=row["cv_decision"],
            swapOutProject=row["swap_out_project"],
            swapInText=row["swap_in_text"],
            draftEmail=row["draft_email"] or "",
            status=row["status"] or "ready",
            error=row["error"],
            createdAt=row["created_at"],
            updatedAt=row["updated_at"],
        )
        for row in rows
    ]
