"""Deterministic application-result validation and fit classification node."""

from __future__ import annotations

import copy
from typing import Any

from backend.app.config import settings
from backend.app.graph.subgraphs.application.state import ApplicationState


def _correction(corrections: list[dict], code: str, **details: Any) -> None:
    corrections.append({"code": code, **details})


def _keep_decision(slot: dict[str, Any], rationale: str) -> dict[str, Any]:
    return {
        "slot_index": int(slot["slot_index"]),
        "action": "keep",
        "current_project_name": slot.get("cv_project_name") or "",
        "swap_in_project_id": None,
        "swap_in_project_name": None,
        "target_requirement_ids": [],
        "evidence_refs": [],
        "rationale": rationale,
        "impact": None,
    }


def _fit_fields(score: int | None) -> tuple[bool | None, str, str]:
    if score is None:
        return None, "insufficient", "The listing has insufficient detail for a fit score."
    passes = score >= settings.application_fit_threshold
    if score >= 75:
        tier = "strong"
    elif score >= 60:
        tier = "moderate"
    elif score >= 45:
        tier = "weak"
    else:
        tier = "not_recommended"
    return passes, tier, f"Current visible CV fit is {tier.replace('_', ' ')} ({score}/100)."


def classify_fit(state: ApplicationState) -> dict:
    """Apply objective input-dependent corrections without an LLM call."""
    if state.get("error") or not state.get("enrich_result"):
        return {"stage_status": "classification_skipped"}

    result = copy.deepcopy(state["enrich_result"])
    context = state.get("validation_context") or {}
    corrections: list[dict] = []

    for field in ("current_cv_score", "suggested_cv_score"):
        score = result.get(field)
        if score is not None:
            clamped = max(0, min(100, int(score)))
            if clamped != score:
                _correction(
                    corrections,
                    "score_clamped",
                    field=field,
                    before=score,
                    after=clamped,
                )
            result[field] = clamped

    requirements: list[dict] = []
    seen_requirement_ids: set[str] = set()
    for requirement in result.get("explicit_requirements") or []:
        requirement_id = requirement.get("requirement_id")
        if not requirement_id or requirement_id in seen_requirement_ids:
            _correction(
                corrections,
                "duplicate_requirement_removed",
                requirement_id=requirement_id,
            )
            continue
        seen_requirement_ids.add(requirement_id)
        if requirement.get("status") in ("matched", "partial") and not any(
            ref.get("source_type") == "cv"
            for ref in requirement.get("evidence_refs") or []
        ):
            requirement["status"] = "not_evidenced"
            requirement["evidence_refs"] = []
            _correction(
                corrections,
                "requirement_missing_cv_evidence",
                requirement_id=requirement_id,
            )
        requirements.append(requirement)
    result["explicit_requirements"] = requirements

    slots = sorted(
        context.get("cv_project_slots") or [], key=lambda item: item["slot_index"]
    )
    slot_ids = {slot["slot_index"] for slot in slots}
    portfolio_ids = set(context.get("portfolio_project_ids") or [])
    evidence_sources = context.get("evidence_sources") or {}
    submitted_by_slot: dict[int, dict] = {}
    for decision in result.get("project_decisions") or []:
        slot_index = decision.get("slot_index")
        if slot_index not in slot_ids:
            _correction(
                corrections, "invalid_slot_decision_removed", slot_index=slot_index
            )
            continue
        if slot_index in submitted_by_slot:
            _correction(
                corrections, "duplicate_slot_decision_removed", slot_index=slot_index
            )
            continue
        submitted_by_slot[slot_index] = decision

    accepted: list[dict] = []
    used_replacements: set[str] = set()
    for slot in slots:
        slot_index = slot["slot_index"]
        decision = submitted_by_slot.get(slot_index)
        if decision is None:
            accepted.append(
                _keep_decision(slot, "No valid model decision was supplied.")
            )
            _correction(
                corrections, "missing_slot_added_as_keep", slot_index=slot_index
            )
            continue
        if decision.get("action") == "keep":
            accepted.append(
                _keep_decision(
                    slot, decision.get("rationale") or "Keep current project."
                )
            )
            continue

        replacement_id = decision.get("swap_in_project_id")
        target_ids = set(decision.get("target_requirement_ids") or [])
        evidence_refs = decision.get("evidence_refs") or []
        current_id = slot.get("matched_portfolio_project_id")
        evidence_valid = any(
            ref.get("source_id") in evidence_sources
            and evidence_sources[ref["source_id"]].get("project_id")
            == replacement_id
            for ref in evidence_refs
        )
        valid = (
            replacement_id in portfolio_ids
            and replacement_id != current_id
            and replacement_id not in used_replacements
            and bool(target_ids & seen_requirement_ids)
            and evidence_valid
        )
        if not valid:
            accepted.append(
                _keep_decision(slot, "Invalid replacement was corrected to keep.")
            )
            _correction(
                corrections, "invalid_swap_forced_keep", slot_index=slot_index
            )
            continue
        used_replacements.add(replacement_id)
        decision["current_project_name"] = slot.get("cv_project_name") or ""
        accepted.append(decision)
    result["project_decisions"] = accepted

    if result.get("analysis_status") == "insufficient_job_detail":
        result["current_cv_score"] = None
        result["suggested_cv_score"] = None
        result["confidence"] = "low"
        result["project_decisions"] = [
            _keep_decision(slot, "The listing has insufficient detail.")
            for slot in slots
        ]
    elif all(item["action"] == "keep" for item in accepted):
        result["suggested_cv_score"] = result.get("current_cv_score")
    elif (
        result.get("current_cv_score") is not None
        and result.get("suggested_cv_score") is not None
        and result["suggested_cv_score"] < result["current_cv_score"]
    ):
        result["suggested_cv_score"] = result["current_cv_score"]
        _correction(corrections, "suggested_score_raised_to_current")

    passes, tier, message = _fit_fields(result.get("current_cv_score"))
    result.update(
        {
            "passes_threshold": passes,
            "fit_tier": tier,
            "fit_message": message,
            "corrections": corrections,
        }
    )
    return {"classified_result": result, "stage_status": "classified"}
