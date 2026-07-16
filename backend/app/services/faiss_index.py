"""Per-user FAISS index build, load, and search."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from backend.app.config import settings
from backend.app.db import get_connection
from backend.app.services import embedding_client, evidence_index_store

logger = logging.getLogger(__name__)


def _faiss_path(user_id: int) -> Path:
    return settings.faiss_dir / f"{user_id}.index"


def _meta_path(user_id: int) -> Path:
    return settings.faiss_dir / f"{user_id}.meta.json"


def _load_meta(user_id: int) -> dict[str, Any] | None:
    path = _meta_path(user_id)
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def rebuild_user_faiss_index(user_id: int) -> dict[str, Any] | None:
    """Rebuild FAISS index for all chunks belonging to user."""
    settings.faiss_dir.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, embed_text FROM project_readme_chunks
            WHERE user_id = ?
            ORDER BY project_id, chunk_index
            """,
            (user_id,),
        ).fetchall()

    if not rows:
        for path in (_faiss_path(user_id), _meta_path(user_id)):
            if path.exists():
                path.unlink()
        with get_connection() as conn:
            conn.execute("DELETE FROM user_evidence_indexes WHERE user_id = ?", (user_id,))
            conn.commit()
        return None

    chunk_ids = [row["id"] for row in rows]
    texts = [row["embed_text"] for row in rows]

    if settings.dashscope_api_key:
        vectors, model = embedding_client.embed_texts(texts, text_type="document")
    else:
        logger.warning("No API key — using hash pseudo-embeddings for user %s", user_id)
        model = "pseudo-local"
        vectors = _pseudo_embed(texts)

    normalized = embedding_client.normalize_vectors(vectors)
    dim = normalized.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(normalized)

    faiss_path = _faiss_path(user_id)
    meta_path = _meta_path(user_id)
    faiss.write_index(index, str(faiss_path))

    version = evidence_index_store.next_index_version(user_id)
    meta = {
        "user_id": user_id,
        "embedding_model": model,
        "embedding_dims": dim,
        "index_type": "IndexFlatIP",
        "chunk_ids": chunk_ids,
        "chunk_count": len(chunk_ids),
        "built_at": datetime.now(timezone.utc).isoformat(),
        "index_version": version,
    }
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    evidence_index_store.upsert_index_record(
        user_id,
        embedding_model=model,
        embedding_dims=dim,
        faiss_path=str(faiss_path),
        meta_path=str(meta_path),
        chunk_count=len(chunk_ids),
        index_version=version,
    )
    return meta


def _pseudo_embed(texts: list[str]) -> list[list[float]]:
    """Deterministic local vectors for tests without API key."""
    dim = settings.embedding_dimensions
    vectors: list[list[float]] = []
    for text in texts:
        seed = abs(hash(text)) % (2**32)
        rng = np.random.default_rng(seed)
        vec = rng.standard_normal(dim).astype(np.float32)
        vectors.append(vec.tolist())
    return vectors


def vector_search(user_id: int, query_vector: list[float], top_k: int = 30) -> list[tuple[str, float]]:
    """Search user FAISS index; returns (chunk_id, similarity)."""
    faiss_path = _faiss_path(user_id)
    meta = _load_meta(user_id)
    if not meta or not faiss_path.exists():
        return []

    index = faiss.read_index(str(faiss_path))
    query = embedding_client.normalize_vectors([query_vector])
    scores, indices = index.search(query, min(top_k, index.ntotal))
    chunk_ids = meta["chunk_ids"]
    results: list[tuple[str, float]] = []
    for idx, score in zip(indices[0], scores[0]):
        if idx < 0 or idx >= len(chunk_ids):
            continue
        results.append((chunk_ids[int(idx)], float(score)))
    return results


def delete_user_index_files(user_id: int) -> None:
    for path in (_faiss_path(user_id), _meta_path(user_id)):
        if path.exists():
            path.unlink()
