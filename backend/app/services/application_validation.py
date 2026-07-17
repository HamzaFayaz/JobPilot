"""Source-boundary and swap validation helpers."""

from __future__ import annotations

import re
from typing import Any

from backend.app.services.date_tenure import required_months

STOPWORDS = {
    "and", "the", "with", "for", "from", "that", "this", "have", "will",
    "your", "you", "our", "are", "into", "using", "required", "preferred",
    "experience", "knowledge", "ability", "work",
}
TECH_ALIASES = (
    {"aws", "amazon web services"},
    {"azure ai foundry", "ai foundry"},
    {"azure openai", "openai on azure"},
    {"whatsapp business api", "whatsapp api"},
    {"step functions", "aws step functions"},
    {"langgraph", "lang graph"},
)


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def quote_is_contained(quote: str, source: str) -> bool:
    return bool(quote.strip()) and normalize_whitespace(quote).casefold() in normalize_whitespace(source).casefold()


def meaning_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9+#.]+", text.casefold())
        if len(token) >= 2 and token not in STOPWORDS
    }


def direct_support(requirement: str, evidence: str) -> bool:
    requirement_normalized = normalize_whitespace(requirement).casefold()
    evidence_normalized = normalize_whitespace(evidence).casefold()
    for aliases in TECH_ALIASES:
        if any(alias in requirement_normalized for alias in aliases):
            return any(alias in evidence_normalized for alias in aliases)
    required = meaning_tokens(requirement)
    evidenced = meaning_tokens(evidence)
    if not required:
        return False
    overlap = required & evidenced
    return len(overlap) >= min(2, len(required)) and len(overlap) / len(required) >= 0.25


def validate_non_cv_reference(
    reference: dict[str, Any],
    context: dict[str, Any],
    *,
    project_id: str | None = None,
) -> bool:
    source = (context.get("evidence_sources") or {}).get(reference.get("source_id"))
    if not source:
        return False
    return (
        source.get("source_type") == reference.get("source_type")
        and (project_id is None or source.get("project_id") == project_id)
        and quote_is_contained(reference.get("quote") or "", source.get("content") or "")
    )


def valid_cv_references(
    references: list[dict[str, Any]],
    context: dict[str, Any],
) -> list[dict[str, Any]]:
    cv_text = context.get("cv_text") or ""
    return [
        reference
        for reference in references
        if reference.get("source_type") == "cv"
        and quote_is_contained(reference.get("quote") or "", cv_text)
    ]


def validate_application_contract(
    result: dict[str, Any],
    context: dict[str, Any],
) -> list[dict[str, Any]]:
    """Validate identity, boundaries, swaps, dates, and score invariants."""
    errors: list[dict[str, Any]] = []
    job_description = context.get("job_description") or ""
    cv_sources = context.get("cv_evidence_sources") or {}
    portfolio_sources = context.get("evidence_sources") or {}
    date_fact_ids = {
        item.get("date_fact_id") for item in context.get("date_facts") or []
    }
    requirements = result.get("explicit_requirements") or []
    requirements_by_id: dict[str, dict[str, Any]] = {}

    for requirement in requirements:
        requirement_id = requirement.get("requirement_id")
        if not requirement_id or requirement_id in requirements_by_id:
            errors.append(
                {"code": "duplicate_or_missing_requirement_id", "requirement_id": requirement_id}
            )
            continue
        requirements_by_id[requirement_id] = requirement
        start = requirement.get("job_source_start")
        end = requirement.get("job_source_end")
        quote = requirement.get("job_quote") or ""
        if (
            not isinstance(start, int)
            or not isinstance(end, int)
            or start < 0
            or end <= start
            or end > len(job_description)
            or job_description[start:end] != quote
        ):
            errors.append(
                {"code": "invalid_job_source_range", "requirement_id": requirement_id}
            )
        valid_cv_count = 0
        for reference in requirement.get("evidence_refs") or []:
            span_id = reference.get("cv_span_id")
            if reference.get("source_type") != "cv" or span_id not in cv_sources:
                errors.append(
                    {"code": "invalid_current_cv_source", "requirement_id": requirement_id}
                )
            else:
                valid_cv_count += 1
        if requirement.get("status") in {"matched", "partial"} and valid_cv_count == 0:
            errors.append(
                {"code": "supported_status_without_cv_span", "requirement_id": requirement_id}
            )
        supplied_date_ids = set(requirement.get("date_fact_ids") or [])
        if not supplied_date_ids <= date_fact_ids:
            errors.append(
                {"code": "unknown_date_fact", "requirement_id": requirement_id}
            )
        if (
            required_months(quote) is not None
            and requirement.get("status") != "cannot_assess"
            and not supplied_date_ids
        ):
            errors.append(
                {"code": "tenure_assessment_without_date_fact", "requirement_id": requirement_id}
            )

    slots = sorted(
        context.get("cv_project_slots") or [], key=lambda item: item.get("slot_index", -1)
    )
    decisions = result.get("project_decisions") or []
    expected_slots = [item.get("slot_index") for item in slots]
    actual_slots = [item.get("slot_index") for item in decisions]
    if actual_slots != expected_slots:
        errors.append(
            {
                "code": "project_decisions_do_not_match_slots",
                "expected": expected_slots,
                "actual": actual_slots,
            }
        )

    portfolio_ids = set(context.get("portfolio_project_ids") or [])
    cv_project_ids = set(context.get("cv_project_ids") or [])
    used_replacements: set[str] = set()
    slot_by_index = {item.get("slot_index"): item for item in slots}
    for decision in decisions:
        if decision.get("action") != "swap":
            continue
        slot = slot_by_index.get(decision.get("slot_index")) or {}
        replacement_id = decision.get("swap_in_project_id")
        if (
            replacement_id not in portfolio_ids
            or replacement_id == slot.get("matched_portfolio_project_id")
            or replacement_id in cv_project_ids
            or replacement_id in used_replacements
        ):
            errors.append(
                {"code": "invalid_replacement_project", "slot_index": decision.get("slot_index")}
            )
            continue
        used_replacements.add(replacement_id)
        targets = set(decision.get("target_requirement_ids") or [])
        if not targets <= set(requirements_by_id):
            errors.append(
                {"code": "unknown_swap_requirement", "slot_index": decision.get("slot_index")}
            )
        for coverage in decision.get("swap_coverage") or []:
            if coverage.get("requirement_id") not in targets:
                errors.append(
                    {"code": "swap_coverage_target_mismatch", "slot_index": decision.get("slot_index")}
                )
            for reference in coverage.get("evidence_refs") or []:
                source = portfolio_sources.get(reference.get("source_id"))
                if (
                    reference.get("source_type") == "cv"
                    or source is None
                    or source.get("project_id") != replacement_id
                ):
                    errors.append(
                        {
                            "code": "swap_evidence_not_owned_by_replacement",
                            "slot_index": decision.get("slot_index"),
                        }
                    )

    current = result.get("current_cv_score")
    suggested = result.get("suggested_cv_score")
    if result.get("analysis_status") == "completed":
        if not isinstance(current, int) or not 0 <= current <= 100:
            errors.append({"code": "current_score_out_of_bounds"})
        if not isinstance(suggested, int) or not 0 <= suggested <= 100:
            errors.append({"code": "suggested_score_out_of_bounds"})
        if isinstance(current, int) and isinstance(suggested, int) and suggested < current:
            errors.append({"code": "suggested_score_below_current"})
        if all(item.get("action") == "keep" for item in decisions) and suggested != current:
            errors.append({"code": "all_keep_score_uplift"})
    return errors
