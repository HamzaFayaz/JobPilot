"""Deterministic requirement-query extraction for evidence retrieval."""

from __future__ import annotations

import hashlib
import re
from typing import Any

MARKER_RE = re.compile(
    r"\b(must|required|minimum|preferred|nice to have|responsibilit(?:y|ies)|"
    r"qualification(?:s)?|experience with|proficien(?:t|cy)|knowledge of|"
    r"ability to|you will|we are looking for)\b",
    re.IGNORECASE,
)
PREFERRED_RE = re.compile(r"\b(preferred|nice to have|bonus|desirable|ideally)\b", re.I)
REQUIRED_RE = re.compile(r"\b(must|required|minimum|essential|need to)\b", re.I)
APPLICATION_RE = re.compile(
    r"\b(apply|application|submit|send (?:your )?(?:cv|resume)|email|contact|"
    r"equal opportunity|privacy|recruiter|click here)\b",
    re.IGNORECASE,
)
CONTACT_RE = re.compile(r"(?:https?://|www\.|\b[\w.+-]+@[\w.-]+\.\w+\b|\+?\d[\d\s().-]{7,})", re.I)
HEADING_RE = re.compile(
    r"^\s*(requirements?|qualifications?|responsibilities|what you(?:'|’)ll do|"
    r"what we(?:'|’)re looking for|preferred qualifications?)\s*:?\s*$",
    re.IGNORECASE,
)
BULLET_RE = re.compile(r"^\s*(?:[-*•●▪◦‣⁃]|\d{1,2}[.)])\s+")


def _normalize_query(text: str) -> str:
    text = BULLET_RE.sub("", text)
    text = CONTACT_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip(" \t\r\n-–—:;,.")
    return text


def _importance(text: str, section_hint: str) -> str:
    if PREFERRED_RE.search(text) or "preferred" in section_hint:
        return "preferred"
    if REQUIRED_RE.search(text) or section_hint in {"requirements", "qualifications"}:
        return "required"
    return "general"


def _category(text: str) -> str:
    lowered = text.casefold()
    if re.search(r"\b(degree|bachelor|master|phd|education)\b", lowered):
        return "education"
    if re.search(r"\b(remote|hybrid|onsite|on-site|location|relocat|travel)\b", lowered):
        return "location_or_work_mode"
    if re.search(r"\b(authori[sz]ed|visa|citizen|eligib|work permit|clearance)\b", lowered):
        return "eligibility"
    if re.search(r"\b(years?|experience|tenure)\b", lowered):
        return "experience"
    if re.search(r"\b(build|design|develop|deliver|manage|lead|maintain|collaborate|responsib)\b", lowered):
        return "responsibility"
    if re.search(
        r"\b(python|java|typescript|javascript|c\+\+|sql|aws|azure|gcp|api|"
        r"fastapi|langgraph|langchain|docker|kubernetes|machine learning|ai|llm)\b",
        lowered,
    ):
        return "skill"
    return "other"


def _stable_id(quote: str, position: int) -> str:
    digest = hashlib.sha256(quote.encode("utf-8")).hexdigest()[:8]
    return f"retrieval_req_{position + 1:02d}_{digest}"


def _candidate_fragments(description: str) -> list[tuple[int, str, str]]:
    lines = list(re.finditer(r".*(?:\r\n|\n|\r|$)", description))
    candidates: list[tuple[int, str, str]] = []
    section_hint = ""
    for match in lines:
        raw = match.group(0).rstrip("\r\n")
        if not raw.strip():
            continue
        if HEADING_RE.match(raw):
            section_hint = re.sub(r"\W+", " ", raw.casefold()).strip()
            continue
        if BULLET_RE.match(raw):
            candidates.append((match.start(), BULLET_RE.sub("", raw).strip(), section_hint))
            continue
        # Keep marker-bearing sentences independently. Product names remain
        # untouched because splitting occurs only at sentence punctuation.
        cursor = 0
        for sentence in re.finditer(r".+?(?:[.!?](?=\s+|$)|$)", raw):
            quote = sentence.group(0).strip()
            if quote and (MARKER_RE.search(quote) or section_hint):
                candidates.append((match.start() + sentence.start(), quote, section_hint))
            cursor = sentence.end()
        if cursor == 0 and MARKER_RE.search(raw):
            candidates.append((match.start(), raw.strip(), section_hint))
    return candidates


def extract_requirement_queries(
    job_title: str,
    description: str,
    *,
    max_queries: int = 12,
) -> list[dict[str, Any]]:
    """Extract bounded, exact-quote requirement queries plus one fallback."""
    max_queries = max(1, max_queries)
    selected: list[tuple[int, str, str]] = []
    seen: set[str] = set()
    for position, quote, section_hint in _candidate_fragments(description):
        normalized = _normalize_query(quote)
        key = normalized.casefold()
        if (
            not normalized
            or key in seen
            or CONTACT_RE.search(quote)
            or APPLICATION_RE.search(quote)
        ):
            continue
        seen.add(key)
        selected.append((position, quote, section_hint))
        if len(selected) >= max_queries - 1:
            break

    queries: list[dict[str, Any]] = []
    for index, (position, quote, section_hint) in enumerate(selected):
        normalized = _normalize_query(quote)
        queries.append(
            {
                "requirement_id": _stable_id(quote, index),
                "job_quote": quote,
                "query": normalized,
                "importance": _importance(quote, section_hint),
                "category": _category(quote),
                "source_position": position,
                "is_fallback": False,
            }
        )

    fallback_text = _normalize_query(f"{job_title}. {description}")
    if fallback_text:
        fallback_text = fallback_text[:2000]
        queries.append(
            {
                "requirement_id": "retrieval_fallback",
                "job_quote": description[:2000],
                "query": fallback_text,
                "importance": "general",
                "category": "other",
                "source_position": 0,
                "is_fallback": True,
            }
        )
    return queries[:max_queries]
