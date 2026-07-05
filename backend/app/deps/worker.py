"""FastAPI dependency — resolve paired Search Helper from bearer token."""

from fastapi import Header, HTTPException, status

from backend.app.services.worker_store import get_worker_device_by_token


def get_worker_device(
    authorization: str | None = Header(default=None),
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing worker token",
        )

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing worker token",
        )

    device = get_worker_device_by_token(token)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked worker token",
        )
    return device
