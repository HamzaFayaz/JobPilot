"""Tests for agent loop empty-json guards."""

import json
from pathlib import Path

from worker.agent_loop import (
    _job_listings_missing_description,
    _reject_empty_json_reply,
    _reject_incomplete_jobs_reply,
    _stale_ref_failure,
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


def _load_snapshot(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    result = payload["result"]
    data = result.get("data")
    return data if isinstance(data, dict) else result


def test_posts_rejects_empty_when_hiring_openings_visible():
    assert _reject_empty_json_reply(
        phase="posts",
        target=2,
        listings_found=0,
        llm_step=10,
        max_steps=40,
        min_steps=8,
        hiring_openings_visible=2,
    )


def test_posts_allows_empty_when_no_openings_at_min_steps():
    assert not _reject_empty_json_reply(
        phase="posts",
        target=2,
        listings_found=0,
        llm_step=8,
        max_steps=40,
        min_steps=8,
        hiring_openings_visible=0,
    )


def test_jobs_uses_llm_step_floor_not_bootstrap():
    assert _reject_empty_json_reply(
        phase="jobs",
        target=2,
        listings_found=0,
        llm_step=5,
        max_steps=40,
        min_steps=12,
        hiring_openings_visible=0,
    )
    assert not _reject_empty_json_reply(
        phase="jobs",
        target=2,
        listings_found=0,
        llm_step=12,
        max_steps=40,
        min_steps=12,
        hiring_openings_visible=0,
    )


def test_stale_ref_failure_detects_extension_error():
    payload = (
        '{"ok": false, "error": {"code": "extension_error", '
        '"message": "{\\"message\\":\\"Node with given id does not belong to the document\\"}"}}'
    )
    assert _stale_ref_failure(payload)


def test_jobs_rejects_partial_when_more_rows_visible():
    assert _reject_incomplete_jobs_reply(
        phase="jobs",
        target=2,
        listings_found=1,
        llm_step=10,
        max_steps=40,
        job_rows_visible=5,
        raw_text='[{"title":"AI Engineer","company":"Acme","url":"https://www.linkedin.com/jobs/view/1/","descriptionText":"Full JD text here","sourcePlatform":"linkedin"}]',
        platform="linkedin",
        last_snapshot=None,
    )


def test_jobs_rejects_when_description_missing_but_about_job_in_snapshot():
    snapshot = _load_snapshot(RUN33_JOB_DETAIL_FIXTURE)
    raw = json.dumps(
        [
            {
                "title": "AI Engineer",
                "company": "Hyphen Connect",
                "url": "https://www.linkedin.com/jobs/view/4433930433/",
                "descriptionText": "",
                "sourcePlatform": "linkedin",
            }
        ]
    )
    assert _job_listings_missing_description(raw, platform="linkedin", last_snapshot=snapshot)
    assert _reject_incomplete_jobs_reply(
        phase="jobs",
        target=1,
        listings_found=1,
        llm_step=10,
        max_steps=40,
        job_rows_visible=1,
        raw_text=raw,
        platform="linkedin",
        last_snapshot=snapshot,
    )
