"""OAuth token storage — scoped per user with encrypted tokens."""

from backend.app.db import get_connection
from backend.app.services import crypto


def save_token(
    user_id: int,
    provider: str,
    access_token: str,
    email: str | None = None,
    refresh_token: str | None = None,
    expires_at: str | None = None,
) -> None:
    enc_access = crypto.encrypt(access_token)
    enc_refresh = crypto.encrypt(refresh_token) if refresh_token else None
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO oauth_tokens
                (user_id, provider, email, access_token, refresh_token, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, provider) DO UPDATE SET
                email = excluded.email,
                access_token = excluded.access_token,
                refresh_token = COALESCE(excluded.refresh_token, oauth_tokens.refresh_token),
                expires_at = excluded.expires_at
            """,
            (user_id, provider, email, enc_access, enc_refresh, expires_at),
        )
        conn.commit()


def get_token(user_id: int, provider: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM oauth_tokens WHERE user_id = ? AND provider = ?",
            (user_id, provider),
        ).fetchone()
    if not row:
        return None
    data = dict(row)
    data["access_token"] = crypto.decrypt(data["access_token"])
    if data.get("refresh_token"):
        data["refresh_token"] = crypto.decrypt(data["refresh_token"])
    return data


def delete_token(user_id: int, provider: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM oauth_tokens WHERE user_id = ? AND provider = ?",
            (user_id, provider),
        )
        conn.commit()


def get_access_token(user_id: int, provider: str) -> str | None:
    token = get_token(user_id, provider)
    return token["access_token"] if token else None
