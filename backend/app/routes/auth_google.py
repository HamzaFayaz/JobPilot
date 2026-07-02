"""Google OAuth routes — requires authenticated user for connect."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from backend.app.config import settings
from backend.app.deps.auth import get_current_user
from backend.app.services.gmail_oauth import begin_auth, exchange_callback, oauth_config_summary
from backend.app.services.oauth_store import delete_token

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth-google"])


@router.get("/auth/google")
def google_auth_start(current_user: dict = Depends(get_current_user)) -> RedirectResponse:
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    return RedirectResponse(begin_auth(current_user["id"]))


@router.get("/auth/google/callback")
def google_auth_callback(request: Request, error: str | None = None) -> RedirectResponse:
    if error:
        logger.warning("Google OAuth denied: %s", error)
        return RedirectResponse(f"{settings.frontend_url}/profile?gmail=error")
    try:
        exchange_callback(str(request.url))
    except Exception as exc:
        logger.exception("Google OAuth token exchange failed: %s", exc)
        if str(exc) == "missing_gmail_send_scope":
            return RedirectResponse(
                f"{settings.frontend_url}/profile?gmail=missing_send_scope"
            )
        return RedirectResponse(f"{settings.frontend_url}/profile?gmail=error")
    return RedirectResponse(f"{settings.frontend_url}/profile?gmail=connected")


@router.get("/auth/google/config")
def google_auth_config() -> dict:
    return oauth_config_summary()


@router.delete("/api/auth/google")
def google_disconnect(current_user: dict = Depends(get_current_user)) -> dict[str, bool]:
    delete_token(current_user["id"], "google")
    return {"disconnected": True}
