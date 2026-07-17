"""Deterministic CV date-range and tenure arithmetic."""

from __future__ import annotations

import calendar
import re
from datetime import date

MONTHS = {
    name.casefold(): index
    for index, name in enumerate(calendar.month_name)
    if name
}
MONTHS.update(
    {
        name.casefold(): index
        for index, name in enumerate(calendar.month_abbr)
        if name
    }
)
DATE_RANGE_RE = re.compile(
    r"\b(?:(?P<start_month>[A-Za-z]{3,9})\s+)?(?P<start_year>\d{4})"
    r"\s*(?:-|–|—|to)\s*"
    r"(?:(?P<end_month>[A-Za-z]{3,9})\s+)?"
    r"(?P<end_year>\d{4}|present|current|now)\b",
    re.IGNORECASE,
)


def _month_index(month: str | None, year: int, *, end: bool) -> int:
    number = MONTHS.get((month or "").casefold(), 12 if end else 1)
    return year * 12 + number - 1


def parse_date_ranges(text: str, reference_date: date) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    reference = reference_date.year * 12 + reference_date.month - 1
    for match in DATE_RANGE_RE.finditer(text):
        start_year = int(match.group("start_year"))
        start = _month_index(match.group("start_month"), start_year, end=False)
        end_value = match.group("end_year").casefold()
        if end_value in {"present", "current", "now"}:
            end = reference
        else:
            end = _month_index(
                match.group("end_month"),
                int(end_value),
                end=True,
            )
            end = min(end, reference)
        if start <= end:
            ranges.append((start, end))
    return ranges


def completed_months(text: str, reference_date: date) -> int:
    """Count the union of explicit ranges so overlapping work is not doubled."""
    covered: set[int] = set()
    for start, end in parse_date_ranges(text, reference_date):
        covered.update(range(start, end + 1))
    return len(covered)


def required_months(requirement_text: str) -> int | None:
    match = re.search(
        r"\b(?:minimum\s+of\s+|at\s+least\s+)?(\d+(?:\.\d+)?)\+?\s*years?\b",
        requirement_text,
        re.IGNORECASE,
    )
    return round(float(match.group(1)) * 12) if match else None
