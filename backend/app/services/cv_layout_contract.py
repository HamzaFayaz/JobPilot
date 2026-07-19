"""Build per-slot layout budgets and docx paragraph targets before tailor_cv LLM."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from docx import Document

from backend.app.services.cv_project_slots import BULLET_RE

_BULLET_PREFIX_RE = re.compile(r"^\s*(?:[-*•●▪◦‣⁃]|\d{1,2}[.)])\s+")


def _plain_lines(excerpt: str) -> list[str]:
    return [line.strip() for line in excerpt.splitlines() if line.strip()]


def _strip_bullet(line: str) -> str:
    return _BULLET_PREFIX_RE.sub("", line).strip()


def parse_slot_layout_from_excerpt(slot_index: int, excerpt: str) -> dict[str, Any]:
    """Measure title + per-line/paragraph character budgets from the swap-out slot text."""
    lines = _plain_lines(excerpt)
    if not lines:
        raise ValueError(f"slot {slot_index} has empty CV excerpt")

    title_text = _strip_bullet(lines[0])
    body_lines = lines[1:]
    bullet_lines = [line for line in body_lines if BULLET_RE.match(line)]
    non_bullet = [line for line in body_lines if not BULLET_RE.match(line)]

    description_items: list[dict[str, Any]] = []
    if bullet_lines and len(bullet_lines) >= len(non_bullet):
        for index, line in enumerate(bullet_lines):
            text = _strip_bullet(line)
            description_items.append(
                {
                    "item_index": index,
                    "type": "bullet",
                    "current_text": text,
                    "max_characters": max(len(text), 1),
                }
            )
    elif body_lines:
        # One or more plain paragraphs under the title.
        if len(body_lines) == 1:
            text = _strip_bullet(body_lines[0])
            description_items.append(
                {
                    "item_index": 0,
                    "type": "paragraph",
                    "current_text": text,
                    "max_characters": max(len(text), 1),
                }
            )
        else:
            for index, line in enumerate(body_lines):
                text = _strip_bullet(line)
                description_items.append(
                    {
                        "item_index": index,
                        "type": "paragraph",
                        "current_text": text,
                        "max_characters": max(len(text), 1),
                    }
                )
    else:
        # Title-only slot — still require one short item so the model has a place
        # for a single description line with a small budget.
        description_items.append(
            {
                "item_index": 0,
                "type": "paragraph",
                "current_text": "",
                "max_characters": max(len(title_text), 24),
            }
        )

    return {
        "slot_index": slot_index,
        "title": {
            "current_text": title_text,
            "max_characters": max(len(title_text), 1),
        },
        "description_items": description_items,
        "docx_targets": {
            "title_paragraph_index": None,
            "item_paragraph_indexes": [],
        },
    }


def _normalize_match(value: str) -> str:
    value = _strip_bullet(value)
    value = re.sub(r"\s+", " ", value).strip().casefold()
    return value


def attach_docx_targets(
    layout_slots: list[dict[str, Any]],
    docx_path: Path,
) -> list[dict[str, Any]]:
    """Map layout current_text strings to paragraph indexes in the master .docx."""
    doc = Document(str(docx_path))
    paragraphs = list(doc.paragraphs)
    used: set[int] = set()

    def find_paragraph(text: str, start_at: int = 0) -> int | None:
        needle = _normalize_match(text)
        if not needle:
            return None
        for index in range(start_at, len(paragraphs)):
            if index in used:
                continue
            hay = _normalize_match(paragraphs[index].text)
            if not hay:
                continue
            if hay == needle or needle in hay or hay in needle:
                return index
        return None

    enriched: list[dict[str, Any]] = []
    for slot in layout_slots:
        slot = dict(slot)
        title_text = str((slot.get("title") or {}).get("current_text") or "")
        title_index = find_paragraph(title_text)
        item_indexes: list[int | None] = []
        search_from = (title_index + 1) if title_index is not None else 0
        if title_index is not None:
            used.add(title_index)
        for item in slot.get("description_items") or []:
            item_text = str(item.get("current_text") or "")
            found = find_paragraph(item_text, start_at=search_from)
            if found is not None:
                used.add(found)
                search_from = found + 1
            item_indexes.append(found)
        slot["docx_targets"] = {
            "title_paragraph_index": title_index,
            "item_paragraph_indexes": item_indexes,
        }
        enriched.append(slot)
    return enriched


def build_layout_contracts_for_swaps(
    *,
    cv_slots: list[dict[str, Any]],
    approved_slot_indexes: list[int],
    docx_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Build layout contracts for approved swap slot indexes."""
    by_index = {int(slot["slot_index"]): slot for slot in cv_slots}
    layouts: list[dict[str, Any]] = []
    for slot_index in approved_slot_indexes:
        source = by_index.get(int(slot_index))
        if source is None:
            raise ValueError(f"CV slot {slot_index} not found")
        layouts.append(
            parse_slot_layout_from_excerpt(
                int(slot_index),
                str(source.get("cv_excerpt") or ""),
            )
        )
    if docx_path is not None and docx_path.exists():
        layouts = attach_docx_targets(layouts, docx_path)
    return layouts


def layout_for_llm(layout_slots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Strip docx_targets before sending layout to the model."""
    payload: list[dict[str, Any]] = []
    for slot in layout_slots:
        payload.append(
            {
                "slot_index": slot["slot_index"],
                "title": slot["title"],
                "description_items": slot["description_items"],
            }
        )
    return payload
