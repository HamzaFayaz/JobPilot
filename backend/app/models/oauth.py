"""OAuth token schemas."""

from pydantic import BaseModel, Field


class OAuthToken(BaseModel):
    provider: str
    email: str | None = None
    access_token: str
    refresh_token: str | None = None
    expires_at: str | None = None


class GitHubRepoItem(BaseModel):
    name: str
    full_name: str
    private: bool
    fork: bool
    description: str | None = None
    default_branch: str = "main"


class GitHubImportRequest(BaseModel):
    repos: list[str]
