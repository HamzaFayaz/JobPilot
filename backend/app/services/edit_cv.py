"""In-place .docx text replacement preserving paragraph/run styles."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from docx import Document


def _set_paragraph_text(paragraph, text: str) -> None:
    """Replace paragraph text while keeping the first run's formatting."""
    runs = paragraph.runs
    if not runs:
        paragraph.add_run(text)
        return
    runs[0].text = text
    for run in runs[1:]:
        run.text = ""


def apply_slot_replacements(
    *,
    source_docx: Path,
    dest_docx: Path,
    layout_slots: list[dict[str, Any]],
    generated_slots: list[dict[str, Any]],
) -> None:
    """Copy master CV and write generated title/items into mapped paragraphs."""
    dest_docx.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_docx, dest_docx)
    doc = Document(str(dest_docx))
    paragraphs = list(doc.paragraphs)
    by_index = {int(slot["slot_index"]): slot for slot in generated_slots}

    for layout in layout_slots:
        slot_index = int(layout["slot_index"])
        generated = by_index.get(slot_index)
        if generated is None:
            continue
        targets = layout.get("docx_targets") or {}
        title_index = targets.get("title_paragraph_index")
        item_indexes = targets.get("item_paragraph_indexes") or []

        title = str(generated.get("title") or "")
        items = [str(item) for item in (generated.get("items") or [])]

        if title_index is not None and 0 <= int(title_index) < len(paragraphs):
            _set_paragraph_text(paragraphs[int(title_index)], title)

        for item_index, para_index in enumerate(item_indexes):
            if para_index is None:
                continue
            if item_index >= len(items):
                break
            idx = int(para_index)
            if 0 <= idx < len(paragraphs):
                _set_paragraph_text(paragraphs[idx], items[item_index])

    doc.save(str(dest_docx))
