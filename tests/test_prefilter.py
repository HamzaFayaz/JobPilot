"""Tests for listing prefilter — normalize, dedupe, drop applied."""

from backend.app.db import get_connection
from backend.app.graph.nodes.prefilter import prefilter
from backend.app.graph.state import RunState
from backend.app.models.browser import RawJobListing
from backend.app.services.listing_prefilter import (
    dedupe_listings,
    is_synthetic_post_url,
    normalize_raw_listing,
    run_prefilter,
    synthetic_post_url,
)


def _raw(
    *,
    title: str = "AI Engineer",
    company: str = "Devorbis",
    url: str = "",
    description: str = "Apply at laiba@devorbis.com. Python required.",
    platform: str = "linkedin",
) -> RawJobListing:
    return RawJobListing(
        title=title,
        company=company,
        url=url,
        descriptionText=description,
        sourcePlatform=platform,
    )


def test_normalize_drops_missing_description():
    assert normalize_raw_listing(_raw(description="")) is None


def test_normalize_keeps_missing_title_uses_description_line():
    listing = normalize_raw_listing(
        _raw(title="", description="Hiring Python Developer\nSend CV to hr@acme.com")
    )
    assert listing is not None
    assert listing["title"] == "Hiring Python Developer"
    assert listing["company"] == "Devorbis"


def test_normalize_defaults_missing_company():
    listing = normalize_raw_listing(_raw(company="", description="Full post body here."))
    assert listing is not None
    assert listing["company"] == "Unknown"


def test_normalize_assigns_synthetic_url_when_missing():
    description = "Apply at laiba@devorbis.com"
    listing = normalize_raw_listing(_raw(url="", description=description))
    assert listing is not None
    assert is_synthetic_post_url(listing["url"])
    assert listing["url"] == synthetic_post_url("Devorbis", "AI Engineer", description)


def test_normalize_maps_platform_field():
    listing = normalize_raw_listing(_raw())
    assert listing is not None
    assert listing["platform"] == "linkedin"


def test_dedupe_by_same_url():
    first = normalize_raw_listing(_raw(url="https://www.linkedin.com/jobs/view/123/")) 
    second = normalize_raw_listing(
        _raw(
            title="Duplicate title",
            url="https://www.linkedin.com/jobs/view/123",
            description="Different text but same job id.",
        )
    )
    assert first is not None and second is not None
    deduped = dedupe_listings([first, second])
    assert len(deduped) == 1


def test_dedupe_by_same_contact_email():
    first = normalize_raw_listing(
        _raw(
            title="Role A",
            url="",
            description="Reach us at same.role@company.com for details.",
        )
    )
    second = normalize_raw_listing(
        _raw(
            title="Role B",
            url="",
            description="Email same.role@company.com to apply today.",
        )
    )
    assert first is not None and second is not None
    deduped = dedupe_listings([first, second])
    assert len(deduped) == 1


def test_drop_applied_by_title_and_company(test_db):
    user_id = 1
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO users (id, email, password_hash)
            VALUES (1, 'user@example.com', 'hash')
            """
        )
        conn.execute(
            """
            INSERT INTO job_applications (user_id, url, platform, title, company, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, "", "linkedin", "AI Engineer", "Devorbis", "sent"),
        )
        conn.commit()

    listings, matched = run_prefilter([_raw()], user_id=user_id)
    assert len(listings) == 1
    assert matched == []


def test_prefilter_node_returns_matched_jobs(test_db):
    raw = _raw()
    listing = normalize_raw_listing(raw)
    assert listing is not None

    state: RunState = {
        "run_id": 1,
        "user_id": 1,
        "role": "AI Engineer",
        "platform": "linkedin",
        "country": "Pakistan",
        "work_mode": "both",
        "max_listings": 8,
        "job_age": "week",
        "profile": {
            "cv_text": "",
            "skills": [],
            "target_roles": [],
            "projects": [],
        },
        "listings": [],
        "raw_listings": [raw],
        "warnings": [],
        "matched_jobs": [],
        "packages": [],
        "errors": [],
        "status": "running",
    }

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO users (id, email, password_hash)
            VALUES (1, 'node@example.com', 'hash')
            """
        )
        conn.execute(
            """
            INSERT INTO search_runs (id, user_id, status)
            VALUES (1, 1, 'running')
            """
        )
        conn.commit()

    result = prefilter(state)
    assert len(result["listings"]) == 1
    assert len(result["matched_jobs"]) == 1
    assert is_synthetic_post_url(result["matched_jobs"][0]["url"])
    with get_connection() as conn:
        packages = conn.execute(
            "SELECT status FROM job_packages WHERE run_id = 1"
        ).fetchall()
    assert len(packages) == 1
    assert packages[0]["status"] == "analyzing"
