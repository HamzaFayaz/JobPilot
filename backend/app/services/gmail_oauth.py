"""Google OAuth helpers for Gmail connect."""

from datetime import datetime, timezone

import httpx
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

from backend.app.config import settings
from backend.app.services.oauth_store import get_token, save_token

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]


def _client_config() -> dict:
    return {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_redirect_uri],
        }
    }


def create_flow() -> Flow:
    return Flow.from_client_config(
        _client_config(),
        scopes=SCOPES,
        redirect_uri=settings.google_redirect_uri,
    )


def exchange_code(code: str) -> tuple[str, str | None, str | None]:
    flow = create_flow()
    flow.fetch_token(code=code)
    creds: Credentials = flow.credentials
    email = _fetch_google_email(creds.token)
    expires_at = None
    if creds.expiry:
        expires_at = creds.expiry.replace(tzinfo=timezone.utc).isoformat()
    save_token(
        "google",
        access_token=creds.token,
        refresh_token=creds.refresh_token,
        email=email,
        expires_at=expires_at,
    )
    return creds.token, creds.refresh_token, email


def _fetch_google_email(access_token: str) -> str | None:
    resp = httpx.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    if resp.status_code == 200:
        return resp.json().get("email")
    return None


def get_valid_access_token() -> str | None:
    token_row = get_token("google")
    if not token_row:
        return None
    return token_row["access_token"]
