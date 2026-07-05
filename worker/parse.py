"""Parse browser agent output into RawJobListing rows (provider-agnostic)."""

import json
import re

from worker.models import Platform, RawJobListing


def _extract_json_array(text: str) -> list[dict]:
    text = text.strip()
    if not text:
        return []

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", text, re.IGNORECASE)
    if fenced:
        try:
            parsed = json.loads(fenced.group(1))
            if isinstance(parsed, list):
                return [item for item in parsed if isinstance(item, dict)]
        except json.JSONDecodeError:
            pass

    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            parsed = json.loads(text[start : end + 1])
            if isinstance(parsed, list):
                return [item for item in parsed if isinstance(item, dict)]
        except json.JSONDecodeError:
            pass

    return []


def parse_listings_from_agent_output(text: str, *, platform: Platform) -> list[RawJobListing]:
    listings: list[RawJobListing] = []
    for item in _extract_json_array(text):
        title = str(item.get("title") or "").strip()
        company = str(item.get("company") or "").strip()
        url = str(item.get("url") or item.get("link") or "").strip()
        if not title or not url:
            continue

        description = str(
            item.get("descriptionText")
            or item.get("description_text")
            or item.get("description")
            or ""
        ).strip()
        source = item.get("sourcePlatform") or item.get("source_platform") or platform

        listings.append(
            RawJobListing(
                title=title,
                company=company or "Unknown",
                url=url,
                description_text=description,
                source_platform=source,
            )
        )
    return listings
