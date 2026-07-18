"""Immutable source spans for model references to the submitted CV."""

from __future__ import annotations

import hashlib
import re
from typing import Any


def _section_name(line: str, current: str) -> str:
    stripped = line.strip().strip(":")
    if (
        stripped
        and len(stripped) <= 60
        and not re.search(r"[.!?]$", stripped)
        and (stripped.isupper() or re.fullmatch(r"[A-Z][A-Za-z &/+-]+", stripped))
    ):
        return stripped
    return current


def build_cv_evidence_spans(
    cv_text: str,
    project_slots: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return exact non-overlapping line spans with stable content identities."""
    project_slots = project_slots or []
    spans: list[dict[str, Any]] = []
    section = "Document"
    for match in re.finditer(r"[^\r\n]+", cv_text):
        raw = match.group(0)
        leading = len(raw) - len(raw.lstrip())
        trailing = len(raw) - len(raw.rstrip())
        start = match.start() + leading
        end = match.end() - trailing
        if start >= end:
            continue
        content = cv_text[start:end]
        section = _section_name(content, section)
        slot = next(
            (
                item
                for item in project_slots
                if item.get("source_start") is not None
                and item.get("source_end") is not None
                and int(item["source_start"]) <= start
                and end <= int(item["source_end"])
            ),
            None,
        )
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        spans.append(
            {
                "source_id": f"cv:{start}:{end}:{digest[:12]}",
                "content": content,
                "source_start": start,
                "source_end": end,
                "section": section,
                "project_slot_id": (
                    f"cv_slot_{int(slot['slot_index'])}" if slot is not None else None
                ),
                "content_hash": digest,
            }
        )
    return spans
