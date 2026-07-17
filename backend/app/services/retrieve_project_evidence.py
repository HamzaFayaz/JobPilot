"""Hybrid project evidence retrieval — no LLM."""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

from backend.app.config import settings
from backend.app.observability import span
from backend.app.services import embedding_client, evidence_index_store, faiss_index
from backend.app.services.cv_project_slots import parse_cv_project_slots
from backend.app.services.job_requirement_queries import extract_requirement_queries

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
        "max_requirement_queries": int(cfg.get("max_requirement_queries", 12)),
        "candidates_per_requirement": int(cfg.get("candidates_per_requirement", 25)),
        "rerank_candidates_per_requirement": int(
            cfg.get("rerank_candidates_per_requirement", 15)
        ),
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


def _content_fingerprint(content: str) -> str:
    normalized = re.sub(r"\W+", " ", content.casefold()).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _content_tokens(content: str) -> set[str]:
    return set(re.findall(r"[a-z0-9+#.]+", content.casefold()))


def _pack_for_coverage(
    candidates: list[dict[str, Any]],
    requirements: list[dict[str, Any]],
    cfg: dict[str, int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    importance_order = {"required": 0, "preferred": 1, "general": 2}
    requirement_order = {
        item["requirement_id"]: importance_order.get(item["importance"], 2)
        for item in requirements
        if not item.get("is_fallback")
    }
    uncovered = set(requirement_order)
    per_project: dict[str, int] = {}
    packed: list[dict[str, Any]] = []
    removals: list[dict[str, Any]] = []
    used_fingerprints: set[str] = set()
    used_token_sets: list[set[str]] = []
    remaining = list(candidates)
    while remaining and len(packed) < cfg["max_chunks_per_job"]:
        eligible = [
            chunk
            for chunk in remaining
            if per_project.get(chunk.get("project_id"), 0)
            < cfg["max_chunks_per_project"]
        ]
        if not eligible:
            break
        eligible.sort(
            key=lambda chunk: (
                min(
                    (
                        requirement_order.get(requirement_id, 3)
                        for requirement_id in chunk["requirement_ids"]
                        if requirement_id in uncovered
                    ),
                    default=4,
                ),
                -len(set(chunk["requirement_ids"]) & uncovered),
                -float(chunk.get("best_retrieval_score", 0.0)),
                chunk["id"],
            )
        )
        chunk = eligible[0]
        remaining.remove(chunk)
        fingerprint = chunk["content_fingerprint"]
        if fingerprint in used_fingerprints:
            removals.append({"chunk_id": chunk["id"], "reason": "normalized_duplicate"})
            continue
        tokens = _content_tokens(chunk.get("content") or "")
        if any(
            len(tokens & existing) / max(1, len(tokens | existing)) >= 0.85
            for existing in used_token_sets
        ):
            removals.append({"chunk_id": chunk["id"], "reason": "near_duplicate"})
            continue
        adds_coverage = bool(set(chunk["requirement_ids"]) & uncovered)
        if not adds_coverage and packed:
            break
        pid = chunk.get("project_id")
        packed.append(
            {
                "source_id": chunk["id"],
                "project_id": pid,
                "project_name": chunk.get("project_name"),
                "heading_path": chunk.get("heading_path"),
                "content": chunk.get("content"),
                "retrieval_score": chunk.get("best_retrieval_score", 0.0),
                "source": "evidence_claim"
                if chunk.get("chunk_type") == "evidence_claim"
                else "readme_chunk",
                "source_start": chunk.get("source_start"),
                "source_end": chunk.get("source_end"),
                "requirement_ids": sorted(chunk["requirement_ids"]),
                "content_hash": hashlib.sha256(
                    (chunk.get("content") or "").encode("utf-8")
                ).hexdigest(),
                "retrieval_provenance": chunk["per_requirement"],
            }
        )
        used_fingerprints.add(fingerprint)
        used_token_sets.append(tokens)
        per_project[pid] = per_project.get(pid, 0) + 1
        uncovered -= set(chunk["requirement_ids"])
    return packed, removals


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
    cv_slots = parse_cv_project_slots(cv_text, projects)
    requirement_queries = extract_requirement_queries(
        title,
        description,
        max_queries=cfg["max_requirement_queries"],
    )
    candidate_matrix: dict[str, dict[str, Any]] = {}
    query_cache: dict[str, tuple[list[tuple[str, float]], list[tuple[str, float]]]] = {}
    fallback_reasons: list[dict[str, str]] = []
    stage_counts: list[dict[str, Any]] = []

    for requirement in requirement_queries:
        requirement_id = requirement["requirement_id"]
        query_text = requirement["query"]
        normalized_query = query_text.casefold()
        if normalized_query in query_cache:
            bm25_hits, vector_hits = query_cache[normalized_query]
        else:
            fts_query = _sanitize_fts_query(query_text)
            with span("bm25_search", user_id=user_id, requirement_id=requirement_id):
                bm25_hits = (
                    evidence_index_store.bm25_search(
                        user_id, fts_query, cfg["bm25_top_k"]
                    )
                    if fts_query
                    else []
                )
            vector_hits: list[tuple[str, float]] = []
            try:
                if settings.dashscope_api_key:
                    with span(
                        "embed_query",
                        user_id=user_id,
                        requirement_id=requirement_id,
                        model=settings.embedding_model,
                    ):
                        query_vec, _ = embedding_client.embed_query(query_text)
                else:
                    query_vec = _pseudo_query_vector(query_text)
                with span(
                    "faiss_search",
                    user_id=user_id,
                    requirement_id=requirement_id,
                ):
                    vector_hits = faiss_index.vector_search(
                        user_id, query_vec, cfg["vector_top_k"]
                    )
            except Exception as exc:
                logger.warning(
                    "Vector search failed for requirement %s: %s",
                    requirement_id,
                    exc,
                )
                fallback_reasons.append(
                    {"requirement_id": requirement_id, "stage": "vector", "reason": type(exc).__name__}
                )
            query_cache[normalized_query] = (bm25_hits, vector_hits)

        with span("rrf_fusion", user_id=user_id, requirement_id=requirement_id):
            fused = _rrf_fuse([bm25_hits, vector_hits], rrf_k=cfg["rrf_k"])
        fused = fused[: cfg["candidates_per_requirement"]]
        candidate_ids = [chunk_id for chunk_id, _ in fused]
        chunks = evidence_index_store.get_chunks_by_ids(user_id, candidate_ids)
        by_id = {chunk["id"]: chunk for chunk in chunks}
        ordered = [by_id[chunk_id] for chunk_id in candidate_ids if chunk_id in by_id]
        rerank_scores: dict[str, tuple[int, float]] = {}
        if ordered:
            try:
                reranked = embedding_client.rerank_documents(
                    query_text,
                    [chunk["content"] for chunk in ordered][
                        : cfg["rerank_candidates_per_requirement"]
                    ],
                    top_n=min(
                        settings.rerank_top_n,
                        cfg["rerank_candidates_per_requirement"],
                    ),
                )
                for rank, (document_index, score) in enumerate(reranked, start=1):
                    if document_index < len(ordered):
                        rerank_scores[ordered[document_index]["id"]] = (rank, float(score))
            except Exception as exc:
                fallback_reasons.append(
                    {"requirement_id": requirement_id, "stage": "rerank", "reason": type(exc).__name__}
                )

        bm25_rank = {chunk_id: rank for rank, (chunk_id, _) in enumerate(bm25_hits, 1)}
        vector_rank = {chunk_id: rank for rank, (chunk_id, _) in enumerate(vector_hits, 1)}
        fused_scores = dict(fused)
        for fused_rank, chunk_id in enumerate(candidate_ids, start=1):
            chunk = by_id.get(chunk_id)
            if not chunk:
                continue
            entry = candidate_matrix.setdefault(
                chunk_id,
                {
                    **chunk,
                    "requirement_ids": set(),
                    "per_requirement": {},
                    "best_retrieval_score": 0.0,
                    "content_fingerprint": _content_fingerprint(chunk.get("content") or ""),
                },
            )
            rerank_rank, rerank_score = rerank_scores.get(
                chunk_id, (None, fused_scores.get(chunk_id, 0.0))
            )
            entry["requirement_ids"].add(requirement_id)
            entry["per_requirement"][requirement_id] = {
                "bm25_rank": bm25_rank.get(chunk_id),
                "vector_rank": vector_rank.get(chunk_id),
                "rrf_rank": fused_rank,
                "rrf_score": fused_scores.get(chunk_id, 0.0),
                "rerank_rank": rerank_rank,
                "rerank_score": rerank_score,
            }
            entry["best_retrieval_score"] = max(
                float(entry["best_retrieval_score"]), float(rerank_score)
            )
        stage_counts.append(
            {
                "requirement_id": requirement_id,
                "bm25": len(bm25_hits),
                "vector": len(vector_hits),
                "fused": len(fused),
                "reranked": len(rerank_scores),
            }
        )

    layer2b, deduplication_removals = _pack_for_coverage(
        list(candidate_matrix.values()), requirement_queries, cfg
    )
    packed_requirement_ids = {
        requirement_id
        for chunk in layer2b
        for requirement_id in chunk["requirement_ids"]
    }
    nonfallback_ids = {
        item["requirement_id"]
        for item in requirement_queries
        if not item.get("is_fallback")
    }
    candidate_project_ids = sorted(
        {
            chunk.get("project_id")
            for chunk in candidate_matrix.values()
            if chunk.get("project_id")
        }
    )
    packed_project_ids = sorted(
        {chunk["project_id"] for chunk in layer2b if chunk.get("project_id")}
    )

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
            "candidate_project_ids": candidate_project_ids,
            "packed_project_ids": packed_project_ids,
            "packed_chunk_ids": [chunk["source_id"] for chunk in layer2b],
            "requirement_queries": requirement_queries,
            "requirement_coverage": {
                requirement_id: [
                    chunk["source_id"]
                    for chunk in layer2b
                    if requirement_id in chunk["requirement_ids"]
                ]
                for requirement_id in nonfallback_ids
            },
            "uncovered_requirement_ids": sorted(
                nonfallback_ids - packed_requirement_ids
            ),
            "stage_counts": stage_counts,
            "deduplication_removals": deduplication_removals,
            "fallback_reasons": fallback_reasons,
        },
    }


def _pseudo_query_vector(query: str) -> list[float]:
    import numpy as np

    dim = settings.embedding_dimensions
    seed = abs(hash(query)) % (2**32)
    rng = np.random.default_rng(seed)
    return rng.standard_normal(dim).astype(np.float32).tolist()
