"""Deterministic CV project-slot parsing with source traceability."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any

PROJECT_HEADING_RE = re.compile(
    r"^\s*(?:selected\s+projects?|projects?|portfolio(?:\s+projects?)?)\s*:?\s*$",
    re.IGNORECASE,
)
KNOWN_NEXT_HEADING_RE = re.compile(
    r"^\s*(?:experience|employment|education|skills?|certifications?|"
    r"professional\s+summary|summary|awards?|publications?|languages?|"
    r"interests?|references?)\s*:?\s*$",
    re.IGNORECASE,
)
BULLET_RE = re.compile(r"^\s*(?:[-*•●▪◦‣⁃]|\d{1,2}[.)])\s+")


def _line_spans(text: str) -> list[tuple[int, int, str]]:
    return [(m.start(), m.end(), m.group(0)) for m in re.finditer(r".*(?:\r\n|\n|\r|$)", text) if m.group(0)]


def _normalized(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).replace("\u00a0", " ")
    value = value.casefold()
    value = re.sub(r"[^\w+#./-]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _display_name(excerpt: str) -> str:
    first = next((line.strip() for line in excerpt.splitlines() if line.strip()), excerpt.strip())
    first = BULLET_RE.sub("", first)
    for separator in (" — ", " – ", " | ", ":", " - "):
        if separator in first:
            first = first.split(separator, 1)[0].strip()
            break
    return first[:200]


def _aliases(project: dict[str, Any]) -> set[str]:
    values = {
        str(project.get("name") or ""),
        str(project.get("repo_full_name") or ""),
        str(project.get("repo_name") or ""),
    }
    repo = str(project.get("repo_full_name") or "")
    if "/" in repo:
        values.add(repo.rsplit("/", 1)[-1])
    aliases = project.get("aliases") or []
    if isinstance(aliases, list):
        values.update(str(alias) for alias in aliases)
    return {alias for value in values if (alias := _normalized(value))}


def _looks_like_top_heading(line: str) -> bool:
    stripped = line.strip().rstrip(":")
    if not stripped or len(stripped) > 60 or BULLET_RE.match(line):
        return False
    return bool(KNOWN_NEXT_HEADING_RE.match(line))


def _section_span(cv_text: str) -> tuple[int, int] | None:
    lines = _line_spans(cv_text)
    heading_index = next(
        (index for index, (_, _, line) in enumerate(lines) if PROJECT_HEADING_RE.match(line.rstrip("\r\n"))),
        None,
    )
    if heading_index is None:
        return None
    start = lines[heading_index][1]
    end = len(cv_text)
    for _, (line_start, _, line) in enumerate(lines[heading_index + 1 :], start=heading_index + 1):
        if _looks_like_top_heading(line.rstrip("\r\n")):
            end = line_start
            break
    return start, end


def _candidate_spans(section: str, section_start: int, aliases: list[tuple[str, dict[str, Any]]]) -> list[tuple[int, int]]:
    lines = _line_spans(section)
    nonempty = [(start, end, line) for start, end, line in lines if line.strip()]
    bullet_starts = [index for index, (_, _, line) in enumerate(nonempty) if BULLET_RE.match(line)]
    spans: list[tuple[int, int]] = []
    if bullet_starts:
        for position, index in enumerate(bullet_starts):
            start = nonempty[index][0]
            next_index = bullet_starts[position + 1] if position + 1 < len(bullet_starts) else len(nonempty)
            end = nonempty[next_index - 1][1]
            spans.append((section_start + start, section_start + end))
        return spans

    title_starts: list[int] = []
    for start, _end, line in nonempty:
        stripped = line.strip()
        normalized_line = _normalized(stripped)
        alias_overlap = max(
            (
                len(set(alias.rstrip("s").split()) & set(normalized_line.rstrip("s").split()))
                for alias, _project in aliases
            ),
            default=0,
        )
        if (
            len(stripped) <= 240
            and not stripped.endswith((".", ";"))
            and (
                bool(re.search(r"\([^()\n]{2,100}\)\s*$", stripped))
                or alias_overlap >= 2
            )
        ):
            title_starts.append(start)
    title_starts = sorted(set(title_starts))
    if title_starts:
        for index, start in enumerate(title_starts):
            end = (
                title_starts[index + 1]
                if index + 1 < len(title_starts)
                else len(section.rstrip())
            )
            spans.append((section_start + start, section_start + end))
        return spans

    # DOCX extraction commonly emits a title paragraph followed by one or more
    # description paragraphs. Known project-name occurrences provide reliable
    # ordered boundaries without merging multiple projects into one slot.
    normalized_section = _normalized(section)
    located: list[int] = []
    for alias, _project in aliases:
        if len(alias) < 3:
            continue
        match = re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", normalized_section)
        if match:
            # Map a normalized occurrence back to its original line by matching
            # each line independently; offsets returned below always use source.
            for start, _end, line in nonempty:
                if alias in _normalized(line):
                    located.append(start)
                    break
    starts = sorted(set(located))
    if starts:
        for index, start in enumerate(starts):
            end = starts[index + 1] if index + 1 < len(starts) else len(section)
            while end > start and section[end - 1].isspace():
                end -= 1
            spans.append((section_start + start, section_start + end))
        return spans

    # Preserve unknown unbulleted slots. Blank-line separated paragraphs are
    # independent candidates; a single paragraph remains one slot.
    trimmed_section = section.rstrip()
    for match in re.finditer(r"\S(?:.*?\S)?(?=(?:\r?\n){2,}|\Z)", trimmed_section, re.DOTALL):
        spans.append((section_start + match.start(), section_start + match.end()))
    return spans


def _match_project(excerpt: str, projects: list[dict[str, Any]]) -> tuple[str | None, str, float]:
    normalized_excerpt = _normalized(excerpt)
    exact_matches: list[tuple[int, dict[str, Any]]] = []
    fuzzy: list[tuple[float, dict[str, Any]]] = []
    for project in projects:
        project_aliases = _aliases(project)
        contained = [alias for alias in project_aliases if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", normalized_excerpt)]
        if contained:
            exact_matches.append((max(map(len, contained)), project))
            continue
        title = _normalized(_display_name(excerpt))
        score = max((SequenceMatcher(None, title, alias).ratio() for alias in project_aliases), default=0.0)
        fuzzy.append((score, project))
    if exact_matches:
        _, project = max(exact_matches, key=lambda item: item[0])
        return project.get("id"), "exact_alias", 1.0
    if fuzzy:
        score, project = max(fuzzy, key=lambda item: item[0])
        if score >= 0.72:
            return project.get("id"), "fuzzy_alias", round(score, 4)
    return None, "unmatched", 0.0


def parse_cv_project_slots(
    cv_text: str,
    portfolio_projects: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return ordered project slots with exact CV excerpts and offsets."""
    section = _section_span(cv_text)
    if not section:
        return []
    section_start, section_end = section
    aliases = [
        (alias, project)
        for project in portfolio_projects
        for alias in _aliases(project)
    ]
    spans = _candidate_spans(cv_text[section_start:section_end], section_start, aliases)
    slots: list[dict[str, Any]] = []
    for source_start, source_end in spans:
        while source_start < source_end and cv_text[source_start].isspace():
            source_start += 1
        while source_end > source_start and cv_text[source_end - 1].isspace():
            source_end -= 1
        if source_start >= source_end:
            continue
        excerpt = cv_text[source_start:source_end]
        matched_id, method, confidence = _match_project(excerpt, portfolio_projects)
        slots.append(
            {
                "slot_index": len(slots),
                "cv_project_name": _display_name(excerpt),
                "display_project_name": _display_name(excerpt),
                "cv_excerpt": excerpt,
                "source_start": source_start,
                "source_end": source_end,
                "chars_budget": len(excerpt),
                "character_budget": len(excerpt),
                "matched_portfolio_project_id": matched_id,
                "match_method": method,
                "match_confidence": confidence,
            }
        )
    return slots
