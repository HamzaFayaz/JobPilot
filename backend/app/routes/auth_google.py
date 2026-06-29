"""Google OAuth routes."""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from backend.app.config import settings
from backend.app.services.gmail_oauth import create_flow, exchange_code
from backend.app.services.oauth_store import delete_token

router = APIRouter(tags=["auth-google"])


@router.get("/auth/google")
def google_auth_start() -> RedirectResponse:
    flow = create_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return RedirectResponse(auth_url)


@router.get("/auth/google/callback")
def google_auth_callback(code: str) -> RedirectResponse:
    exchange_code(code)
    return RedirectResponse(f"{settings.frontend_url}/profile?gmail=connected")


@router.delete("/api/auth/google")
def google_disconnect() -> dict[str, bool]:
    delete_token("google")
    return {"disconnected": True}
