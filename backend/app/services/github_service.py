"""GitHub API helpers via PyGithub."""

from github import Auth, Github

from backend.app.models.oauth import GitHubRepoItem
from backend.app.services.oauth_store import get_access_token


def _github_client() -> Github:
    token = get_access_token("github")
    if not token:
        raise RuntimeError("GitHub not connected")
    return Github(auth=Auth.Token(token))


def list_repos() -> list[GitHubRepoItem]:
    gh = _github_client()
    user = gh.get_user()
    repos = []
    for repo in user.get_repos(affiliation="owner"):
        repos.append(
            GitHubRepoItem(
                name=repo.name,
                full_name=repo.full_name,
                private=repo.private,
                fork=repo.fork,
                description=repo.description,
                default_branch=repo.default_branch or "main",
            )
        )
    return repos


def get_readme(full_name: str) -> str:
    gh = _github_client()
    repo = gh.get_repo(full_name)
    try:
        content = repo.get_readme()
        return content.decoded_content.decode("utf-8", errors="replace")
    except Exception:
        return ""
