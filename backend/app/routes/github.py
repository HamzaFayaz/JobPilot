"""GitHub repo list and import routes — scoped to current user."""

import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, HTTPException

from backend.app.deps.auth import get_current_user
from backend.app.models.oauth import GitHubImportRequest, GitHubRepoItem
from backend.app.models.profile import README_MAX_CHARS, ProfileResponse
from backend.app.services import github_service, profile_llm
from backend.app.services.oauth_store import get_access_token
from backend.app.services.profile_store import get_cv_text, merge_github_import

router = APIRouter(prefix="/api/github", tags=["github"])

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
    current_user: dict = Depends(get_current_user),
) -> ProfileResponse:
    user_id = current_user["id"]
    token = get_access_token(user_id, "github")
    if not token:
        raise HTTPException(status_code=401, detail="GitHub not connected")
    if not body.repos:
        raise HTTPException(status_code=400, detail="No repos selected")

    cv_summary = get_cv_text(user_id)[:2000]
    loop = asyncio.get_event_loop()

    async def run_import(full_name: str) -> dict:
        return await loop.run_in_executor(
            _executor, _import_one_repo, full_name, cv_summary, token
        )

    sem = asyncio.Semaphore(MAX_PARALLEL)

    async def bounded(full_name: str) -> dict:
        async with sem:
            return await run_import(full_name)

    results = await asyncio.gather(*[bounded(r) for r in body.repos])

    new_projects = []
    new_skills: list[str] = []
    for item in results:
        skills = item.pop("repo_skills", [])
        new_projects.append(item)
        new_skills.extend(skills)

    return merge_github_import(user_id, new_projects, new_skills)
