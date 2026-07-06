"""Parse browser agent output into RawJobListing rows (provider-agnostic)."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from typing import Any, Literal
from urllib.parse import parse_qs, urlparse

from worker.models import Platform, RawJobListing
from worker.snapshot_compress import (
    extract_job_description_from_snapshot,
    extract_posts_from_search_snapshot,
    snapshot_has_job_detail_panel,
)

logger = logging.getLogger(__name__)

PhaseHint = Literal["jobs", "posts", "indeed", "mixed"]

_LINKEDIN_JOB_VIEW_RE = re.compile(r"linkedin\.com/jobs/view/", re.IGNORECASE)
_LINKEDIN_POST_URL_MARKERS = (
    "/feed/update/",
    "/posts/",
    "urn:li:activity:",
    "urn:li:share:",
)
_AGGREGATOR_COMPANIES = frozenset({"hire feed"})
_SYNTHETIC_POST_URL_PREFIX = "linkedin-post://"


def _synthetic_post_url(author: str, title: str, description: str) -> str:
    key = f"{author}|{title}|{description[:200]}"
    digest = hashlib.sha256(key.encode()).hexdigest()[:16]
    return f"{_SYNTHETIC_POST_URL_PREFIX}{digest}"


def is_synthetic_post_url(url: str) -> bool:
    return url.strip().lower().startswith(_SYNTHETIC_POST_URL_PREFIX)


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


def merge_listings(listings: list[RawJobListing], *, max_listings: int) -> list[RawJobListing]:
    """Deduplicate by URL and cap at max_listings."""
    seen: set[str] = set()
    merged: list[RawJobListing] = []
    for item in listings:
        key = item.url.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(item)
        if len(merged) >= max_listings:
            break
    return merged


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


def _slug_from_job_url(url: str) -> str:
    match = re.search(r"/jobs/view/([^/?#]+)", url, re.IGNORECASE)
    return match.group(1).lower() if match else ""


def _title_words_in_slug(title: str, slug: str) -> bool:
    words = [word for word in re.findall(r"[a-z0-9]+", title.lower()) if len(word) > 2]
    if not words:
        return True
    hits = sum(1 for word in words[:4] if word in slug)
    return hits >= min(2, len(words))


def current_job_id_from_url(url: str) -> str | None:
    return _current_job_id_from_url(url)


def _current_job_id_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    values = parse_qs(parsed.query).get("currentJobId")
    if values and values[0].strip().isdigit():
        return values[0].strip()
    return None


def _linkedin_job_view_url(job_id: str) -> str:
    return f"https://www.linkedin.com/jobs/view/{job_id}/"


def is_valid_linkedin_job_url(url: str) -> bool:
    return bool(_LINKEDIN_JOB_VIEW_RE.search(url))


def is_valid_linkedin_post_url(url: str) -> bool:
    lower = url.lower()
    if not lower.startswith("http"):
        return False
    if "/in/" in lower and not any(marker in lower for marker in _LINKEDIN_POST_URL_MARKERS):
        return False
    if "linkedin.com/search/results" in lower:
        return False
    return any(marker in lower for marker in _LINKEDIN_POST_URL_MARKERS) or (
        "linkedin.com/feed" in lower and "/update/" in lower
    )


def _job_id_from_listing_url(url: str) -> str:
    slug = _slug_from_job_url(url)
    return slug if slug.isdigit() else ""


def job_id_from_listing_url(url: str) -> str:
    """Numeric LinkedIn job id from a listing or search URL, if present."""
    job_id = _job_id_from_listing_url(url)
    if job_id:
        return job_id
    current = _current_job_id_from_url(url)
    return current or ""


def sanitize_and_enrich_listings(
    listings: list[RawJobListing],
    *,
    phase: PhaseHint,
    last_snapshot: dict[str, Any] | None = None,
    job_descriptions: dict[str, str] | None = None,
) -> list[RawJobListing]:
    """Fill missing descriptions, fix job URLs, and drop invalid post/job links."""
    snapshot_url = ""
    if last_snapshot:
        inner = last_snapshot.get("data")
        if isinstance(inner, dict):
            snapshot_url = str(inner.get("url") or "")
        else:
            snapshot_url = str(last_snapshot.get("url") or "")

    current_job_id = _current_job_id_from_url(snapshot_url)
    snapshot_description = ""
    if last_snapshot and phase in {"jobs", "mixed"}:
        if snapshot_has_job_detail_panel(last_snapshot):
            snapshot_description = extract_job_description_from_snapshot(last_snapshot)

    enriched: list[RawJobListing] = []
    for item in listings:
        description = item.description_text.strip()
        listing_job_id = job_id_from_listing_url(item.url)

        worker_description = ""
        if job_descriptions and listing_job_id:
            worker_description = job_descriptions.get(listing_job_id, "")
        if not worker_description and snapshot_description:
            if listing_job_id and listing_job_id == current_job_id:
                worker_description = snapshot_description
            elif not job_descriptions and not description:
                worker_description = snapshot_description

        if worker_description:
            description = worker_description

        url = item.url.strip()
        company_lower = item.company.strip().lower()

        if phase in {"jobs", "mixed"}:
            slug = _slug_from_job_url(url)
            title_matches_url = _title_words_in_slug(item.title, slug) if slug else False

            if company_lower in _AGGREGATOR_COMPANIES and not title_matches_url:
                logger.warning(
                    "Dropping aggregator job with mismatched URL: %s / %s",
                    item.title,
                    url,
                )
                continue

            if current_job_id and (
                not is_valid_linkedin_job_url(url) or not title_matches_url
            ):
                url = _linkedin_job_view_url(current_job_id)
                logger.info(
                    "Replaced job URL for %r with currentJobId=%s",
                    item.title,
                    current_job_id,
                )
            elif not is_valid_linkedin_job_url(url):
                logger.warning("Dropping job with invalid URL: %s", url)
                continue
            elif not title_matches_url:
                logger.warning("Job URL slug may not match title: %s / %s", item.title, url)

        if phase in {"posts", "mixed"} and not is_valid_linkedin_job_url(url):
            if is_synthetic_post_url(url):
                pass
            elif not is_valid_linkedin_post_url(url):
                logger.warning("Dropping post with invalid URL: %s", url)
                continue

        if phase in {"jobs", "mixed"} and not description:
            logger.warning(
                "Dropping job missing descriptionText: %s @ %s",
                item.title,
                item.company,
            )
            continue

        if phase == "posts" and not description:
            logger.warning("Dropping post missing descriptionText: %s @ %s", item.title, item.company)
            continue

        enriched.append(
            RawJobListing(
                title=item.title,
                company=item.company,
                url=url,
                description_text=description,
                source_platform=item.source_platform,
            )
        )
    return enriched


def enrich_agent_listings_json(
    text: str,
    *,
    platform: Platform,
    phase: PhaseHint,
    last_snapshot: dict[str, Any] | None,
    job_descriptions: dict[str, str] | None = None,
) -> str:
    listings = parse_listings_from_agent_output(text, platform=platform)
    if not listings:
        return text
    enriched = sanitize_and_enrich_listings(
        listings,
        phase=phase,
        last_snapshot=last_snapshot,
        job_descriptions=job_descriptions,
    )
    return json.dumps(
        [item.model_dump(by_alias=True) for item in enriched],
        ensure_ascii=False,
    )


def listings_from_extracted_posts(
    posts: list[dict[str, Any]],
    *,
    platform: Platform,
    max_listings: int | None = None,
) -> list[RawJobListing]:
    listings: list[RawJobListing] = []
    for post in posts:
        if not post.get("isJobOpening"):
            continue
        title = str(post.get("title") or "").strip()
        company = str(post.get("company") or "").strip()
        url = str(post.get("url") or "").strip()
        description = str(post.get("descriptionText") or "").strip()
        if not title or not description:
            continue
        if not url:
            author = str(post.get("author") or "").strip()
            url = _synthetic_post_url(author, title, description)
        listings.append(
            RawJobListing(
                title=title,
                company=company or "Unknown",
                url=url,
                description_text=description,
                source_platform=platform,
            )
        )
        if max_listings is not None and len(listings) >= max_listings:
            break
    return listings


def _posts_from_snapshot(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    posts = snapshot.get("posts")
    if isinstance(posts, list) and posts:
        return posts
    return extract_posts_from_search_snapshot(snapshot)


def merge_jobs_agent_with_extraction(
    text: str,
    *,
    platform: Platform,
    job_descriptions: dict[str, str],
    last_snapshot: dict[str, Any] | None,
) -> str:
    """Inject worker-extracted JD text; agent supplies title/company/url only."""
    agent_listings = parse_listings_from_agent_output(text, platform=platform)
    if not agent_listings:
        return text
    enriched = sanitize_and_enrich_listings(
        agent_listings,
        phase="jobs",
        last_snapshot=last_snapshot,
        job_descriptions=job_descriptions,
    )
    if not enriched:
        return text
    return json.dumps(
        [item.model_dump(by_alias=True) for item in enriched],
        ensure_ascii=False,
    )


def merge_posts_agent_with_extraction(
    text: str,
    *,
    platform: Platform,
    last_snapshot: dict[str, Any] | None,
    target: int,
) -> str:
    agent_listings = parse_listings_from_agent_output(text, platform=platform)
    if not last_snapshot:
        return text

    extracted = _posts_from_snapshot(last_snapshot)
    extracted_listings = listings_from_extracted_posts(
        extracted,
        platform=platform,
        max_listings=target,
    )
    if not extracted_listings:
        return text

    merged = merge_listings(extracted_listings + agent_listings, max_listings=target)
    return json.dumps(
        [item.model_dump(by_alias=True) for item in merged],
        ensure_ascii=False,
    )
