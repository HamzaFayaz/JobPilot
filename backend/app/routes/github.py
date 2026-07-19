"""GitHub repo list and import routes — scoped to current user."""

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from backend.app.deps.auth import get_current_user
from backend.app.models.oauth import GitHubImportRequest, GitHubRepoItem
from backend.app.models.profile import README_MAX_CHARS, ProfileResponse
from backend.app.services import github_service, profile_llm
from backend.app.services.evidence_indexing import index_project_evidence
from backend.app.services.oauth_store import get_access_token
from backend.app.services.profile_store import (
    get_cv_text,
    get_profile,
    merge_github_import,
    set_projects_indexing_status,
)

router = APIRouter(prefix="/api/github", tags=["github"])

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=4)
MAX_PARALLEL = 4


def _import_one_repo(full_name: str, cv_summary: str, access_token: str) -> dict:
    readme = github_service.get_readme(full_name, access_token=access_token)
    readme_stored = readme[:README_MAX_CHARS] if readme else ""
    evidence = profile_llm.build_project_evidence(readme_stored, full_name, cv_summary)
    return {
        "id": str(uuid.uuid4()),
        "name": evidence["name"],
        "description": evidence["description"],
        "source": "github",
        "repo_full_name": full_name,
        "readme_md": readme_stored,
        "portfolio_overview": evidence["portfolio_overview"],
        "evidence_card": evidence["evidence_card"],
        "repo_skills": evidence.get("repo_skills", []),
    }


def _run_github_import_job(
    user_id: int,
    repos: list[str],
    access_token: str,
    cv_summary: str,
) -> None:
    """Background: overview + evidence + chunk/index, then reveal projects."""
    try:
        futures = {
            _executor.submit(_import_one_repo, full_name, cv_summary, access_token): full_name
            for full_name in repos
        }
        new_projects: list[dict] = []
        new_skills: list[str] = []
        for future in as_completed(futures):
            full_name = futures[future]
            try:
                item = future.result()
            except Exception as exc:
                logger.exception("GitHub import failed for %s: %s", full_name, exc)
                raise
            skills = item.pop("repo_skills", [])
            new_projects.append(item)
            new_skills.extend(skills)

        merge_github_import(user_id, new_projects, new_skills)
        for project in new_projects:
            try:
                index_project_evidence(user_id, project)
            except Exception as exc:
                logger.warning(
                    "Evidence indexing failed for %s: %s", project.get("id"), exc
                )
        set_projects_indexing_status(user_id, "ready")
        logger.info(
            "GitHub import ready for user %s (%d project(s))",
            user_id,
            len(new_projects),
        )
    except Exception:
        logger.exception("GitHub import background job failed for user %s", user_id)
        set_projects_indexing_status(user_id, "failed")


@router.get("/repos", response_model=list[GitHubRepoItem])
def list_github_repos(current_user: dict = Depends(get_current_user)) -> list[GitHubRepoItem]:
    token = get_access_token(current_user["id"], "github")
    if not token:
        raise HTTPException(status_code=401, detail="GitHub not connected")
    try:
        return github_service.list_repos(access_token=token)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/import", response_model=ProfileResponse)
async def import_github_repos(
    body: GitHubImportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
) -> ProfileResponse:
    user_id = current_user["id"]
    token = get_access_token(user_id, "github")
    if not token:
        raise HTTPException(status_code=401, detail="GitHub not connected")
    if not body.repos:
        raise HTTPException(status_code=400, detail="No repos selected")

    profile = get_profile(user_id)
    if profile.projects_indexing_status == "pending":
        raise HTTPException(
            status_code=409,
            detail="A GitHub import is already preparing your projects. Please wait.",
        )

    cv_summary = get_cv_text(user_id)[:2000]
    set_projects_indexing_status(user_id, "pending")
    background_tasks.add_task(
        _run_github_import_job,
        user_id,
        list(body.repos),
        token,
        cv_summary,
    )
    # Projects stay hidden until the background job merges them.
    return get_profile(user_id)
