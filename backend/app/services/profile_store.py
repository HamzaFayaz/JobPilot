"""Profile CRUD against SQLite."""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.app.db import get_connection
from backend.app.models.profile import ProfileResponse, ProfileUpdate, Project


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_json_list(raw: str | None) -> list:
    if not raw:
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


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


def _get_oauth_flags() -> dict[str, dict | None]:
    from backend.app.services.oauth_store import get_token

    return {
        "google": get_token("google"),
        "github": get_token("github"),
    }


def get_profile() -> ProfileResponse:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM profiles WHERE id = 1").fetchone()
    if not row:
        return ProfileResponse()
    return _row_to_profile(dict(row), _get_oauth_flags())


def update_profile(data: ProfileUpdate) -> ProfileResponse:
    fields: list[str] = []
    values: list[Any] = []

    if data.target_roles is not None:
        fields.append("target_roles = ?")
        values.append(json.dumps(data.target_roles))
    if data.projects is not None:
        fields.append("projects = ?")
        values.append(json.dumps([p.model_dump() for p in data.projects]))

    if not fields:
        return get_profile()

    fields.append("updated_at = ?")
    values.append(_now_iso())

    with get_connection() as conn:
        conn.execute(
            f"UPDATE profiles SET {', '.join(fields)} WHERE id = 1",
            values,
        )
        conn.commit()
    return get_profile()


def update_cv(
    filename: str,
    path: str,
    cv_text: str,
    skills: list[str],
    status: str,
) -> ProfileResponse:
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
            WHERE id = 1
            """,
            (filename, path, cv_text, json.dumps(skills), status, _now_iso()),
        )
        conn.commit()
    return get_profile()


def set_skills_extraction_status(status: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE profiles SET skills_extraction_status = ?, updated_at = ? WHERE id = 1",
            (status, _now_iso()),
        )
        conn.commit()


def get_cv_text() -> str:
    with get_connection() as conn:
        row = conn.execute("SELECT cv_text FROM profiles WHERE id = 1").fetchone()
    return (row["cv_text"] if row and row["cv_text"] else "") or ""


def merge_github_import(
    new_projects: list[dict],
    new_skills: list[str],
) -> ProfileResponse:
    profile = get_profile()
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
            UPDATE profiles SET projects = ?, skills = ?, updated_at = ? WHERE id = 1
            """,
            (json.dumps(existing_projects), json.dumps(merged_skills), _now_iso()),
        )
        conn.commit()
    return get_profile()
