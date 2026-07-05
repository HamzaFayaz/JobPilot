"""Parent graph entry node — load run + profile snapshot."""

from backend.app.graph.state import ProfileState, ProjectState, RunState
from backend.app.models.browser import Platform
from backend.app.models.search_prefs import (
    DEFAULT_JOB_AGE,
    DEFAULT_MAX_LISTINGS,
    DEFAULT_WORK_MODE,
    JobAgePreset,
    WorkMode,
    clamp_max_listings,
)
from backend.app.services.profile_store import (
    get_cv_text,
    get_profile,
    get_stored_projects,
)
from backend.app.services.search_store import get_search_run, update_search_run


def _stored_project_to_state(project) -> ProjectState:
    return ProjectState(
        id=project.id,
        name=project.name,
        description=project.description,
        source=project.source,
        repo_full_name=project.repo_full_name,
        readme_md=project.readme_md,
        chars_per_line=None,
    )


def _validate_profile(user_id: int) -> tuple[ProfileState | None, str | None]:
    profile = get_profile(user_id)
    cv_text = get_cv_text(user_id)

    if not cv_text.strip():
        return None, "CV is required before starting a search."

    if len(profile.skills) < 3 or profile.skills_extraction_status != "ready":
        return None, "At least 3 extracted skills are required before starting a search."

    if not profile.projects:
        return None, "At least one project is required before starting a search."

    profile_state = ProfileState(
        cv_text=cv_text,
        skills=list(profile.skills),
        target_roles=list(profile.target_roles),
        projects=[_stored_project_to_state(p) for p in get_stored_projects(user_id)],
    )
    return profile_state, None


def _fail_run(run_id: int, message: str) -> dict:
    update_search_run(run_id, status="failed", error=message, finished=True)
    return {
        "status": "failed",
        "errors": [message],
    }


def init_run(state: RunState) -> dict:
    """Load search_runs row, hydrate ProfileState, set status=running."""
    run_id = state["run_id"]
    user_id = state["user_id"]

    run = get_search_run(run_id)
    if not run:
        return _fail_run(run_id, f"Search run {run_id} was not found.")

    if run["user_id"] != user_id:
        return _fail_run(run_id, "Search run does not belong to this user.")

    if run["status"] not in ("pending", "running"):
        return _fail_run(
            run_id,
            f"Search run {run_id} cannot start from status '{run['status']}'.",
        )

    profile_state, profile_error = _validate_profile(user_id)
    if profile_error:
        return _fail_run(run_id, profile_error)

    role = run["role"] or ""
    if not role:
        return _fail_run(run_id, "Search run is missing a target role.")

    platform: Platform = run["platform"] or "linkedin"
    country = (run.get("country") or "").strip()
    if not country:
        return _fail_run(run_id, "Search run is missing a target country.")

    work_mode: WorkMode = run.get("work_mode") or DEFAULT_WORK_MODE
    max_listings = clamp_max_listings(run.get("max_listings") or DEFAULT_MAX_LISTINGS)
    job_age: JobAgePreset = run.get("job_age") or DEFAULT_JOB_AGE

    update_search_run(run_id, status="running")

    return {
        "role": role,
        "platform": platform,
        "country": country,
        "work_mode": work_mode,
        "max_listings": max_listings,
        "job_age": job_age,
        "profile": profile_state,
        "listings": [],
        "matched_jobs": [],
        "errors": [],
        "status": "running",
    }
