"""Signed OAuth state tying callbacks to authenticated user_id."""

import base64
import hashlib
import hmac
import json
import time

from backend.app.config import settings

_MAX_AGE_SECONDS = 600


def create_oauth_state(user_id: int) -> str:
    payload = {"user_id": user_id, "ts": int(time.time())}
    data = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    sig = hmac.new(
        settings.jwt_secret.encode(), data.encode(), hashlib.sha256
    ).hexdigest()
    return f"{data}.{sig}"


def verify_oauth_state(state: str) -> int:
    if not settings.jwt_secret:
        raise ValueError("JWT_SECRET is not configured")
    try:
        data, sig = state.rsplit(".", 1)
    except ValueError as exc:
        raise ValueError("Invalid OAuth state") from exc

    expected = hmac.new(
        settings.jwt_secret.encode(), data.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise ValueError("Invalid OAuth state signature")

    payload = json.loads(base64.urlsafe_b64decode(data.encode()))
    ts = payload.get("ts", 0)
    if int(time.time()) - ts > _MAX_AGE_SECONDS:
        raise ValueError("OAuth state expired")
    return int(payload["user_id"])
