"""Google OAuth helpers for Gmail connect — per-user token storage."""

import logging
import os
from datetime import datetime, timezone
from threading import Lock
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
from google_auth_oauthlib.flow import Flow

from backend.app.config import settings
from backend.app.services.oauth_store import get_token, save_token

logger = logging.getLogger(__name__)

os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
]

_sessions: dict[str, tuple[Flow, int]] = {}
_sessions_lock = Lock()


def _client_config() -> dict:
    return {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": GOOGLE_AUTH_URL,
            "token_uri": GOOGLE_TOKEN_URL,
            "redirect_uris": [settings.google_redirect_uri],
        }
    }


def _create_flow() -> Flow:
    return Flow.from_client_config(
        _client_config(),
        scopes=SCOPES,
        redirect_uri=settings.google_redirect_uri,
    )


def begin_auth(user_id: int) -> str:
    """Start OAuth; store Flow + user_id by state so callback can save per-user token."""
    flow = _create_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent select_account",
        include_granted_scopes="false",
    )
    with _sessions_lock:
        _sessions[state] = (flow, user_id)
        if len(_sessions) > 20:
            for key in list(_sessions.keys())[:-10]:
                _sessions.pop(key, None)
    logger.info("Google OAuth started for user %s (state=%s…)", user_id, state[:8])
    return auth_url


def _exchange_with_httpx(code: str) -> dict:
    resp = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"Google token exchange failed ({resp.status_code}): {resp.text[:400]}"
        )
    data = resp.json()
    if "error" in data:
        raise RuntimeError(
            f"{data.get('error')}: {data.get('error_description', '')}"
        )
    return data


def exchange_callback(authorization_response: str) -> tuple[str, str | None, str | None]:
    parsed = urlparse(authorization_response)
    qs = parse_qs(parsed.query)
    state = (qs.get("state") or [None])[0]
    code = (qs.get("code") or [None])[0]
    granted_scope = (qs.get("scope") or [""])[0]

    if not code:
        raise RuntimeError("Missing authorization code in callback")

    if "gmail.send" not in granted_scope:
        logger.warning("gmail.send not in granted scope: %s", granted_scope)
        raise RuntimeError("missing_gmail_send_scope")

    flow: Flow | None = None
    user_id: int | None = None
    if state:
        with _sessions_lock:
            session = _sessions.pop(state, None)
            if session:
                flow, user_id = session

    if user_id is None:
        raise RuntimeError("OAuth session expired or invalid state")

    if flow is not None:
        try:
            flow.fetch_token(authorization_response=authorization_response)
            creds = flow.credentials
            return _save_credentials(
                user_id,
                creds.token,
                creds.refresh_token,
                creds.expiry,
            )
        except Exception as exc:
            logger.warning("Flow token exchange failed, trying HTTP fallback: %s", exc)

    data = _exchange_with_httpx(code)
    expires_at = None
    if data.get("expires_in"):
        expires_at = datetime.fromtimestamp(
            datetime.now(timezone.utc).timestamp() + int(data["expires_in"]),
            tz=timezone.utc,
        )
    return _save_credentials(
        user_id,
        data["access_token"],
        data.get("refresh_token"),
        expires_at,
    )


def _save_credentials(
    user_id: int,
    access_token: str,
    refresh_token: str | None,
    expiry: datetime | None,
) -> tuple[str, str | None, str | None]:
    email = _fetch_google_email(access_token)
    expires_at = None
    if expiry:
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        expires_at = expiry.isoformat()
    save_token(
        user_id,
        "google",
        access_token=access_token,
        refresh_token=refresh_token,
        email=email,
        expires_at=expires_at,
    )
    logger.info("Google OAuth connected for user %s (%s)", user_id, email or "(unknown)")
    return access_token, refresh_token, email


def _fetch_google_email(access_token: str) -> str | None:
    resp = httpx.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    if resp.status_code == 200:
        return resp.json().get("email")
    return None


def get_valid_access_token(user_id: int) -> str | None:
    token_row = get_token(user_id, "google")
    if not token_row:
        return None
    return token_row["access_token"]


def oauth_config_summary() -> dict[str, str | list[str]]:
    return {
        "redirect_uri": settings.google_redirect_uri,
        "client_id_suffix": settings.google_client_id[-20:] if settings.google_client_id else "",
        "scopes": SCOPES,
    }
