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
    projects_indexing_status TEXT NOT NULL DEFAULT 'idle',
    target_roles TEXT NOT NULL DEFAULT '[]',
    search_role TEXT,
    search_platform TEXT NOT NULL DEFAULT 'linkedin',
    search_country TEXT,
    search_work_mode TEXT NOT NULL DEFAULT 'both',
    search_max_listings INTEGER NOT NULL DEFAULT 8,
    search_job_age TEXT NOT NULL DEFAULT 'week',
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
    country TEXT,
    work_mode TEXT,
    max_listings INTEGER,
    job_age TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    error TEXT,
    jobs_ready_count INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS job_packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    run_id INTEGER REFERENCES search_runs(id) ON DELETE SET NULL,
    title TEXT,
    company TEXT,
    url TEXT,
    platform TEXT,
    description_text TEXT NOT NULL DEFAULT '',
    display_description_text TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    match_score INTEGER,
    current_cv_score INTEGER,
    suggested_cv_score INTEGER,
    cv_decision TEXT,
    swap_out_project TEXT,
    swap_in_text TEXT,
    draft_email TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'ready',
    error TEXT,
    analysis_json TEXT NOT NULL DEFAULT '{}',
    model_name TEXT,
    prompt_version TEXT,
    profile_snapshot_hash TEXT,
    package_key TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS job_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_package_id INTEGER REFERENCES job_packages(id) ON DELETE SET NULL,
    url TEXT,
    platform TEXT,
    title TEXT,
    company TEXT,
    status TEXT NOT NULL DEFAULT 'sent',
    email_subject TEXT,
    cv_filename TEXT,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS worker_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL DEFAULT 'Search Helper',
    browser_health TEXT NOT NULL DEFAULT 'not_installed',
    last_seen_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS worker_tasks (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    run_id INTEGER NOT NULL REFERENCES search_runs(id) ON DELETE CASCADE,
    type TEXT NOT NULL DEFAULT 'browser_search',
    status TEXT NOT NULL DEFAULT 'pending',
    payload_json TEXT NOT NULL,
    result_json TEXT,
    error TEXT,
    error_code TEXT,
    warnings_json TEXT,
    claimed_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    return {row["name"] for row in rows}


def _column_names(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def _ensure_columns(
    conn: sqlite3.Connection, table_name: str, column_defs: dict[str, str]
) -> None:
    existing_columns = _column_names(conn, table_name)
    for column_name, column_def in column_defs.items():
        if column_name in existing_columns:
            continue
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_def}")
        logger.info("Added %s.%s to database schema.", table_name, column_name)


def _ensure_search_schema(conn: sqlite3.Connection) -> None:
    _ensure_columns(
        conn,
        "profiles",
        {
            "search_role": "search_role TEXT",
            "search_platform": "search_platform TEXT NOT NULL DEFAULT 'linkedin'",
            "search_country": "search_country TEXT",
            "search_work_mode": "search_work_mode TEXT NOT NULL DEFAULT 'both'",
            "search_max_listings": "search_max_listings INTEGER NOT NULL DEFAULT 8",
            "search_job_age": "search_job_age TEXT NOT NULL DEFAULT 'week'",
            "projects_indexing_status": "projects_indexing_status TEXT NOT NULL DEFAULT 'idle'",
        },
    )
    _ensure_columns(
        conn,
        "search_runs",
        {
            "error": "error TEXT",
            "jobs_ready_count": "jobs_ready_count INTEGER NOT NULL DEFAULT 0",
            "updated_at": "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "finished_at": "finished_at TIMESTAMP",
            "country": "country TEXT",
            "work_mode": "work_mode TEXT",
            "max_listings": "max_listings INTEGER",
            "job_age": "job_age TEXT",
        },
    )
    _ensure_columns(
        conn,
        "job_packages",
        {
            "title": "title TEXT",
            "company": "company TEXT",
            "url": "url TEXT",
            "platform": "platform TEXT",
            "description_text": "description_text TEXT NOT NULL DEFAULT ''",
            "display_description_text": "display_description_text TEXT NOT NULL DEFAULT ''",
            "summary": "summary TEXT NOT NULL DEFAULT ''",
            "match_score": "match_score INTEGER",
            "current_cv_score": "current_cv_score INTEGER",
            "suggested_cv_score": "suggested_cv_score INTEGER",
            "cv_decision": "cv_decision TEXT",
            "swap_out_project": "swap_out_project TEXT",
            "swap_in_text": "swap_in_text TEXT",
            "draft_email": "draft_email TEXT NOT NULL DEFAULT ''",
            "status": "status TEXT NOT NULL DEFAULT 'ready'",
            "error": "error TEXT",
            "analysis_json": "analysis_json TEXT NOT NULL DEFAULT '{}'",
            "model_name": "model_name TEXT",
            "prompt_version": "prompt_version TEXT",
            "profile_snapshot_hash": "profile_snapshot_hash TEXT",
            "package_key": "package_key TEXT",
            "updated_at": "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        },
    )
    _ensure_columns(
        conn,
        "job_applications",
        {
            "url": "url TEXT",
            "platform": "platform TEXT",
            "title": "title TEXT",
            "company": "company TEXT",
            "status": "status TEXT NOT NULL DEFAULT 'sent'",
            "email_subject": "email_subject TEXT",
            "cv_filename": "cv_filename TEXT",
            "sent_at": "sent_at TIMESTAMP",
        },
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_job_packages_run_package_key
        ON job_packages (run_id, package_key)
        WHERE run_id IS NOT NULL AND package_key IS NOT NULL
        """
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_job_applications_user_platform_url
        ON job_applications (user_id, platform, url)
        WHERE url IS NOT NULL
        """
    )


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


def _ensure_evidence_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS project_readme_chunks (
            id              TEXT PRIMARY KEY,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            project_id      TEXT NOT NULL,
            project_name    TEXT NOT NULL,
            repo_full_name  TEXT,
            chunk_type      TEXT NOT NULL DEFAULT 'readme_section'
                            CHECK (chunk_type IN ('readme_section', 'evidence_claim')),
            parent_heading  TEXT,
            heading_path    TEXT NOT NULL,
            content           TEXT NOT NULL,
            embed_text        TEXT NOT NULL,
            token_count       INTEGER NOT NULL DEFAULT 0,
            stack_tags        TEXT NOT NULL DEFAULT '[]',
            source_start      INTEGER,
            source_end        INTEGER,
            short_chunk_reason TEXT,
            oversize_reason    TEXT,
            chunk_index       INTEGER NOT NULL DEFAULT 0,
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_chunks_user_id
            ON project_readme_chunks (user_id);

        CREATE INDEX IF NOT EXISTS idx_chunks_user_project
            ON project_readme_chunks (user_id, project_id);

        CREATE UNIQUE INDEX IF NOT EXISTS idx_chunks_user_project_slot
            ON project_readme_chunks (user_id, project_id, chunk_type, heading_path, chunk_index);

        CREATE TABLE IF NOT EXISTS user_evidence_indexes (
            user_id           INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            embedding_model   TEXT NOT NULL,
            embedding_dims    INTEGER NOT NULL,
            faiss_path        TEXT NOT NULL,
            meta_path         TEXT NOT NULL,
            chunk_count       INTEGER NOT NULL DEFAULT 0,
            index_version     INTEGER NOT NULL DEFAULT 1,
            built_at          TIMESTAMP,
            updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    _ensure_columns(
        conn,
        "project_readme_chunks",
        {
            "short_chunk_reason": "short_chunk_reason TEXT",
            "oversize_reason": "oversize_reason TEXT",
        },
    )

    fts_exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE name='project_readme_chunks_fts'"
    ).fetchone()
    if not fts_exists:
        conn.executescript(
            """
            CREATE VIRTUAL TABLE project_readme_chunks_fts USING fts5(
                project_name,
                heading_path,
                content,
                stack_tags,
                content='project_readme_chunks',
                content_rowid='rowid',
                tokenize='porter unicode61'
            );

            CREATE TRIGGER project_readme_chunks_ai AFTER INSERT ON project_readme_chunks BEGIN
                INSERT INTO project_readme_chunks_fts(rowid, project_name, heading_path, content, stack_tags)
                VALUES (new.rowid, new.project_name, new.heading_path, new.content, new.stack_tags);
            END;

            CREATE TRIGGER project_readme_chunks_ad AFTER DELETE ON project_readme_chunks BEGIN
                INSERT INTO project_readme_chunks_fts(project_readme_chunks_fts, rowid, project_name, heading_path, content, stack_tags)
                VALUES ('delete', old.rowid, old.project_name, old.heading_path, old.content, old.stack_tags);
            END;

            CREATE TRIGGER project_readme_chunks_au AFTER UPDATE ON project_readme_chunks BEGIN
                INSERT INTO project_readme_chunks_fts(project_readme_chunks_fts, rowid, project_name, heading_path, content, stack_tags)
                VALUES ('delete', old.rowid, old.project_name, old.heading_path, old.content, old.stack_tags);
                INSERT INTO project_readme_chunks_fts(rowid, project_name, heading_path, content, stack_tags)
                VALUES (new.rowid, new.project_name, new.heading_path, new.content, new.stack_tags);
            END;
            """
        )


def init_db() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.faiss_dir.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        if _is_legacy_schema(conn):
            _migrate_legacy_schema(conn)
        else:
            conn.executescript(SCHEMA)
            _ensure_search_schema(conn)
            _ensure_evidence_schema(conn)
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
