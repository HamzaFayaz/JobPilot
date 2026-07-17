"""Deterministic application-result validation and fit classification node."""

from __future__ import annotations

import copy
from datetime import date
from typing import Any

from backend.app.config import settings
from backend.app.graph.subgraphs.application.state import ApplicationState
from backend.app.services.application_scoring import (
    SCORING_POLICY_VERSION,
    rebuild_narrative,
    score_requirements,
    suggested_statuses,
)
from backend.app.services.application_validation import (
    direct_support,
    normalize_whitespace,
    quote_is_contained,
    valid_cv_references,
    validate_non_cv_reference,
)
from backend.app.services.date_tenure import completed_months, required_months


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
        "swap_coverage": [],
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
    """Enforce source boundaries, swap validity, scores, and narrative."""
    if state.get("error") or not state.get("enrich_result"):
        return {"stage_status": "classification_skipped"}

    result = copy.deepcopy(state["enrich_result"])
    context = state.get("validation_context") or {}
    corrections: list[dict] = []
    proposed_scores = {
        "current_cv_score": result.get("current_cv_score"),
        "suggested_cv_score": result.get("suggested_cv_score"),
    }
    job_description = context.get("job_description") or (
        state.get("job") or {}
    ).get("description_text") or ""
    cv_text = context.get("cv_text") or (state.get("profile") or {}).get("cv_text") or ""
    run_date = date.fromisoformat(context.get("run_date") or date.today().isoformat())
    cv_months = completed_months(cv_text, run_date)
    requirements: list[dict] = []
    seen_requirements: set[str] = set()
    for requirement in result.get("explicit_requirements") or []:
        requirement_id = requirement.get("requirement_id")
        job_quote = requirement.get("job_quote") or requirement.get("text") or ""
        duplicate_key = normalize_whitespace(job_quote).casefold()
        if (
            not requirement_id
            or duplicate_key in seen_requirements
            or not quote_is_contained(job_quote, job_description)
        ):
            _correction(
                corrections,
                "invalid_or_duplicate_requirement_removed",
                requirement_id=requirement_id,
            )
            continue
        seen_requirements.add(duplicate_key)
        valid_refs = valid_cv_references(
            requirement.get("evidence_refs") or [],
            context,
        )
        if len(valid_refs) != len(requirement.get("evidence_refs") or []):
            _correction(
                corrections,
                "invalid_requirement_evidence_removed",
                requirement_id=requirement_id,
            )
        requirement["evidence_refs"] = valid_refs
        if requirement.get("status") in ("matched", "partial") and not valid_refs:
            requirement["status"] = "not_evidenced"
            _correction(
                corrections,
                "requirement_missing_cv_evidence",
                requirement_id=requirement_id,
            )
        tenure_needed = required_months(job_quote)
        if tenure_needed is not None and requirement["status"] in ("matched", "partial"):
            deterministic_status = (
                "matched"
                if cv_months >= tenure_needed
                else "partial"
                if cv_months > 0
                else "not_evidenced"
            )
            if deterministic_status != requirement["status"]:
                _correction(
                    corrections,
                    "tenure_status_corrected",
                    requirement_id=requirement_id,
                    completed_months=cv_months,
                    required_months=tenure_needed,
                )
                requirement["status"] = deterministic_status
        requirements.append(requirement)
    result["explicit_requirements"] = requirements
    requirements_by_id = {
        requirement["requirement_id"]: requirement for requirement in requirements
    }

    slots = sorted(
        context.get("cv_project_slots") or [], key=lambda item: item["slot_index"]
    )
    slot_ids = {slot["slot_index"] for slot in slots}
    portfolio_ids = set(context.get("portfolio_project_ids") or [])
    cv_project_ids = set(context.get("cv_project_ids") or [])
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
        current_id = slot.get("matched_portfolio_project_id")
        replacement_valid = (
            replacement_id in portfolio_ids
            and replacement_id != current_id
            and replacement_id not in used_replacements
            and replacement_id not in cv_project_ids
        )
        if not replacement_valid:
            accepted.append(
                _keep_decision(slot, "Invalid replacement was corrected to keep.")
            )
            _correction(
                corrections, "invalid_swap_forced_keep", slot_index=slot_index
            )
            continue
        valid_coverage: list[dict[str, Any]] = []
        for coverage in decision.get("swap_coverage") or []:
            requirement_id = coverage.get("requirement_id")
            requirement = requirements_by_id.get(requirement_id)
            references = coverage.get("evidence_refs") or []
            valid_references = [
                reference
                for reference in references
                if validate_non_cv_reference(
                    reference,
                    context,
                    project_id=replacement_id,
                )
                and direct_support(
                    requirement.get("job_quote") or requirement.get("text") or "",
                    reference.get("quote") or "",
                )
            ] if requirement else []
            if (
                not requirement
                or requirement.get("status") not in ("partial", "not_evidenced")
                or not valid_references
                or sum(len(reference["quote"]) for reference in valid_references)
                > int(slot.get("character_budget") or slot.get("chars_budget") or 200)
            ):
                _correction(
                    corrections,
                    "invalid_swap_target_removed",
                    slot_index=slot_index,
                    requirement_id=requirement_id,
                )
                continue
            valid_coverage.append(
                {
                    "requirement_id": requirement_id,
                    "proposed_status": coverage.get("proposed_status") or "partial",
                    "evidence_refs": valid_references,
                }
            )
        if not valid_coverage:
            accepted.append(
                _keep_decision(slot, "No swap target had direct replacement evidence.")
            )
            _correction(corrections, "invalid_swap_forced_keep", slot_index=slot_index)
            continue
        used_replacements.add(replacement_id)
        decision["current_project_name"] = slot.get("cv_project_name") or ""
        decision["swap_coverage"] = valid_coverage
        decision["target_requirement_ids"] = [
            coverage["requirement_id"] for coverage in valid_coverage
        ]
        decision["evidence_refs"] = [
            reference
            for coverage in valid_coverage
            for reference in coverage["evidence_refs"]
        ]
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
    else:
        result["current_cv_score"] = score_requirements(requirements)
        result["suggested_cv_score"] = max(
            result["current_cv_score"],
            score_requirements(
                requirements,
                status_overrides=suggested_statuses(result["project_decisions"]),
            ),
        )
        if proposed_scores != {
            "current_cv_score": result["current_cv_score"],
            "suggested_cv_score": result["suggested_cv_score"],
        }:
            _correction(
                corrections,
                "scores_recomputed",
                proposed=proposed_scores,
                final={
                    "current_cv_score": result["current_cv_score"],
                    "suggested_cv_score": result["suggested_cv_score"],
                },
                policy=SCORING_POLICY_VERSION,
            )
        rebuild_narrative(result, materially_corrected=bool(corrections))

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
