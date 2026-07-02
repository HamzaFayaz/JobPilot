"""Profile CRUD against SQLite — scoped per user with encrypted cv_text."""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.app.db import get_connection
from backend.app.models.profile import ProfileResponse, ProfileUpdate, Project
from backend.app.services import crypto


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_json_list(raw: str | None) -> list:
    if not raw:
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


def _decrypt_cv_text(raw: str | None) -> str:
    if not raw:
        return ""
    try:
        return crypto.decrypt(raw)
    except ValueError:
        return raw


def _row_to_profile(row: dict, oauth: dict[str, dict | None]) -> ProfileResponse:
    google = oauth.get("google")
    github = oauth.get("github")
    cv_path = row.get("cv_path")
    cv_file_meta = None
    if cv_path and os.path.exists(cv_path):
        cv_file_meta = {"size": os.path.getsize(cv_path)}

    projects_raw = _parse_json_list(row.get("projects"))
    projects = [Project(**p) for p in projects_raw]

    return ProfileResponse(
        cv_filename=row.get("cv_filename"),
        cv_file_meta=cv_file_meta,
        skills=_parse_json_list(row.get("skills")),
        skills_extraction_status=row.get("skills_extraction_status") or "idle",
        target_roles=_parse_json_list(row.get("target_roles")),
        projects=projects,
        gmail_connected=google is not None,
        gmail_email=google.get("email") if google else None,
        github_connected=github is not None,
        github_username=github.get("email") if github else None,
        updated_at=row.get("updated_at"),
    )


def _get_oauth_flags(user_id: int) -> dict[str, dict | None]:
    from backend.app.services.oauth_store import get_token

    return {
        "google": get_token(user_id, "google"),
        "github": get_token(user_id, "github"),
    }


def get_profile(user_id: int) -> ProfileResponse:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
    if not row:
        return ProfileResponse()
    return _row_to_profile(dict(row), _get_oauth_flags(user_id))


def update_profile(user_id: int, data: ProfileUpdate) -> ProfileResponse:
    fields: list[str] = []
    values: list[Any] = []

    if data.target_roles is not None:
        fields.append("target_roles = ?")
        values.append(json.dumps(data.target_roles))
    if data.projects is not None:
        fields.append("projects = ?")
        values.append(json.dumps([p.model_dump() for p in data.projects]))

    if not fields:
        return get_profile(user_id)

    fields.append("updated_at = ?")
    values.append(_now_iso())
    values.append(user_id)

    with get_connection() as conn:
        conn.execute(
            f"UPDATE profiles SET {', '.join(fields)} WHERE user_id = ?",
            values,
        )
        conn.commit()
    return get_profile(user_id)


def update_cv(
    user_id: int,
    filename: str,
    path: str,
    cv_text: str,
    skills: list[str],
    status: str,
) -> ProfileResponse:
    encrypted_cv = crypto.encrypt(cv_text) if cv_text else None
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE profiles SET
                cv_filename = ?,
                cv_path = ?,
                cv_text = ?,
                skills = ?,
                skills_extraction_status = ?,
                updated_at = ?
            WHERE user_id = ?
            """,
            (filename, path, encrypted_cv, json.dumps(skills), status, _now_iso(), user_id),
        )
        conn.commit()
    return get_profile(user_id)


def set_skills_extraction_status(user_id: int, status: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE profiles SET skills_extraction_status = ?, updated_at = ? WHERE user_id = ?",
            (status, _now_iso(), user_id),
        )
        conn.commit()


def get_cv_text(user_id: int) -> str:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT cv_text FROM profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
    if not row or not row["cv_text"]:
        return ""
    return _decrypt_cv_text(row["cv_text"])


def merge_github_import(
    user_id: int,
    new_projects: list[dict],
    new_skills: list[str],
) -> ProfileResponse:
    profile = get_profile(user_id)
    existing_projects = [p.model_dump() for p in profile.projects]
    existing_skills = list(profile.skills)

    for proj in new_projects:
        proj.setdefault("id", str(uuid.uuid4()))
        proj.setdefault("source", "github")
        existing_projects.append(proj)

    merged_skills = list(dict.fromkeys(existing_skills + new_skills))

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE profiles SET projects = ?, skills = ?, updated_at = ? WHERE user_id = ?
            """,
            (json.dumps(existing_projects), json.dumps(merged_skills), _now_iso(), user_id),
        )
        conn.commit()
    return get_profile(user_id)
