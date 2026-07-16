"""Orchestrate chunking and index rebuild at GitHub import/refresh."""

from __future__ import annotations

import logging
from typing import Any

from backend.app.config import settings
from backend.app.services import embedding_client, evidence_index_store, faiss_index, readme_chunker

logger = logging.getLogger(__name__)


def _stack_tags_from_project(project: dict[str, Any]) -> list[str]:
    card = project.get("evidence_card") or project.get("evidenceCard") or {}
    return list(card.get("tech_stack") or card.get("techStack") or [])


def _claims_from_project(project: dict[str, Any]) -> list[dict]:
    card = project.get("evidence_card") or project.get("evidenceCard") or {}
    return list(card.get("evidence") or [])


def index_project_evidence(user_id: int, project: dict[str, Any]) -> dict[str, Any]:
    """Chunk README + evidence claims and rebuild user FAISS index."""
    project_id = project["id"]
    project_name = project.get("name") or "Project"
    repo_full_name = project.get("repo_full_name")
    readme_md = project.get("readme_md") or ""
    stack_tags = _stack_tags_from_project(project)

    evidence_index_store.delete_project_chunks(user_id, project_id)

    embed_fn = None
    if readme_md.strip() and settings.dashscope_api_key:

        def _embed_boundary(texts: list[str]) -> list[list[float]]:
            vectors, _ = embedding_client.embed_texts(texts, text_type="document")
            return vectors

        embed_fn = _embed_boundary

    chunk_result = readme_chunker.chunk_readme(
        readme_md,
        project_name=project_name,
        stack_tags=stack_tags,
        embed_fn=embed_fn,
    )
    claim_chunks = readme_chunker.evidence_claim_chunks(
        _claims_from_project(project),
        project_name=project_name,
        stack_tags=stack_tags,
        start_index=len(chunk_result.chunks),
    )
    all_chunks = chunk_result.chunks + claim_chunks

    chunk_ids = evidence_index_store.insert_chunks(
        user_id,
        project_id,
        project_name,
        repo_full_name,
        stack_tags,
        all_chunks,
    )

    meta = faiss_index.rebuild_user_faiss_index(user_id)
    logger.info(
        "Indexed project %s for user %s: %d chunks",
        project_id,
        user_id,
        len(chunk_ids),
    )
    return {
        "project_id": project_id,
        "chunk_count": len(chunk_ids),
        "chunk_ids": chunk_ids,
        "index_meta": meta,
    }


def reindex_all_projects(user_id: int, projects: list[dict[str, Any]]) -> dict[str, Any]:
    """Rebuild chunks for every project in profile."""
    results = []
    for project in projects:
        results.append(index_project_evidence(user_id, project))
    return {"projects": results}
