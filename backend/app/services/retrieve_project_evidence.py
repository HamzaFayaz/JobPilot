"""Hybrid project evidence retrieval — no LLM."""

from __future__ import annotations

import logging
import math
import re
from difflib import SequenceMatcher
from typing import Any

from backend.app.config import settings
from backend.app.observability import span
from backend.app.services import embedding_client, evidence_index_store, faiss_index

logger = logging.getLogger(__name__)


def _retrieval_cfg() -> dict[str, int]:
    cfg = settings.retrieval_config
    return {
        "bm25_top_k": int(cfg.get("bm25_top_k", 30)),
        "vector_top_k": int(cfg.get("vector_top_k", 30)),
        "rrf_k": int(cfg.get("rrf_k", 60)),
        "target_chunks_per_job": int(cfg.get("target_chunks_per_job", 14)),
        "max_chunks_per_job": int(cfg.get("max_chunks_per_job", 20)),
        "max_chunks_per_project": int(cfg.get("max_chunks_per_project", 3)),
    }


def _sanitize_fts_query(query: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9_+#-]+", query.lower())
    tokens = [t for t in tokens if len(t) >= 2]
    if not tokens:
        return ""
    return " OR ".join(f'"{t}"' for t in tokens[:40])


def _rrf_fuse(
    ranked_lists: list[list[tuple[str, float]]],
    *,
    rrf_k: int,
) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, (chunk_id, _score) in enumerate(ranked, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (rrf_k + rank)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


def parse_cv_project_slots(cv_text: str, portfolio_projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deterministic CV project section parser for swap-aware retrieval."""
    if not cv_text.strip():
        return []

    lines = cv_text.splitlines()
    start_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^\s*(projects?|portfolio|selected projects)\s*:?\s*$", line, re.I):
            start_idx = i + 1
            break
    if start_idx is None:
        return []

    section_lines: list[str] = []
    for line in lines[start_idx:]:
        if re.match(r"^\s*(experience|education|skills|certifications)\s*:?\s*$", line, re.I):
            break
        if line.strip():
            section_lines.append(line.strip())

    entries: list[str] = []
    buf: list[str] = []
    for line in section_lines:
        if re.match(r"^[-•*]\s+", line) or re.match(r"^\d+[.)]\s+", line):
            if buf:
                entries.append(" ".join(buf))
            buf = [re.sub(r"^[-•*]\s+|^\d+[.)]\s+", "", line).strip()]
        elif buf:
            buf.append(line)
        else:
            buf = [line]
    if buf:
        entries.append(" ".join(buf))

    portfolio_by_name = {p.get("name", "").lower(): p for p in portfolio_projects}
    slots: list[dict[str, Any]] = []
    for idx, entry in enumerate(entries):
        matched_id = None
        entry_lower = entry.lower()
        best_ratio = 0.0
        for name, project in portfolio_by_name.items():
            if not name:
                continue
            ratio = SequenceMatcher(None, entry_lower, name).ratio()
            if name in entry_lower:
                ratio = max(ratio, 0.85)
            if ratio > best_ratio:
                best_ratio = ratio
                matched_id = project.get("id")
        if best_ratio < 0.45:
            matched_id = None
        slots.append(
            {
                "slot_index": idx,
                "cv_project_name": entry[:200],
                "chars_budget": max(80, min(200, len(entry))),
                "matched_portfolio_project_id": matched_id,
            }
        )
    return slots


def _layer1_projects(projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    layer: list[dict[str, Any]] = []
    for project in projects:
        layer.append(
            {
                "source_id": f"project:{project.get('id')}:overview",
                "project_id": project.get("id"),
                "name": project.get("name"),
                "repo_full_name": project.get("repo_full_name"),
                "portfolio_overview": project.get("portfolio_overview")
                or project.get("portfolioOverview")
                or "",
            }
        )
    return layer


def _layer2a_projects(projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    layer: list[dict[str, Any]] = []
    for project in projects:
        layer.append(
            {
                "source_id": f"project:{project.get('id')}:evidence_card",
                "project_id": project.get("id"),
                "name": project.get("name"),
                "evidence_card": project.get("evidence_card") or project.get("evidenceCard") or {},
            }
        )
    return layer


def _select_chunk_project_ids(
    ranked_chunks: list[dict[str, Any]],
    cv_slots: list[dict[str, Any]],
    portfolio_projects: list[dict[str, Any]],
    cfg: dict[str, int],
) -> set[str]:
    selected: set[str] = set()
    max_projects = max(1, math.ceil(len(portfolio_projects) * 0.6))

    for chunk in ranked_chunks:
        pid = chunk.get("project_id")
        if pid:
            selected.add(pid)
        if len(selected) >= max_projects:
            break

    for slot in cv_slots:
        pid = slot.get("matched_portfolio_project_id")
        if pid:
            selected.add(pid)

    on_cv = {
        slot.get("matched_portfolio_project_id")
        for slot in cv_slots
        if slot.get("matched_portfolio_project_id")
    }
    for project in portfolio_projects:
        pid = project.get("id")
        if pid and pid not in on_cv:
            selected.add(pid)
        if len(selected) >= max_projects:
            break

    return selected


def _pack_layer2b(
    ranked_chunks: list[dict[str, Any]],
    selected_project_ids: set[str],
    cfg: dict[str, int],
) -> list[dict[str, Any]]:
    per_project: dict[str, int] = {}
    packed: list[dict[str, Any]] = []
    for chunk in ranked_chunks:
        pid = chunk.get("project_id")
        if pid not in selected_project_ids:
            continue
        count = per_project.get(pid, 0)
        if count >= cfg["max_chunks_per_project"]:
            continue
        packed.append(
            {
                "source_id": chunk.get("id"),
                "project_id": pid,
                "project_name": chunk.get("project_name"),
                "heading_path": chunk.get("heading_path"),
                "content": chunk.get("content"),
                "retrieval_score": chunk.get("retrieval_score", 0.0),
                "source": "evidence_claim"
                if chunk.get("chunk_type") == "evidence_claim"
                else "readme_chunk",
            }
        )
        per_project[pid] = count + 1
        if len(packed) >= cfg["max_chunks_per_job"]:
            break
    return packed


def retrieve_project_evidence(
    user_id: int,
    job: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Build EnrichJobInputBundle via hybrid search — no LLM."""
    cfg = _retrieval_cfg()
    projects = profile.get("projects") or []
    cv_text = profile.get("cv_text") or ""

    title = job.get("title") or ""
    description = job.get("description_text") or ""
    query_text = f"{title}\n{description}".strip()

    cv_slots = parse_cv_project_slots(cv_text, projects)

    fts_query = _sanitize_fts_query(query_text)
    with span("bm25_search", user_id=user_id):
        bm25_hits = (
            evidence_index_store.bm25_search(user_id, fts_query, cfg["bm25_top_k"])
            if fts_query
            else []
        )

    vector_hits: list[tuple[str, float]] = []
    if query_text and settings.dashscope_api_key:
        try:
            with span(
                "embed_query",
                user_id=user_id,
                model=settings.embedding_model,
            ):
                query_vec, _ = embedding_client.embed_query(query_text)
            with span("faiss_search", user_id=user_id):
                vector_hits = faiss_index.vector_search(
                    user_id, query_vec, cfg["vector_top_k"]
                )
        except Exception as exc:
            logger.warning("Vector search failed for user %s: %s", user_id, exc)
    elif query_text:
        vector_hits = faiss_index.vector_search(user_id, _pseudo_query_vector(query_text), cfg["vector_top_k"])

    with span("rrf_fusion", user_id=user_id):
        fused = _rrf_fuse([bm25_hits, vector_hits], rrf_k=cfg["rrf_k"])
    candidate_ids = [cid for cid, _ in fused[: settings.rerank_candidate_pool]]
    candidates = evidence_index_store.get_chunks_by_ids(user_id, candidate_ids)
    candidate_by_id = {c["id"]: c for c in candidates}

    ordered_chunks: list[dict[str, Any]] = []
    candidate_chunks = [candidate_by_id[cid] for cid in candidate_ids if cid in candidate_by_id]
    if candidate_chunks and query_text:
        docs = [c["content"] for c in candidate_chunks]
        try:
            with span(
                "rerank_candidates",
                user_id=user_id,
                model=settings.rerank_model,
                candidate_count=len(docs),
            ):
                reranked = embedding_client.rerank_documents(
                    query_text,
                    docs,
                    top_n=settings.rerank_top_n,
                )
            for doc_idx, score in reranked:
                if doc_idx >= len(candidate_chunks):
                    continue
                chunk = dict(candidate_chunks[doc_idx])
                chunk["retrieval_score"] = score
                ordered_chunks.append(chunk)
        except Exception:
            for cid, rrf_score in fused[: settings.rerank_top_n]:
                if cid not in candidate_by_id:
                    continue
                chunk = dict(candidate_by_id[cid])
                chunk["retrieval_score"] = rrf_score
                ordered_chunks.append(chunk)
    else:
        for cid, rrf_score in fused[: cfg["max_chunks_per_job"]]:
            if cid not in candidate_by_id:
                continue
            chunk = dict(candidate_by_id[cid])
            chunk["retrieval_score"] = rrf_score
            ordered_chunks.append(chunk)

    selected_project_ids = _select_chunk_project_ids(
        ordered_chunks, cv_slots, projects, cfg
    )
    layer2b = _pack_layer2b(ordered_chunks, selected_project_ids, cfg)

    return {
        "job": {
            "title": title,
            "company": job.get("company"),
            "url": job.get("url"),
            "source_platform": job.get("source_platform") or job.get("platform"),
            "description_text": description,
        },
        "profile": {
            "cv_text": cv_text,
            "skills": profile.get("skills") or [],
            "target_roles": profile.get("target_roles") or profile.get("targetRoles") or [],
            "cv_project_slots": cv_slots,
        },
        "layer1_portfolio_overviews": _layer1_projects(projects),
        "layer2a_evidence_cards": _layer2a_projects(projects),
        "layer2b_readme_chunks": layer2b,
        "retrieval_debug": {
            "bm25_count": len(bm25_hits),
            "vector_count": len(vector_hits),
            "fused_count": len(fused),
            "selected_project_ids": sorted(selected_project_ids),
        },
    }


def _pseudo_query_vector(query: str) -> list[float]:
    import numpy as np

    dim = settings.embedding_dimensions
    seed = abs(hash(query)) % (2**32)
    rng = np.random.default_rng(seed)
    return rng.standard_normal(dim).astype(np.float32).tolist()
