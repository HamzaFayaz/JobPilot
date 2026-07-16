"""Profile CRUD against SQLite — scoped per user with encrypted cv_text."""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, NamedTuple

from backend.app.db import get_connection
from backend.app.models.profile import ProfileResponse, ProfileUpdate, Project, StoredProject
from backend.app.models.search_prefs import (
    DEFAULT_JOB_AGE,
    DEFAULT_MAX_LISTINGS,
    DEFAULT_WORK_MODE,
    JobAgePreset,
    WorkMode,
    clamp_max_listings,
)
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


def _resolve_search_role(
    target_roles: list[str], search_role: str | None
) -> str | None:
    if search_role and search_role in target_roles:
        return search_role
    return target_roles[0] if target_roles else None


class SearchPreferences(NamedTuple):
    role: str | None
    platform: str
    country: str | None
    work_mode: WorkMode
    max_listings: int
    job_age: JobAgePreset


def _normalize_country(country: str | None) -> str | None:
    if not country:
        return None
    trimmed = country.strip()
    return trimmed or None


def _row_search_prefs(row: dict, target_roles: list[str]) -> SearchPreferences:
    return SearchPreferences(
        role=_resolve_search_role(target_roles, row.get("search_role")),
        platform=row.get("search_platform") or "linkedin",
        country=_normalize_country(row.get("search_country")),
        work_mode=row.get("search_work_mode") or DEFAULT_WORK_MODE,
        max_listings=clamp_max_listings(row.get("search_max_listings") or DEFAULT_MAX_LISTINGS),
        job_age=row.get("search_job_age") or DEFAULT_JOB_AGE,
    )


def _decrypt_cv_text(raw: str | None) -> str:
    if not raw:
        return ""
    try:
        return crypto.decrypt(raw)
    except ValueError:
        return raw


def _parse_stored_projects(raw: str | None) -> list[StoredProject]:
    projects: list[StoredProject] = []
    for item in _parse_json_list(raw):
        try:
            projects.append(StoredProject.model_validate(item))
        except Exception:
            continue
    return projects


def _stored_projects_to_api(projects: list[StoredProject]) -> list[Project]:
    return [p.to_api() for p in projects]


def _merge_project_update(existing: StoredProject | None, incoming: Project) -> dict:
    """Preserve server-only fields when the client updates a project."""
    merged = incoming.model_dump(by_alias=False)
    if existing:
        if existing.readme_md:
            merged["readme_md"] = existing.readme_md
        if existing.portfolio_overview:
            merged["portfolio_overview"] = existing.portfolio_overview
        if existing.evidence_card:
            merged["evidence_card"] = existing.evidence_card.model_dump(by_alias=False)
        if existing.repo_full_name and not merged.get("repo_full_name"):
            merged["repo_full_name"] = existing.repo_full_name
    return merged


def _row_to_profile(row: dict, oauth: dict[str, dict | None]) -> ProfileResponse:
    google = oauth.get("google")
    github = oauth.get("github")
    cv_path = row.get("cv_path")
    cv_file_meta = None
    if cv_path and os.path.exists(cv_path):
        cv_file_meta = {"size": os.path.getsize(cv_path)}

    stored_projects = _parse_stored_projects(row.get("projects"))
    target_roles = _parse_json_list(row.get("target_roles"))
    search_role = _resolve_search_role(target_roles, row.get("search_role"))

    return ProfileResponse(
        cv_filename=row.get("cv_filename"),
        cv_file_meta=cv_file_meta,
        skills=_parse_json_list(row.get("skills")),
        skills_extraction_status=row.get("skills_extraction_status") or "idle",
        target_roles=target_roles,
        search_role=search_role,
        search_platform=row.get("search_platform") or "linkedin",
        search_country=_normalize_country(row.get("search_country")),
        search_work_mode=row.get("search_work_mode") or DEFAULT_WORK_MODE,
        search_max_listings=clamp_max_listings(
            row.get("search_max_listings") or DEFAULT_MAX_LISTINGS
        ),
        search_job_age=row.get("search_job_age") or DEFAULT_JOB_AGE,
        projects=_stored_projects_to_api(stored_projects),
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


def get_search_preferences(user_id: int) -> SearchPreferences:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT target_roles, search_role, search_platform,
                   search_country, search_work_mode, search_max_listings, search_job_age
            FROM profiles
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
    if not row:
        return SearchPreferences(
            role=None,
            platform="linkedin",
            country=None,
            work_mode=DEFAULT_WORK_MODE,
            max_listings=DEFAULT_MAX_LISTINGS,
            job_age=DEFAULT_JOB_AGE,
        )
    target_roles = _parse_json_list(row["target_roles"])
    return _row_search_prefs(dict(row), target_roles)


def get_stored_projects(user_id: int) -> list[StoredProject]:
    """Load full project records including readme_md (server-side only)."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT projects FROM profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
    if not row:
        return []
    return _parse_stored_projects(row["projects"])


def get_project_readme(user_id: int, project_id: str) -> str | None:
    """Return stored README for one project, scoped to user_id."""
    for project in get_stored_projects(user_id):
        if project.id == project_id:
            return project.readme_md
    return None


def update_profile(user_id: int, data: ProfileUpdate) -> ProfileResponse:
    fields: list[str] = []
    values: list[Any] = []
    target_roles = get_profile(user_id).target_roles

    if data.target_roles is not None:
        target_roles = data.target_roles
        resolved_search_role = _resolve_search_role(target_roles, data.search_role)
        fields.append("target_roles = ?")
        values.append(json.dumps(target_roles))
        fields.append("search_role = ?")
        values.append(resolved_search_role)

    elif data.search_role is not None:
        fields.append("search_role = ?")
        values.append(_resolve_search_role(target_roles, data.search_role))

    if data.search_platform is not None:
        fields.append("search_platform = ?")
        values.append(data.search_platform)
    if data.search_country is not None:
        fields.append("search_country = ?")
        values.append(_normalize_country(data.search_country))
    if data.search_work_mode is not None:
        fields.append("search_work_mode = ?")
        values.append(data.search_work_mode)
    if data.search_max_listings is not None:
        fields.append("search_max_listings = ?")
        values.append(clamp_max_listings(data.search_max_listings))
    if data.search_job_age is not None:
        fields.append("search_job_age = ?")
        values.append(data.search_job_age)
    if data.projects is not None:
        existing_by_id = {p.id: p for p in get_stored_projects(user_id)}
        merged_projects = [
            _merge_project_update(existing_by_id.get(p.id), p) for p in data.projects
        ]
        fields.append("projects = ?")
        values.append(json.dumps(merged_projects))

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
    existing_projects = [p.model_dump(by_alias=False) for p in get_stored_projects(user_id)]
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
