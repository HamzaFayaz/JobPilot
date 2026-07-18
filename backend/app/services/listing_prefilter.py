"""Normalize, dedupe, and drop-applied filtering for browser job listings."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from backend.app.db import get_connection
from backend.app.graph.state import JobListing
from backend.app.models.browser import Platform, RawJobListing

SYNTHETIC_POST_URL_PREFIX = "linkedin-post://"
_FALLBACK_TITLE = "Job post"
_TITLE_MAX_LEN = 80
_DESCRIPTION_FP_CHARS = 800

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_LINKEDIN_JOB_ID_RE = re.compile(r"linkedin\.com/jobs/view/(\d+)", re.IGNORECASE)
_LINKEDIN_ACTIVITY_RE = re.compile(r"urn:li:activity:(\d+)", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")


def is_synthetic_post_url(url: str) -> bool:
    return url.strip().lower().startswith(SYNTHETIC_POST_URL_PREFIX)


def synthetic_post_url(company: str, title: str, description: str) -> str:
    """Stable internal id when a post has no real URL (matches worker intent)."""
    key = f"{company}|{title}|{description[:200]}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return f"{SYNTHETIC_POST_URL_PREFIX}{digest}"


def _collapse_whitespace(value: str) -> str:
    return _WHITESPACE_RE.sub(" ", value.strip())


def _normalize_company(company: str) -> str:
    collapsed = _collapse_whitespace(company)
    return collapsed or "Unknown"


def _normalize_title(title: str) -> str:
    return _collapse_whitespace(title)


def _title_from_description(description: str) -> str:
    for line in description.splitlines():
        candidate = _collapse_whitespace(line)
        if candidate:
            if len(candidate) > _TITLE_MAX_LEN:
                return candidate[:_TITLE_MAX_LEN].rstrip()
            return candidate
    return _FALLBACK_TITLE


def _normalize_url(url: str) -> str:
    return url.strip()


def _text_fingerprint(text: str) -> str:
    normalized = _collapse_whitespace(text).lower()
    if len(normalized) > _DESCRIPTION_FP_CHARS:
        normalized = normalized[:_DESCRIPTION_FP_CHARS]
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def url_fingerprint(url: str) -> str | None:
    normalized = _normalize_url(url)
    if not normalized:
        return None

    lowered = normalized.lower().rstrip("/")
    if is_synthetic_post_url(lowered):
        return lowered

    job_match = _LINKEDIN_JOB_ID_RE.search(lowered)
    if job_match:
        return f"job:{job_match.group(1)}"

    activity_match = _LINKEDIN_ACTIVITY_RE.search(lowered)
    if activity_match:
        return f"activity:{activity_match.group(1)}"

    return lowered


def extract_contact_email(description: str) -> str | None:
    match = _EMAIL_RE.search(description)
    if not match:
        return None
    return match.group(0).lower()


def title_company_fingerprint(company: str, title: str) -> str:
    return f"{_normalize_company(company).lower()}::{_normalize_title(title).lower()}"


def dedupe_fingerprint(listing: JobListing) -> str:
    """Ordered identity keys — same job twice in one batch."""
    url = listing["url"]
    if url_key := url_fingerprint(url):
        if not is_synthetic_post_url(url):
            return f"url:{url_key}"
    if email := extract_contact_email(listing["description_text"]):
        return f"email:{email}"
    if url_key := url_fingerprint(url):
        return f"url:{url_key}"
    return f"desc:{_text_fingerprint(listing['description_text'])}"


@dataclass
class AppliedSignatures:
    urls: set[str] = field(default_factory=set)
    title_company: set[str] = field(default_factory=set)


def load_applied_signatures(user_id: int) -> AppliedSignatures:
    signatures = AppliedSignatures()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT url, platform, title, company
            FROM job_applications
            WHERE user_id = ?
            UNION ALL
            SELECT url, platform, title, company
            FROM job_packages
            WHERE user_id = ? AND status = 'applied'
            """,
            (user_id, user_id),
        ).fetchall()

    for row in rows:
        platform = (row["platform"] or "linkedin").lower()
        url = row["url"] or ""
        if url_key := url_fingerprint(url):
            signatures.urls.add(f"{platform}:{url_key}")

        title = row["title"] or ""
        company = row["company"] or ""
        if title or company:
            signatures.title_company.add(
                f"{platform}:{title_company_fingerprint(company, title or _FALLBACK_TITLE)}"
            )

    return signatures


def is_already_applied(listing: JobListing, applied: AppliedSignatures) -> bool:
    platform = listing["platform"]
    if url_key := url_fingerprint(listing["url"]):
        if f"{platform}:{url_key}" in applied.urls:
            return True

    title_company_key = f"{platform}:{title_company_fingerprint(listing['company'], listing['title'])}"
    return title_company_key in applied.title_company


def normalize_raw_listing(raw: RawJobListing) -> JobListing | None:
    """Map worker shape to graph shape. Drop only when description is missing."""
    description = raw.description_text.strip()
    if not description:
        return None

    company = _normalize_company(raw.company)
    title = _normalize_title(raw.title) or _title_from_description(description)
    url = _normalize_url(raw.url)
    if not url:
        url = synthetic_post_url(company, title, description)

    return JobListing(
        title=title,
        company=company,
        url=url,
        platform=raw.source_platform,
        description_text=description,
    )


def dedupe_listings(listings: list[JobListing]) -> list[JobListing]:
    seen: set[str] = set()
    deduped: list[JobListing] = []
    for listing in listings:
        key = dedupe_fingerprint(listing)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(listing)
    return deduped


def drop_applied_listings(
    listings: list[JobListing],
    *,
    user_id: int,
) -> list[JobListing]:
    applied = load_applied_signatures(user_id)
    return [listing for listing in listings if not is_already_applied(listing, applied)]


def run_prefilter(
    raw_listings: list[RawJobListing],
    *,
    user_id: int,
) -> tuple[list[JobListing], list[JobListing]]:
    """Normalize, dedupe, and remove jobs the user already applied to."""
    listings: list[JobListing] = []
    for raw in raw_listings:
        normalized = normalize_raw_listing(raw)
        if normalized is not None:
            listings.append(normalized)

    listings = dedupe_listings(listings)
    matched_jobs = drop_applied_listings(listings, user_id=user_id)
    return listings, matched_jobs
