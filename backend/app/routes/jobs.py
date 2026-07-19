"""Job package polling, decision, and suggested-CV API routes."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from backend.app.db import get_connection
from backend.app.deps.auth import get_current_user
from backend.app.models.search import (
    JobDecisionRequest,
    JobPackageResponse,
    SuggestedCvGenerateRequest,
    SuggestedCvGenerateResponse,
)
from backend.app.services.search_store import set_job_package_decision
from backend.app.services.suggested_cv_service import generate_suggested_cv
from backend.app.services.suggested_cv_store import (
    delete_drafts_for_package,
    get_draft,
    get_latest_draft_for_package,
)
from backend.app.services.tailor_cv_llm import TailorCvError

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

    raw_description = row["description_text"] or ""
    try:
        display = row["display_description_text"] or ""
    except (KeyError, IndexError):
        display = ""
    # Frontend shows formatted display text when present; analysis used raw in DB.
    ui_description = display.strip() or raw_description

    return JobPackageResponse(
        id=int(row["id"]),
        runId=row["run_id"],
        title=row["title"] or "",
        company=row["company"] or "",
        url=row["url"] or "",
        platform=row["platform"] or "linkedin",
        descriptionText=ui_description,
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
                    display_description_text,
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
                    display_description_text,
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

    # Applied: keep suggested CV drafts. Skipped: remove them.
    if body.decision == "skipped":
        delete_drafts_for_package(current_user["id"], job_id)

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                id, run_id, title, company, url, platform, description_text,
                display_description_text,
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


@router.post(
    "/{job_id}/suggested-cv",
    response_model=SuggestedCvGenerateResponse,
)
def create_suggested_cv(
    job_id: int,
    body: SuggestedCvGenerateRequest,
    current_user: dict = Depends(get_current_user),
) -> SuggestedCvGenerateResponse:
    try:
        result = generate_suggested_cv(
            user_id=current_user["id"],
            package_id=job_id,
            approved_slot_indexes=list(body.approved_slot_indexes),
        )
    except TailorCvError as exc:
        status = 404 if exc.code in {"not_found", "missing_cv"} else 400
        if exc.code == "model_unavailable":
            status = 503
        raise HTTPException(status_code=status, detail=exc.message) from exc
    return SuggestedCvGenerateResponse(
        draftId=result["draftId"],
        filename=result["filename"],
        autoShortened=result["autoShortened"],
        approvedSlotIndexes=result["approvedSlotIndexes"],
        downloadPath=result["downloadPath"],
    )


@router.get("/{job_id}/suggested-cv/latest", response_model=SuggestedCvGenerateResponse)
def latest_suggested_cv(
    job_id: int,
    current_user: dict = Depends(get_current_user),
) -> SuggestedCvGenerateResponse:
    """Return the latest kept draft for this job (ready/applied). Missing after skip."""
    draft = get_latest_draft_for_package(current_user["id"], job_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="No suggested CV for this job.")
    path = Path(str(draft["path"]))
    if not path.exists():
        raise HTTPException(status_code=404, detail="Suggested CV file missing.")
    return SuggestedCvGenerateResponse(
        draftId=int(draft["id"]),
        filename=str(draft["filename"]),
        autoShortened=bool(draft["auto_shortened"]),
        approvedSlotIndexes=list(draft["approved_slot_indexes"] or []),
        downloadPath=f"/api/jobs/{job_id}/suggested-cv/{draft['id']}/download",
    )


@router.get("/{job_id}/suggested-cv/{draft_id}/download")
def download_suggested_cv(
    job_id: int,
    draft_id: int,
    current_user: dict = Depends(get_current_user),
) -> FileResponse:
    draft = get_draft(current_user["id"], draft_id)
    if draft is None or int(draft["package_id"]) != int(job_id):
        raise HTTPException(status_code=404, detail="Suggested CV draft not found.")
    path = Path(str(draft["path"]))
    if not path.exists():
        raise HTTPException(status_code=404, detail="Suggested CV file missing.")
    return FileResponse(
        path,
        media_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        filename=str(draft["filename"]),
    )
