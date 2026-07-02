"""GitHub OAuth routes — requires authenticated user."""

from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from backend.app.config import settings
from backend.app.deps.auth import get_current_user
from backend.app.services.oauth_state import create_oauth_state, verify_oauth_state
from backend.app.services.oauth_store import delete_token, save_token

router = APIRouter(tags=["auth-github"])

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


@router.get("/auth/github")
def github_auth_start(current_user: dict = Depends(get_current_user)) -> RedirectResponse:
    if not settings.github_client_id:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
    state = create_oauth_state(current_user["id"])
    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_redirect_uri,
        "scope": "repo read:user",
        "state": state,
    }
    return RedirectResponse(f"{GITHUB_AUTH_URL}?{urlencode(params)}")


@router.get("/auth/github/callback")
def github_auth_callback(code: str, state: str) -> RedirectResponse:
    try:
        user_id = verify_oauth_state(state)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

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

    save_token(user_id, "github", access_token=access_token, email=login)
    return RedirectResponse(f"{settings.frontend_url}/profile?github=connected")


@router.delete("/api/auth/github")
def github_disconnect(current_user: dict = Depends(get_current_user)) -> dict[str, bool]:
    delete_token(current_user["id"], "github")
    return {"disconnected": True}
