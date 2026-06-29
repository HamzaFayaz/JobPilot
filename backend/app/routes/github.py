"""GitHub repo list and import routes."""

import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException

from backend.app.models.oauth import GitHubImportRequest, GitHubRepoItem
from backend.app.models.profile import ProfileResponse
from backend.app.services import github_service, profile_llm
from backend.app.services.profile_store import get_cv_text, merge_github_import
from backend.app.services.oauth_store import get_access_token

router = APIRouter(prefix="/api/github", tags=["github"])

_executor = ThreadPoolExecutor(max_workers=4)
MAX_PARALLEL = 4


def _import_one_repo(full_name: str, cv_summary: str) -> dict:
    readme = github_service.get_readme(full_name)
    summary = profile_llm.summarize_repo(readme, cv_summary)
    return {
        "id": str(uuid.uuid4()),
        "name": summary["name"],
        "description": summary["description"],
        "source": "github",
        "repo_skills": summary.get("repo_skills", []),
    }


@router.get("/repos", response_model=list[GitHubRepoItem])
def list_github_repos() -> list[GitHubRepoItem]:
    if not get_access_token("github"):
        raise HTTPException(status_code=401, detail="GitHub not connected")
    try:
        return github_service.list_repos()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/import", response_model=ProfileResponse)
async def import_github_repos(body: GitHubImportRequest) -> ProfileResponse:
    if not get_access_token("github"):
        raise HTTPException(status_code=401, detail="GitHub not connected")
    if not body.repos:
        raise HTTPException(status_code=400, detail="No repos selected")

    cv_summary = get_cv_text()[:2000]
    loop = asyncio.get_event_loop()

    async def run_import(full_name: str) -> dict:
        return await loop.run_in_executor(
            _executor, _import_one_repo, full_name, cv_summary
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

    return merge_github_import(new_projects, new_skills)
