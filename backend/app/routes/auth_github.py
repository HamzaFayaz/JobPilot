"""GitHub OAuth routes."""

from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from backend.app.config import settings
from backend.app.services.oauth_store import delete_token, save_token

router = APIRouter(tags=["auth-github"])

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


@router.get("/auth/github")
def github_auth_start() -> RedirectResponse:
    if not settings.github_client_id:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_redirect_uri,
        "scope": "repo read:user",
    }
    return RedirectResponse(f"{GITHUB_AUTH_URL}?{urlencode(params)}")


@router.get("/auth/github/callback")
def github_auth_callback(code: str) -> RedirectResponse:
    resp = httpx.post(
        GITHUB_TOKEN_URL,
        headers={"Accept": "application/json"},
        data={
            "client_id": settings.github_client_id,
            "client_secret": settings.github_client_secret,
            "code": code,
            "redirect_uri": settings.github_redirect_uri,
        },
        timeout=15,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="GitHub token exchange failed")

    data = resp.json()
    access_token = data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token from GitHub")

    user_resp = httpx.get(
        GITHUB_USER_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        },
        timeout=15,
    )
    login = None
    if user_resp.status_code == 200:
        login = user_resp.json().get("login")

    save_token("github", access_token=access_token, email=login)
    return RedirectResponse(f"{settings.frontend_url}/profile?github=connected")


@router.delete("/api/auth/github")
def github_disconnect() -> dict[str, bool]:
    delete_token("github")
    return {"disconnected": True}
