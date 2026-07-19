"""Orchestrate suggested-CV generation for one job package."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from backend.app.config import settings
from backend.app.db import get_connection
from backend.app.services.cv_layout_contract import build_layout_contracts_for_swaps
from backend.app.services.cv_project_slots import parse_cv_project_slots
from backend.app.services.edit_cv import apply_slot_replacements
from backend.app.services.evidence_index_store import list_project_chunks
from backend.app.services.profile_store import get_cv_text, get_profile, get_stored_projects
from backend.app.services.suggested_cv_store import (
    drafts_dir,
    insert_draft,
    next_suggested_cv_filename,
)
from backend.app.services.tailor_cv_llm import TailorCvError, generate_suggested_slot_text

logger = logging.getLogger(__name__)

_DEFINITION_HEADING_HINTS = (
    "overview",
    "features",
    "engineering highlights",
    "agentic architecture",
    "architecture",
    "what it does",
    "product",
)
_MAX_DEFINITION_CHUNKS = 3
_MAX_JOB_TARGETED_CHUNKS = 4
_MAX_EVIDENCE_TOTAL = 8


def _chunk_to_evidence(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": chunk.get("source_id") or chunk.get("id"),
        "heading_path": chunk.get("heading_path"),
        "content": chunk.get("content") or "",
    }


def _is_definition_chunk(chunk: dict[str, Any]) -> bool:
    heading = str(chunk.get("heading_path") or "").casefold()
    # Prefer section roots / short product-definition paths; skip deep mermaid dumps.
    content = str(chunk.get("content") or "")
    if "```mermaid" in content and len(content) > 400:
        return False
    return any(hint in heading for hint in _DEFINITION_HEADING_HINTS)


def _project_evidence_payload(
    *,
    user_id: int,
    project_ids: list[str],
    analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build tailor evidence: definition chunks first, then job-targeted ones."""
    stored = {p.id: p for p in get_stored_projects(user_id)}
    bundle = analysis.get("retrieval_bundle") or {}
    analysis_chunks = bundle.get("layer2b_readme_chunks") or []
    payloads: list[dict[str, Any]] = []

    for project_id in project_ids:
        project = stored.get(project_id)
        stored_chunks = list_project_chunks(user_id, project_id)
        definition = [
            _chunk_to_evidence(chunk)
            for chunk in stored_chunks
            if _is_definition_chunk(chunk)
        ][:_MAX_DEFINITION_CHUNKS]

        # If heading filter missed, fall back to earliest non-diagram chunks.
        if not definition:
            for chunk in stored_chunks:
                content = str(chunk.get("content") or "")
                if "```mermaid" in content and len(content) > 400:
                    continue
                definition.append(_chunk_to_evidence(chunk))
                if len(definition) >= _MAX_DEFINITION_CHUNKS:
                    break

        seen_ids = {
            str(item.get("source_id") or "")
            for item in definition
            if item.get("source_id")
        }
        job_targeted: list[dict[str, Any]] = []
        for chunk in analysis_chunks:
            if not isinstance(chunk, dict):
                continue
            if str(chunk.get("project_id") or "") != project_id:
                continue
            source_id = str(chunk.get("source_id") or "")
            if source_id and source_id in seen_ids:
                continue
            item = {
                "source_id": chunk.get("source_id"),
                "heading_path": chunk.get("heading_path"),
                "content": chunk.get("content") or "",
            }
            job_targeted.append(item)
            if source_id:
                seen_ids.add(source_id)
            if len(job_targeted) >= _MAX_JOB_TARGETED_CHUNKS:
                break

        evidence = (definition + job_targeted)[:_MAX_EVIDENCE_TOTAL]
        overview = ""
        name = project_id
        if project is not None:
            name = project.name
            overview = project.portfolio_overview or project.description or ""
            if project.evidence_card is not None and not evidence:
                evidence.append(
                    {
                        "source_id": f"evidence_card:{project_id}",
                        "heading_path": "evidence_card",
                        "content": json.dumps(
                            project.evidence_card.model_dump(by_alias=False),
                            ensure_ascii=False,
                        ),
                    }
                )
        payloads.append(
            {
                "project_id": project_id,
                "name": name,
                "overview": overview,
                "evidence": evidence,
            }
        )
    return payloads


def get_cv_path(user_id: int) -> Path | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT cv_path FROM profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
    if not row or not row["cv_path"]:
        return None
    path = Path(str(row["cv_path"]))
    return path if path.exists() else None


def _load_package(user_id: int, package_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, title, company, url, platform, description_text,
                   analysis_json, status
            FROM job_packages
            WHERE id = ? AND user_id = ?
            """,
            (package_id, user_id),
        ).fetchone()
    if row is None:
        return None
    return {
        "id": int(row["id"]),
        "title": row["title"] or "",
        "company": row["company"] or "",
        "url": row["url"] or "",
        "platform": row["platform"] or "linkedin",
        "description_text": row["description_text"] or "",
        "analysis": json.loads(row["analysis_json"] or "{}"),
        "status": row["status"] or "ready",
    }


def _classified_result(analysis: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "accepted_user_facing_result",
        "classified_result",
        "accepted_model_result",
        "enrich_result",
    ):
        value = analysis.get(key)
        if isinstance(value, dict) and value.get("project_decisions") is not None:
            return value
    return {}


def _requirement_text_map(classified: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in classified.get("explicit_requirements") or []:
        if not isinstance(item, dict):
            continue
        req_id = str(item.get("requirement_id") or "")
        text = str(item.get("text") or item.get("job_quote") or "")
        if req_id:
            mapping[req_id] = text
    return mapping


def generate_suggested_cv(
    *,
    user_id: int,
    package_id: int,
    approved_slot_indexes: list[int],
) -> dict[str, Any]:
    """Generate a suggested CV draft for approved swap slots. Master CV untouched."""
    if not approved_slot_indexes:
        raise TailorCvError("no_slots", "Select at least one swap slot to generate.")

    package = _load_package(user_id, package_id)
    if package is None:
        raise TailorCvError("not_found", "Job package not found.")
    if package["status"] not in {"ready", "applied", "skipped"}:
        raise TailorCvError(
            "not_ready",
            "Job analysis must finish before generating a suggested CV.",
        )

    cv_path = get_cv_path(user_id)
    if cv_path is None:
        raise TailorCvError("missing_cv", "Upload a .docx CV before generating.")

    classified = _classified_result(package["analysis"])
    decisions = classified.get("project_decisions") or []
    decision_by_slot = {
        int(item["slot_index"]): item
        for item in decisions
        if isinstance(item, dict) and "slot_index" in item
    }

    approved_swaps: list[dict[str, Any]] = []
    req_texts = _requirement_text_map(classified)
    for slot_index in approved_slot_indexes:
        decision = decision_by_slot.get(int(slot_index))
        if decision is None:
            raise TailorCvError(
                "unknown_slot",
                f"Slot {slot_index} is not in this job's project decisions.",
            )
        if decision.get("action") != "swap":
            raise TailorCvError(
                "not_swap",
                f"Slot {slot_index} is keep — only swap slots can be generated in v1.",
            )
        if not decision.get("swap_in_project_id"):
            raise TailorCvError(
                "missing_swap_in",
                f"Slot {slot_index} is missing swap_in_project_id.",
            )
        target_ids = [str(x) for x in (decision.get("target_requirement_ids") or [])]
        approved_swaps.append(
            {
                "slot_index": int(slot_index),
                "action": "swap",
                "current_project_name": decision.get("current_project_name"),
                "swap_in_project_id": decision.get("swap_in_project_id"),
                "swap_in_project_name": decision.get("swap_in_project_name"),
                "target_requirement_ids": target_ids,
                "target_requirement_texts": [
                    req_texts.get(req_id, req_id) for req_id in target_ids
                ],
                "rationale": decision.get("rationale") or "",
            }
        )

    portfolio = [
        {
            "id": p.id,
            "name": p.name,
            "repo_full_name": p.repo_full_name,
            "repo_name": (p.repo_full_name or "").split("/")[-1] if p.repo_full_name else None,
        }
        for p in get_stored_projects(user_id)
    ]
    cv_text = get_cv_text(user_id)
    cv_slots = parse_cv_project_slots(cv_text, portfolio)
    layout_slots = build_layout_contracts_for_swaps(
        cv_slots=cv_slots,
        approved_slot_indexes=[int(s["slot_index"]) for s in approved_swaps],
        docx_path=cv_path,
    )

    for layout in layout_slots:
        targets = layout.get("docx_targets") or {}
        if targets.get("title_paragraph_index") is None:
            raise TailorCvError(
                "layout_map_failed",
                "Could not map a project title to the CV .docx. "
                "Use a clear Projects section with title + bullets.",
            )
        item_indexes = targets.get("item_paragraph_indexes") or []
        if any(index is None for index in item_indexes):
            raise TailorCvError(
                "layout_map_failed",
                "Could not map all project lines to the CV .docx paragraphs.",
            )

    project_ids = [
        str(item["swap_in_project_id"]) for item in approved_swaps if item.get("swap_in_project_id")
    ]
    projects = _project_evidence_payload(
        user_id=user_id,
        project_ids=list(dict.fromkeys(project_ids)),
        analysis=package["analysis"],
    )

    generated, auto_shortened, debug = generate_suggested_slot_text(
        user_id=user_id,
        job={
            "title": package["title"],
            "company": package["company"],
            "description_text": package["description_text"],
        },
        approved_swaps=approved_swaps,
        layout_slots=layout_slots,
        projects=projects,
    )

    draft_name = next_suggested_cv_filename(
        user_id, get_profile(user_id).cv_filename
    )
    dest = drafts_dir(user_id) / draft_name
    apply_slot_replacements(
        source_docx=cv_path,
        dest_docx=dest,
        layout_slots=layout_slots,
        generated_slots=generated.get("slots") or [],
    )

    debug_dir = settings.data_dir / "suggested_cv_debug" / str(user_id)
    debug_dir.mkdir(parents=True, exist_ok=True)
    debug_path = debug_dir / f"{dest.stem}.json"
    debug_payload = {
        **debug,
        "package_id": package_id,
        "approved_swaps": approved_swaps,
        "layout_slots": layout_slots,
        "projects": projects,
        "final_generated": generated,
        "auto_shortened": auto_shortened,
        "draft_docx": str(dest),
    }
    debug_path.write_text(
        json.dumps(debug_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(
        "tailor_cv draft saved package_id=%s draft=%s debug=%s outcome=%s",
        package_id,
        dest,
        debug_path,
        debug.get("outcome"),
    )

    draft_id = insert_draft(
        user_id=user_id,
        package_id=package_id,
        filename=draft_name,
        path=str(dest),
        approved_slot_indexes=[int(s["slot_index"]) for s in approved_swaps],
        auto_shortened=auto_shortened,
        model_name=settings.tailor_cv_model,
        prompt_version=settings.tailor_cv_prompt_version,
        generated_json=generated,
    )
    return {
        "draftId": draft_id,
        "filename": draft_name,
        "autoShortened": auto_shortened,
        "approvedSlotIndexes": [int(s["slot_index"]) for s in approved_swaps],
        "downloadPath": f"/api/jobs/{package_id}/suggested-cv/{draft_id}/download",
    }
