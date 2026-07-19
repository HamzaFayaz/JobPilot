"""Deterministic whole-word trim to satisfy character budgets."""

from __future__ import annotations

import re


def word_trim_to_max(text: str, max_characters: int) -> str:
    """Drop whole words from the end until len(text) <= max_characters.

    Character budget is the check; trimming is by words (not mid-word chops),
    except when a single token exceeds the budget.
    """
    if max_characters <= 0:
        return ""
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if len(cleaned) <= max_characters:
        return cleaned

    words = cleaned.split(" ")
    while words and len(" ".join(words)) > max_characters:
        words.pop()
    if words:
        result = " ".join(words).rstrip(" ,;:/")
        if result:
            return result

    # Single oversized token — last-resort character cut at budget.
    token = cleaned[:max_characters].rstrip(" ,;:/")
    return token
