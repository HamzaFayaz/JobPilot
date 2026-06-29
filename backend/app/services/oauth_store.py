"""OAuth token storage."""

from datetime import datetime, timezone

from backend.app.db import get_connection


def save_token(
    provider: str,
    access_token: str,
    email: str | None = None,
    refresh_token: str | None = None,
    expires_at: str | None = None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO oauth_tokens (provider, email, access_token, refresh_token, expires_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(provider) DO UPDATE SET
                email = excluded.email,
                access_token = excluded.access_token,
                refresh_token = COALESCE(excluded.refresh_token, oauth_tokens.refresh_token),
                expires_at = excluded.expires_at
            """,
            (provider, email, access_token, refresh_token, expires_at),
        )
        conn.commit()


def get_token(provider: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM oauth_tokens WHERE provider = ?", (provider,)
        ).fetchone()
    return dict(row) if row else None


def delete_token(provider: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM oauth_tokens WHERE provider = ?", (provider,))
        conn.commit()


def get_access_token(provider: str) -> str | None:
    token = get_token(provider)
    return token["access_token"] if token else None
