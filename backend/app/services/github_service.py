"""GitHub API helpers via PyGithub."""

from github import Auth, Github

from backend.app.models.oauth import GitHubRepoItem


def _github_client(access_token: str) -> Github:
    return Github(auth=Auth.Token(access_token))


def list_repos(access_token: str) -> list[GitHubRepoItem]:
    gh = _github_client(access_token)
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


def get_readme(full_name: str, access_token: str) -> str:
    gh = _github_client(access_token)
    repo = gh.get_repo(full_name)
    try:
        content = repo.get_readme()
        return content.decoded_content.decode("utf-8", errors="replace")
    except Exception:
        return ""
