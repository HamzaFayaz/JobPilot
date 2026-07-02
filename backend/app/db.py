"""SQLite database initialization, migration, and connection helpers."""

import logging
import sqlite3
from contextlib import contextmanager
from typing import Generator

from backend.app.config import settings

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    cv_filename TEXT,
    cv_path TEXT,
    cv_text TEXT,
    skills TEXT NOT NULL DEFAULT '[]',
    skills_extraction_status TEXT NOT NULL DEFAULT 'idle',
    target_roles TEXT NOT NULL DEFAULT '[]',
    projects TEXT NOT NULL DEFAULT '[]',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS oauth_tokens (
    user_id INTEGER NOT NULL,
    provider TEXT NOT NULL,
    email TEXT,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    PRIMARY KEY (user_id, provider),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS search_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT,
    platform TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS job_packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    run_id INTEGER REFERENCES search_runs(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS job_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_package_id INTEGER REFERENCES job_packages(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    return {row["name"] for row in rows}


def _is_legacy_schema(conn: sqlite3.Connection) -> bool:
    if "users" in _table_names(conn):
        return False
    if "profiles" not in _table_names(conn):
        return False
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE name='profiles'"
    ).fetchone()
    return bool(row and row["sql"] and "CHECK (id = 1)" in row["sql"])


def _migrate_legacy_schema(conn: sqlite3.Connection) -> None:
    legacy_profile = conn.execute("SELECT * FROM profiles WHERE id = 1").fetchone()
    if legacy_profile:
        logger.warning(
            "Legacy single-user profile data found (id=1). "
            "Not auto-migrated — use scripts/migrate_single_user.py to assign to an account."
        )

    legacy_tokens = conn.execute("SELECT COUNT(*) AS n FROM oauth_tokens").fetchone()
    if legacy_tokens and legacy_tokens["n"]:
        logger.warning(
            "Legacy OAuth tokens found. Not auto-migrated — "
            "use scripts/migrate_single_user.py after creating a user account."
        )

    conn.execute("DROP TABLE IF EXISTS oauth_tokens")
    conn.execute("DROP TABLE IF EXISTS profiles")
    conn.executescript(SCHEMA)
    conn.commit()
    logger.info("Migrated database from single-user to multi-user schema.")


def init_db() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        if _is_legacy_schema(conn):
            _migrate_legacy_schema(conn)
        else:
            conn.executescript(SCHEMA)
            conn.commit()


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()
