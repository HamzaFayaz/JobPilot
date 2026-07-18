"""Deterministic fit scoring and corrected narrative construction."""

from __future__ import annotations

from typing import Any

SCORING_POLICY_VERSION = "weighted_requirements_v1"
IMPORTANCE_WEIGHT = {"required": 3, "preferred": 2, "general": 1}
STATUS_CREDIT = {
    "matched": 1.0,
    "partial": 0.5,
    "not_evidenced": 0.0,
    "cannot_assess": 0.0,
}


def score_requirements(
    requirements: list[dict[str, Any]],
    *,
    status_overrides: dict[str, str] | None = None,
) -> int:
    status_overrides = status_overrides or {}
    total_weight = sum(
        IMPORTANCE_WEIGHT.get(requirement.get("importance", "general"), 1)
        for requirement in requirements
    )
    if not total_weight:
        return 0
    earned = 0.0
    for requirement in requirements:
        weight = IMPORTANCE_WEIGHT.get(requirement.get("importance", "general"), 1)
        status = status_overrides.get(
            requirement.get("requirement_id"), requirement.get("status")
        )
        earned += weight * STATUS_CREDIT.get(status, 0.0)
    return round(100 * earned / total_weight)


def suggested_statuses(decisions: list[dict[str, Any]]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for decision in decisions:
        if decision.get("action") != "swap":
            continue
        for coverage in decision.get("swap_coverage") or []:
            requirement_id = coverage.get("requirement_id")
            proposed = coverage.get("proposed_status")
            if not requirement_id or proposed not in ("partial", "matched"):
                continue
            if proposed == "matched" or requirement_id not in overrides:
                overrides[requirement_id] = proposed
    return overrides


def rebuild_narrative(result: dict[str, Any], *, materially_corrected: bool) -> None:
    requirements = result.get("explicit_requirements") or []
    matched = [item for item in requirements if item.get("status") == "matched"]
    partial = [item for item in requirements if item.get("status") == "partial"]
    gaps = [
        item
        for item in requirements
        if item.get("status") in ("not_evidenced", "cannot_assess")
    ]
    current = result.get("current_cv_score")
    suggested = result.get("suggested_cv_score")
    swaps = [item for item in result.get("project_decisions") or [] if item["action"] == "swap"]

    result["current_score_rationale"] = (
        f"Validated current-CV evidence fully matches {len(matched)} requirement(s), "
        f"partially matches {len(partial)}, and does not evidence {len(gaps)}."
    )
    if swaps:
        covered = {
            item.get("requirement_id")
            for decision in swaps
            for item in decision.get("swap_coverage") or []
        }
        result["suggested_score_rationale"] = (
            f"{len(swaps)} validated project swap(s) add direct evidence for "
            f"{len(covered)} requirement(s), changing visible fit from "
            f"{current}/100 to {suggested}/100."
        )
    else:
        result["suggested_score_rationale"] = (
            "No validated project swap adds requirement coverage; the suggested "
            "score equals the current score."
        )
    for decision in result.get("project_decisions") or []:
        if decision["action"] == "keep":
            decision["rationale"] = "Keep this slot because no validated replacement adds direct unmet-requirement evidence."
        else:
            targets = ", ".join(decision.get("target_requirement_ids") or [])
            decision["rationale"] = (
                f"Swap in {decision.get('swap_in_project_name')} because supplied "
                f"project evidence directly supports: {targets}."
            )
    limitations = []
    if gaps:
        limitations.append(
            "The submitted CV does not visibly evidence every disclosed requirement."
        )
    if materially_corrected:
        limitations.append(
            "Model-proposed claims or decisions were corrected against supplied sources."
        )
        if result.get("confidence") == "high":
            result["confidence"] = "medium"
        elif result.get("confidence") == "medium":
            result["confidence"] = "low"
    result["limitations"] = limitations
    strongest = matched[0].get("text") if matched else "No requirement is fully evidenced"
    gap = gaps[0].get("text") if gaps else "No disclosed gap remains"
    result["summary"] = (
        f"Strongest visible alignment: {strongest}. Main gap or uncertainty: {gap}. "
        f"Validated fit is {current}/100"
        + (f", improving to {suggested}/100 with the recommended swaps." if swaps else ".")
    )
