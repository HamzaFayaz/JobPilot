"""Lightweight LinkedIn post listing rewrite — not part of the LangGraph orchestrator.

Cleans messy WebBridge a11y dumps into title / company / description and an
apply hint (email, link, WhatsApp, LinkedIn DM, or none). Failures fall back
to the original listing.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Literal

from openai import OpenAI

from backend.app.config import settings
from backend.app.models.browser import RawJobListing

logger = logging.getLogger(__name__)

ApplyMethod = Literal["email", "url", "whatsapp", "linkedin_dm", "none"]

_REWRITE_SYSTEM = """You clean LinkedIn hiring POST listings scraped from an accessibility tree.

The raw text is messy: author profile chrome ("Premium Profile 2nd"), headlines,
"Follow", reaction counts, and duplicated names are mixed into the body.

Return ONLY valid JSON:
{
  "listings": [
    {
      "index": 0,
      "title": "real job title only",
      "company": "employer or hiring org (not author connection degree)",
      "description": "clean readable post body — role, requirements, location, pay if present. No reaction counts, no Follow buttons, no Premium Profile chrome.",
      "apply_method": "email" | "url" | "whatsapp" | "linkedin_dm" | "none",
      "apply_value": "email address, URL, phone, or poster name to search — empty string if none",
      "apply_note": "one short sentence telling the user how to apply"
    }
  ]
}

Rules:
- Prefer real role titles (e.g. Senior AI Engineer) over poster names.
- company = employer brand when known; else the poster/person name without '2nd'/'Premium Profile'.
- If the post says DM / message me / comment: apply_method=linkedin_dm and apply_value=poster name.
- If email present: apply_method=email.
- If apply/JD http(s) link present: apply_method=url (prefer apply over JD when both).
- If WhatsApp present: apply_method=whatsapp.
- If nothing: apply_method=none, apply_note explains to search the poster/company on LinkedIn.
- Do not invent emails, links, or companies. Keep facts from the post only.
- Keep one listing per input index. Same order.
"""

_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _client() -> OpenAI:
    return OpenAI(
        api_key=settings.dashscope_api_key,
        base_url=settings.qwen_base_url,
        timeout=90.0,
    )


def _parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    match = _JSON_OBJECT_RE.search(cleaned)
    if match:
        cleaned = match.group(0)
    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError("rewrite response is not a JSON object")
    return data


def format_apply_header(
    *,
    apply_method: str,
    apply_value: str,
    apply_note: str,
) -> str:
    """User-facing apply block prepended to the cleaned description."""
    method = (apply_method or "none").strip().lower()
    value = (apply_value or "").strip()
    note = (apply_note or "").strip()

    if method == "email" and value:
        line = f"Apply via email: {value}"
    elif method == "url" and value:
        line = f"Apply / JD link: {value}"
    elif method == "whatsapp" and value:
        line = f"WhatsApp: {value}"
    elif method == "linkedin_dm":
        who = value or "the poster"
        line = f"DM on LinkedIn — search “{who}”"
    else:
        line = (
            note
            or "No apply info in this post — search the poster or company on LinkedIn."
        )

    if note and method != "none" and note.lower() not in line.lower():
        return f"How to apply\n{line}\n{note}"
    return f"How to apply\n{line}"


def _compose_description(clean_body: str, apply_header: str) -> str:
    body = clean_body.strip()
    header = apply_header.strip()
    if not body:
        return header
    return f"{header}\n\n{body}"


def _should_rewrite(listing: RawJobListing) -> bool:
    """Rewrite LinkedIn posts; skip empty descriptions."""
    if listing.source_platform != "linkedin":
        return False
    return bool(listing.description_text.strip())


def _apply_rewrite(
    listing: RawJobListing,
    item: dict[str, Any],
) -> RawJobListing:
    title = str(item.get("title") or listing.title).strip() or listing.title
    company = str(item.get("company") or listing.company).strip() or listing.company
    body = str(item.get("description") or listing.description_text).strip()
    apply_method = str(item.get("apply_method") or "none").strip().lower()
    apply_value = str(item.get("apply_value") or "").strip()
    apply_note = str(item.get("apply_note") or "").strip()
    if apply_method not in {"email", "url", "whatsapp", "linkedin_dm", "none"}:
        apply_method = "none"

    description = _compose_description(
        body,
        format_apply_header(
            apply_method=apply_method,
            apply_value=apply_value,
            apply_note=apply_note,
        ),
    )
    return listing.model_copy(
        update={
            "title": title,
            "company": company,
            "description_text": description,
        }
    )


def rewrite_listings(listings: list[RawJobListing]) -> list[RawJobListing]:
    """Rewrite messy post listings with a normal Qwen call. Best-effort."""
    if not listings:
        return listings
    if not settings.dashscope_api_key:
        logger.warning("listing rewrite skipped — DASHSCOPE_API_KEY not set")
        return listings

    targets = [(index, listing) for index, listing in enumerate(listings) if _should_rewrite(listing)]
    if not targets:
        return listings

    payload = [
        {
            "index": index,
            "title": listing.title,
            "company": listing.company,
            "url": listing.url,
            "description": listing.description_text[:6000],
        }
        for index, listing in targets
    ]

    try:
        response = _client().chat.completions.create(
            model=settings.qwen_model,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _REWRITE_SYSTEM},
                {
                    "role": "user",
                    "content": json.dumps({"listings": payload}, ensure_ascii=False),
                },
            ],
        )
        content = response.choices[0].message.content or ""
        data = _parse_json_object(content)
        items = data.get("listings")
        if not isinstance(items, list):
            raise ValueError("listings array missing")

        by_index: dict[int, dict[str, Any]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                idx = int(item.get("index"))
            except (TypeError, ValueError):
                continue
            by_index[idx] = item

        rewritten = list(listings)
        for index, listing in targets:
            item = by_index.get(index)
            if item:
                rewritten[index] = _apply_rewrite(listing, item)
        logger.info(
            "listing rewrite applied to %s/%s LinkedIn listing(s)",
            sum(1 for index, _ in targets if index in by_index),
            len(targets),
        )
        return rewritten
    except Exception as exc:
        logger.warning("listing rewrite failed — using raw listings: %s", exc)
        return listings
