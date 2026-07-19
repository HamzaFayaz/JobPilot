"""Lightweight LinkedIn post listing display formatter — not part of LangGraph.

Formats messy WebBridge a11y dumps for the Applications UI only.
Keeps description_text (raw JD) unchanged for analysis / retrieval.
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

_REWRITE_SYSTEM = """You format LinkedIn hiring POST listings for display only.

The input is a messy accessibility-tree dump (Premium Profile, Follow, reaction
counts, duplicated names mixed into the body). Your job is FORMAT + APPLY HINTS —
not to rewrite, summarize, or judge what matters.

Return ONLY valid JSON:
{
  "listings": [
    {
      "index": 0,
      "title": "real job title only",
      "company": "employer or hiring org (not author connection degree)",
      "description": "same post content, cleaned of UI chrome only — keep ALL role facts, requirements, location, pay, tech, and instructions that appear in the post",
      "apply_method": "email" | "url" | "whatsapp" | "linkedin_dm",
      "apply_value": "exact email, exact URL, exact phone, or poster name for DM search",
      "apply_note": "one short sentence on how to apply"
    }
  ]
}

Hard rules:
- SAME content: do not drop requirements, skills, tenure, location, or other facts.
- Do not decide importance. Do not invent or improve the JD.
- Strip only UI chrome: Follow, reactions, Premium Profile, connection degree, duplicated nav noise.
- title = real role title when present; else best title from the post (not "Verified Profile 2nd").
- company = employer brand when known; else poster name without Premium/2nd chrome.
- Apply extraction (use what is EXPLICITLY in the post only):
  - email → apply_method=email, apply_value=that email
  - http(s) apply/JD/form link (Google Form, careers page, etc.) → apply_method=url, apply_value=that exact URL
  - WhatsApp / wa.me / phone for WhatsApp → apply_method=whatsapp
  - DM / message me / comment to apply → apply_method=linkedin_dm, apply_value=poster name
- NEVER invent emails, phone numbers, or URLs. Never fabricate a LinkedIn job URL or any link not in the post.
- If none of email / url / whatsapp / explicit DM apply are present: apply_method=linkedin_dm and apply_value=poster name so the user can search that person on LinkedIn and apply themselves.
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
        line = f"DM on LinkedIn. Search “{who}” and apply yourself"
    else:
        who = value or "the poster"
        line = (
            note
            or f"No email/link/WhatsApp in this post. Search “{who}” on LinkedIn and DM to apply."
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


def _poster_fallback_name(listing: RawJobListing, item: dict[str, Any]) -> str:
    company = str(item.get("company") or listing.company or "").strip()
    if company and "premium" not in company.lower() and "2nd" not in company.lower():
        return company
    title = str(item.get("title") or listing.title or "").strip()
    return title or "the poster"


def _apply_rewrite(
    listing: RawJobListing,
    item: dict[str, Any],
) -> RawJobListing:
    """Keep raw description_text; set display_description_text for UI only."""
    raw_description = listing.description_text
    title = str(item.get("title") or listing.title).strip() or listing.title
    company = str(item.get("company") or listing.company).strip() or listing.company
    body = str(item.get("description") or raw_description).strip()
    apply_method = str(item.get("apply_method") or "none").strip().lower()
    apply_value = str(item.get("apply_value") or "").strip()
    apply_note = str(item.get("apply_note") or "").strip()
    if apply_method not in {"email", "url", "whatsapp", "linkedin_dm", "none"}:
        apply_method = "none"

    # No inventable contact → DM / search the poster (same as linkedin_dm).
    if apply_method == "none" or (
        apply_method in {"email", "url", "whatsapp"} and not apply_value
    ):
        apply_method = "linkedin_dm"
        if not apply_value:
            apply_value = _poster_fallback_name(listing, item)
        if not apply_note:
            apply_note = (
                f"Search “{apply_value}” on LinkedIn and message them to apply."
            )

    display = _compose_description(
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
            "description_text": raw_description,
            "display_description_text": display,
        }
    )


def rewrite_listings(listings: list[RawJobListing]) -> list[RawJobListing]:
    """Format LinkedIn posts for UI; leave raw description_text for analysis."""
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
            "listing display format applied to %s/%s LinkedIn listing(s)",
            sum(1 for index, _ in targets if index in by_index),
            len(targets),
        )
        return rewritten
    except Exception as exc:
        logger.warning("listing rewrite failed — using raw listings: %s", exc)
        return listings
