"""FastAPI auth dependency — resolve current user from JWT cookie."""

from fastapi import Cookie, HTTPException, status

from backend.app.services import auth_service
from backend.app.services.user_store import get_user_by_id

COOKIE_NAME = auth_service.COOKIE_NAME


def get_current_user(
    jobpilot_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> dict:
    if not jobpilot_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = auth_service.decode_access_token(jobpilot_token)
        user_id = int(payload["sub"])
    except (ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        ) from exc

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user
