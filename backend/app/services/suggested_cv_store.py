"""Persist suggested-CV drafts (never overwrite master CV)."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.config import settings
from backend.app.db import get_connection

_UNSAFE_FILENAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
_SUFFIX_RE = re.compile(r"^(.+)_(\d+)$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def drafts_dir(user_id: int) -> Path:
    path = settings.user_uploads_dir(user_id) / "suggested_cv"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_stem(cv_filename: str | None) -> str:
    raw = (cv_filename or "CV").strip()
    stem = Path(raw).stem or "CV"
    stem = _UNSAFE_FILENAME_RE.sub("_", stem).strip(" ._") or "CV"
    return stem[:120]


def next_suggested_cv_filename(user_id: int, cv_filename: str | None) -> str:
    """Return `{cvStem}_1.docx`, then `_2`, `_3`, … based on existing draft files."""
    stem = _safe_stem(cv_filename)
    directory = drafts_dir(user_id)
    used: set[int] = set()
    for path in directory.glob(f"{stem}_*.docx"):
        match = _SUFFIX_RE.match(path.stem)
        if match and match.group(1) == stem:
            used.add(int(match.group(2)))
    number = 1
    while number in used:
        number += 1
    return f"{stem}_{number}.docx"


def _row_to_draft(row) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "user_id": int(row["user_id"]),
        "package_id": int(row["package_id"]),
        "filename": row["filename"],
        "path": row["path"],
        "approved_slot_indexes": json.loads(row["approved_slot_indexes_json"] or "[]"),
        "auto_shortened": bool(row["auto_shortened"]),
        "model_name": row["model_name"],
        "prompt_version": row["prompt_version"],
        "generated": json.loads(row["generated_json"] or "{}"),
        "created_at": row["created_at"],
    }


def insert_draft(
    *,
    user_id: int,
    package_id: int,
    filename: str,
    path: str,
    approved_slot_indexes: list[int],
    auto_shortened: bool,
    model_name: str | None,
    prompt_version: str | None,
    generated_json: dict[str, Any],
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO suggested_cv_drafts (
                user_id, package_id, filename, path,
                approved_slot_indexes_json, auto_shortened,
                model_name, prompt_version, generated_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                package_id,
                filename,
                path,
                json.dumps(approved_slot_indexes),
                1 if auto_shortened else 0,
                model_name,
                prompt_version,
                json.dumps(generated_json, ensure_ascii=False),
                _now_iso(),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def get_draft(user_id: int, draft_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, user_id, package_id, filename, path,
                   approved_slot_indexes_json, auto_shortened,
                   model_name, prompt_version, generated_json, created_at
            FROM suggested_cv_drafts
            WHERE id = ? AND user_id = ?
            """,
            (draft_id, user_id),
        ).fetchone()
    if row is None:
        return None
    return _row_to_draft(row)


def get_latest_draft_for_package(
    user_id: int, package_id: int
) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, user_id, package_id, filename, path,
                   approved_slot_indexes_json, auto_shortened,
                   model_name, prompt_version, generated_json, created_at
            FROM suggested_cv_drafts
            WHERE user_id = ? AND package_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id, package_id),
        ).fetchone()
    if row is None:
        return None
    return _row_to_draft(row)


def delete_drafts_for_package(user_id: int, package_id: int) -> int:
    """Delete suggested-CV files + DB rows for a package (used on skip)."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, path FROM suggested_cv_drafts
            WHERE user_id = ? AND package_id = ?
            """,
            (user_id, package_id),
        ).fetchall()
        conn.execute(
            """
            DELETE FROM suggested_cv_drafts
            WHERE user_id = ? AND package_id = ?
            """,
            (user_id, package_id),
        )
        conn.commit()
    deleted = 0
    for row in rows:
        path = Path(str(row["path"] or ""))
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass
        deleted += 1
    return deleted
