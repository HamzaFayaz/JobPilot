"""Source-boundary and swap validation helpers."""

from __future__ import annotations

import re
from typing import Any

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
