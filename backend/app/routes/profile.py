"""Profile API routes — authenticated per user."""

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from backend.app.config import settings
from backend.app.deps.auth import get_current_user
from backend.app.models.profile import ProfileResponse, ProfileUpdate
from backend.app.services import cv_parser, profile_llm
from backend.app.services.profile_store import (
    get_profile,
    set_skills_extraction_status,
    update_cv,
    update_profile,
)

router = APIRouter(prefix="/api/profile", tags=["profile"])

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@router.get("", response_model=ProfileResponse)
def read_profile(current_user: dict = Depends(get_current_user)) -> ProfileResponse:
    return get_profile(current_user["id"])


@router.put("", response_model=ProfileResponse)
def put_profile(
    body: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
) -> ProfileResponse:
    return update_profile(current_user["id"], body)


@router.post("/cv", response_model=ProfileResponse)
async def upload_cv(
    cv: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
) -> ProfileResponse:
    user_id = current_user["id"]
    filename = cv.filename or "cv.docx"
    if not filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported")

    content_type = cv.content_type or ""
    if content_type and content_type not in (DOCX_MIME, "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported")

    upload_dir = settings.user_uploads_dir(user_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest_name = f"{uuid.uuid4().hex}_{filename}"
    dest_path: Path = upload_dir / dest_name

    set_skills_extraction_status(user_id, "pending")

    try:
        with dest_path.open("wb") as f:
            shutil.copyfileobj(cv.file, f)

        cv_text = cv_parser.extract_text_from_docx(dest_path)
        skills = profile_llm.extract_skills(cv_text)
        status = "ready" if len(skills) >= 1 else "failed"
        return update_cv(user_id, filename, str(dest_path), cv_text, skills, status)
    except Exception:
        set_skills_extraction_status(user_id, "failed")
        if dest_path.exists():
            dest_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="CV parsing or skill extraction failed")
