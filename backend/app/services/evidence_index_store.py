"""SQLite CRUD for project evidence chunks and FTS5 search."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from backend.app.db import get_connection
from backend.app.services.readme_chunker import ReadmeChunk

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def delete_project_chunks(user_id: int, project_id: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM project_readme_chunks WHERE user_id = ? AND project_id = ?",
            (user_id, project_id),
        )
        conn.commit()
        return cur.rowcount


def insert_chunks(
    user_id: int,
    project_id: str,
    project_name: str,
    repo_full_name: str | None,
    stack_tags: list[str],
    chunks: list[ReadmeChunk],
) -> list[str]:
    """Insert chunk rows; returns chunk ids in order."""
    if not chunks:
        return []
    stack_json = json.dumps(stack_tags)
    now = _now_iso()
    ids: list[str] = []
    with get_connection() as conn:
        for chunk in chunks:
            conn.execute(
                """
                INSERT INTO project_readme_chunks (
                    id, user_id, project_id, project_name, repo_full_name,
                    chunk_type, parent_heading, heading_path, content, embed_text,
                    token_count, stack_tags, source_start, source_end, chunk_index,
                    short_chunk_reason, oversize_reason, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk.id,
                    user_id,
                    project_id,
                    project_name,
                    repo_full_name,
                    chunk.chunk_type,
                    chunk.parent_heading,
                    chunk.heading_path,
                    chunk.content,
                    chunk.embed_text,
                    chunk.token_count,
                    stack_json,
                    chunk.source_start,
                    chunk.source_end,
                    chunk.chunk_index,
                    chunk.short_chunk_reason,
                    chunk.oversize_reason,
                    now,
                    now,
                ),
            )
            ids.append(chunk.id)
        conn.commit()
    return ids


def list_user_chunks(user_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM project_readme_chunks
            WHERE user_id = ?
            ORDER BY project_id, chunk_index
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_project_chunks(user_id: int, project_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM project_readme_chunks
            WHERE user_id = ? AND project_id = ?
            ORDER BY chunk_index ASC
            """,
            (user_id, project_id),
        ).fetchall()
    return [dict(row) for row in rows]


def get_chunks_by_ids(user_id: int, chunk_ids: list[str]) -> list[dict[str, Any]]:
    if not chunk_ids:
        return []
    placeholders = ",".join("?" for _ in chunk_ids)
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM project_readme_chunks
            WHERE user_id = ? AND id IN ({placeholders})
            """,
            [user_id, *chunk_ids],
        ).fetchall()
    by_id = {row["id"]: dict(row) for row in rows}
    return [by_id[cid] for cid in chunk_ids if cid in by_id]


def bm25_search(user_id: int, query: str, top_k: int = 30) -> list[tuple[str, float]]:
    """FTS5 BM25 search; returns (chunk_id, bm25_score)."""
    if not query.strip():
        return []
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT c.id, bm25(project_readme_chunks_fts) AS score
                FROM project_readme_chunks_fts fts
                JOIN project_readme_chunks c ON c.rowid = fts.rowid
                WHERE project_readme_chunks_fts MATCH ?
                  AND c.user_id = ?
                ORDER BY score
                LIMIT ?
                """,
                (query, user_id, top_k),
            ).fetchall()
    except Exception as exc:
        logger.warning("FTS5 search failed for query %r: %s", query, exc)
        return []
    return [(row["id"], float(row["score"])) for row in rows]


def upsert_index_record(
    user_id: int,
    *,
    embedding_model: str,
    embedding_dims: int,
    faiss_path: str,
    meta_path: str,
    chunk_count: int,
    index_version: int,
) -> None:
    now = _now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO user_evidence_indexes (
                user_id, embedding_model, embedding_dims, faiss_path, meta_path,
                chunk_count, index_version, built_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                embedding_model = excluded.embedding_model,
                embedding_dims = excluded.embedding_dims,
                faiss_path = excluded.faiss_path,
                meta_path = excluded.meta_path,
                chunk_count = excluded.chunk_count,
                index_version = excluded.index_version,
                built_at = excluded.built_at,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                embedding_model,
                embedding_dims,
                faiss_path,
                meta_path,
                chunk_count,
                index_version,
                now,
                now,
            ),
        )
        conn.commit()


def get_index_record(user_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM user_evidence_indexes WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def next_index_version(user_id: int) -> int:
    record = get_index_record(user_id)
    if not record:
        return 1
    return int(record.get("index_version", 0)) + 1
