"""Tests for listing parse, sanitize, and enrichment."""

import json
from pathlib import Path

from worker.models import RawJobListing
from worker.parse import (
    enrich_agent_listings_json,
    is_synthetic_post_url,
    is_valid_linkedin_post_url,
    listings_from_extracted_posts,
    merge_posts_agent_with_extraction,
    sanitize_and_enrich_listings,
)
from worker.snapshot_compress import (
    extract_job_description_from_snapshot,
    extract_posts_from_search_snapshot,
)

RUN33_JOB_DETAIL_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "worker"
    / "debug_snapshots"
    / "run-33"
    / "jobs"
    / "full"
    / "step-07-snapshot.json"
)

RUN36_POSTS_SEARCH_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "worker"
    / "debug_snapshots"
    / "run-36"
    / "posts"
    / "full"
    / "step-09-snapshot.json"
)


def _load_snapshot(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    result = payload["result"]
    data = result.get("data")
    return data if isinstance(data, dict) else result


def test_extract_job_description_from_snapshot_fixture():
    snapshot = _load_snapshot(RUN33_JOB_DETAIL_FIXTURE)
    description = extract_job_description_from_snapshot(snapshot)
    assert "AI Engineer" in description
    assert "machine learning" in description.lower()


def test_sanitize_fills_description_and_fixes_job_url():
    snapshot = _load_snapshot(RUN33_JOB_DETAIL_FIXTURE)
    listings = [
        RawJobListing(
            title="AI Engineer",
            company="Hyphen Connect",
            url="https://www.linkedin.com/jobs/view/wrong-slug-4433930434/",
            description_text="",
            source_platform="linkedin",
        )
    ]
    enriched = sanitize_and_enrich_listings(
        listings,
        phase="jobs",
        last_snapshot=snapshot,
    )
    assert len(enriched) == 1
    assert "AI Engineer" in enriched[0].description_text
    assert enriched[0].url == "https://www.linkedin.com/jobs/view/4433930433/"


def test_sanitize_drops_hire_feed_mismatched_url():
    snapshot = _load_snapshot(RUN33_JOB_DETAIL_FIXTURE)
    listings = [
        RawJobListing(
            title="AI Specialist (Remote)",
            company="Hire Feed",
            url="https://www.linkedin.com/jobs/view/maintenance-operator-999/",
            description_text="",
            source_platform="linkedin",
        )
    ]
    enriched = sanitize_and_enrich_listings(
        listings,
        phase="jobs",
        last_snapshot=snapshot,
    )
    assert enriched == []


def test_sanitize_drops_invalid_post_profile_url():
    listings = [
        RawJobListing(
            title="We're Hiring",
            company="Acme",
            url="https://www.linkedin.com/in/someone/",
            description_text="Hiring AI Engineer",
            source_platform="linkedin",
        )
    ]
    enriched = sanitize_and_enrich_listings(listings, phase="posts")
    assert enriched == []


def test_valid_post_url_patterns():
    assert is_valid_linkedin_post_url(
        "https://www.linkedin.com/feed/update/urn:li:activity:123/"
    )
    assert not is_valid_linkedin_post_url("https://www.linkedin.com/in/person/")


def test_enrich_agent_listings_json_round_trip():
    snapshot = _load_snapshot(RUN33_JOB_DETAIL_FIXTURE)
    raw = json.dumps(
        [
            {
                "title": "AI Engineer",
                "company": "Hyphen Connect",
                "url": "https://www.linkedin.com/jobs/view/bad-slug/",
                "descriptionText": "",
                "sourcePlatform": "linkedin",
            }
        ]
    )
    enriched = enrich_agent_listings_json(
        raw,
        platform="linkedin",
        phase="jobs",
        last_snapshot=snapshot,
    )
    payload = json.loads(enriched)
    assert payload[0]["descriptionText"]
    assert payload[0]["url"].endswith("/4433930433/")


def test_listings_from_extracted_posts_run36_includes_posts_without_url():
    snapshot = _load_snapshot(RUN36_POSTS_SEARCH_FIXTURE)
    posts = extract_posts_from_search_snapshot(snapshot)
    listings = listings_from_extracted_posts(posts, platform="linkedin", max_listings=4)

    assert len(listings) >= 2
    assert all(listing.description_text for listing in listings)
    assert all(is_synthetic_post_url(listing.url) for listing in listings)
    assert any("samiullah.aizaz@devorbis.com" in listing.description_text for listing in listings)
    assert all("Question to Pakistan" not in listing.description_text for listing in listings)


def test_sanitize_keeps_synthetic_post_url():
    listings = [
        RawJobListing(
            title="We're Hiring – AI Engineer",
            company="Devorbis",
            url="linkedin-post://abc123def456",
            description_text="Apply at laiba@devorbis.com",
            source_platform="linkedin",
        )
    ]
    enriched = sanitize_and_enrich_listings(listings, phase="posts")
    assert len(enriched) == 1
    assert is_synthetic_post_url(enriched[0].url)


def test_merge_posts_agent_with_extraction_prefers_worker_posts():
    snapshot = _load_snapshot(RUN36_POSTS_SEARCH_FIXTURE)
    merged = merge_posts_agent_with_extraction(
        "[]",
        platform="linkedin",
        last_snapshot=snapshot,
        target=2,
    )
    payload = json.loads(merged)
    assert len(payload) >= 2
    assert all(item["descriptionText"] for item in payload)
    assert any("devorbis.com" in item["descriptionText"].lower() for item in payload)


def test_sanitize_drops_job_without_description_when_no_snapshot_text():
    listings = [
        RawJobListing(
            title="AI Engineer",
            company="Acme",
            url="https://www.linkedin.com/jobs/view/1234567890/",
            description_text="",
            source_platform="linkedin",
        )
    ]
    enriched = sanitize_and_enrich_listings(listings, phase="jobs", last_snapshot=None)
    assert enriched == []
