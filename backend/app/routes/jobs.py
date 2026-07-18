"""Job package polling and decision API routes."""

import json

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.db import get_connection
from backend.app.deps.auth import get_current_user
from backend.app.models.search import JobDecisionRequest, JobPackageResponse
from backend.app.services.search_store import set_job_package_decision

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _row_to_package(row) -> JobPackageResponse:
    error_raw = row["error"]
    error_text: str | None = None
    if error_raw:
        try:
            parsed = json.loads(error_raw)
            if isinstance(parsed, dict):
                error_text = str(parsed.get("message") or parsed.get("code") or error_raw)
            else:
                error_text = str(parsed)
        except (json.JSONDecodeError, TypeError):
            error_text = str(error_raw)

    return JobPackageResponse(
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
        analysis=json.loads(row["analysis_json"] or "{}"),
        modelName=row["model_name"],
        promptVersion=row["prompt_version"],
        status=row["status"] or "ready",
        error=error_text,
        createdAt=row["created_at"],
        updatedAt=row["updated_at"],
    )


@router.get("", response_model=list[JobPackageResponse])
def list_jobs(
    run_id: int | None = Query(None, alias="runId"),
    current_user: dict = Depends(get_current_user),
) -> list[JobPackageResponse]:
    with get_connection() as conn:
        if run_id is not None:
            rows = conn.execute(
                """
                SELECT
                    id, run_id, title, company, url, platform, description_text,
                    summary, match_score, current_cv_score, suggested_cv_score,
                    cv_decision, swap_out_project, swap_in_text, draft_email,
                    analysis_json, model_name, prompt_version, status, error,
                    created_at, updated_at
                FROM job_packages
                WHERE run_id = ? AND user_id = ?
                ORDER BY created_at ASC, id ASC
                """,
                (run_id, current_user["id"]),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT
                    id, run_id, title, company, url, platform, description_text,
                    summary, match_score, current_cv_score, suggested_cv_score,
                    cv_decision, swap_out_project, swap_in_text, draft_email,
                    analysis_json, model_name, prompt_version, status, error,
                    created_at, updated_at
                FROM job_packages
                WHERE user_id = ?
                ORDER BY
                  CASE status
                    WHEN 'analyzing' THEN 0
                    WHEN 'ready' THEN 1
                    WHEN 'applied' THEN 2
                    WHEN 'skipped' THEN 3
                    ELSE 4
                  END,
                  updated_at DESC,
                  id DESC
                LIMIT 100
                """,
                (current_user["id"],),
            ).fetchall()

    return [_row_to_package(row) for row in rows]


@router.patch("/{job_id}/decision", response_model=JobPackageResponse)
def decide_job(
    job_id: int,
    body: JobDecisionRequest,
    current_user: dict = Depends(get_current_user),
) -> JobPackageResponse:
    result = set_job_package_decision(
        package_id=job_id,
        user_id=current_user["id"],
        decision=body.decision,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Job package not found.")
    if result.get("ok") is False:
        raise HTTPException(
            status_code=409,
            detail=f"Job must be ready before marking {body.decision} (current: {result.get('status')}).",
        )

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                id, run_id, title, company, url, platform, description_text,
                summary, match_score, current_cv_score, suggested_cv_score,
                cv_decision, swap_out_project, swap_in_text, draft_email,
                analysis_json, model_name, prompt_version, status, error,
                created_at, updated_at
            FROM job_packages
            WHERE id = ? AND user_id = ?
            """,
            (job_id, current_user["id"]),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Job package not found.")
    return _row_to_package(row)
