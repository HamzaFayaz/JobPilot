"""Tests for agent loop empty-json guards."""

import json
from pathlib import Path

from worker.agent_loop import (
    _accumulated_jobs_missing_description,
    _job_detail_not_ready,
    _job_listings_missing_description,
    _merge_jobs_into_accumulated,
    _next_job_click_hints,
    _reject_empty_json_reply,
    _reject_incomplete_jobs_reply,
    _stale_ref_failure,
    _sync_jobs_progress_message,
)
from worker.models import RawJobListing

RUN33_JOB_DETAIL_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "worker"
    / "debug_snapshots"
    / "run-33"
    / "jobs"
    / "full"
    / "step-07-snapshot.json"
)

RUN40_JOB_DETAIL_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "worker"
    / "debug_snapshots"
    / "run-40"
    / "jobs"
    / "full"
    / "step-04-snapshot.json"
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


def test_jobs_accepts_when_target_met_even_if_descriptions_missing():
    assert not _reject_incomplete_jobs_reply(
        phase="jobs",
        target=3,
        listings_found=3,
        llm_step=10,
        max_steps=40,
        job_rows_visible=7,
        raw_text='[{"title":"AI Engineer","company":"Acme","url":"https://www.linkedin.com/jobs/search/?currentJobId=1","descriptionText":"","sourcePlatform":"linkedin"}]',
        platform="linkedin",
        last_snapshot=None,
        accumulated_jobs={
            "1": RawJobListing(
                title="AI Engineer",
                company="Acme",
                url="https://www.linkedin.com/jobs/search/?currentJobId=1",
                source_platform="linkedin",
            ),
            "2": RawJobListing(
                title="ML Engineer",
                company="Beta",
                url="https://www.linkedin.com/jobs/search/?currentJobId=2",
                source_platform="linkedin",
            ),
            "3": RawJobListing(
                title="Data Engineer",
                company="Gamma",
                url="https://www.linkedin.com/jobs/search/?currentJobId=3",
                source_platform="linkedin",
            ),
        },
        job_descriptions={},
    )


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


def test_jobs_accepts_at_target_when_description_empty_but_snapshot_has_jd():
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
    assert not _reject_incomplete_jobs_reply(
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


def test_jobs_accepts_at_target_when_detail_panel_not_ready_run40():
    snapshot = _load_snapshot(RUN40_JOB_DETAIL_FIXTURE)
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
    assert _job_detail_not_ready(snapshot, raw_text=raw, platform="linkedin")
    assert not _reject_incomplete_jobs_reply(
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


def test_merge_jobs_into_accumulated_keeps_distinct_titles_with_same_url():
    accumulated: dict[str, RawJobListing] = {}
    shared_url = "https://www.linkedin.com/jobs/search/?currentJobId=4433930433"
    raw = json.dumps(
        [
            {
                "title": "AI Engineer",
                "company": "Hyphen Connect",
                "url": shared_url,
                "descriptionText": "",
                "sourcePlatform": "linkedin",
            },
            {
                "title": "AI/ML Engineer (Remote)",
                "company": "Hire Feed",
                "url": shared_url,
                "descriptionText": "",
                "sourcePlatform": "linkedin",
            },
            {
                "title": "AI Engineer (LInE)",
                "company": "micro1",
                "url": shared_url,
                "descriptionText": "",
                "sourcePlatform": "linkedin",
            },
        ]
    )
    _merge_jobs_into_accumulated(accumulated, raw, platform="linkedin", last_snapshot=None)
    assert len(accumulated) == 3


def test_jobs_reject_uses_json_count_not_accumulated_only():
    assert not _reject_incomplete_jobs_reply(
        phase="jobs",
        target=3,
        listings_found=3,
        llm_step=7,
        max_steps=40,
        job_rows_visible=7,
        raw_text="[]",
        platform="linkedin",
        last_snapshot=None,
        accumulated_jobs={
            "hyphen connect::ai engineer": RawJobListing(
                title="AI Engineer",
                company="Hyphen Connect",
                url="https://www.linkedin.com/jobs/search/?currentJobId=4433930433",
                source_platform="linkedin",
            )
        },
        job_descriptions={},
    )


def test_merge_jobs_into_accumulated_dedupes_by_job_id():
    accumulated: dict[str, RawJobListing] = {}
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
    _merge_jobs_into_accumulated(accumulated, raw, platform="linkedin", last_snapshot=None)
    _merge_jobs_into_accumulated(accumulated, raw, platform="linkedin", last_snapshot=None)
    assert len(accumulated) == 1


def test_accumulated_jobs_missing_description():
    accumulated = {
        "4433930433": RawJobListing(
            title="AI Engineer",
            company="Hyphen Connect",
            url="https://www.linkedin.com/jobs/view/4433930433/",
            source_platform="linkedin",
        )
    }
    assert _accumulated_jobs_missing_description(accumulated, {})
    assert not _accumulated_jobs_missing_description(
        accumulated,
        {"4433930433": "Full job description text here."},
    )


def test_sync_jobs_progress_message_replaces_in_place():
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "task"},
        {"role": "user", "content": "Jobs progress:\nfirst"},
    ]
    _sync_jobs_progress_message(messages, "second hint")
    assert messages[-1]["content"] == "Jobs progress:\nsecond hint"
    assert len(messages) == 3


def test_next_job_click_hints_skips_collected_company():
    snapshot = _load_snapshot(RUN40_JOB_DETAIL_FIXTURE)
    accumulated = {
        "4433930433": RawJobListing(
            title="AI Engineer",
            company="Hyphen Connect",
            url="https://www.linkedin.com/jobs/view/4433930433/",
            source_platform="linkedin",
        )
    }
    hints = _next_job_click_hints(snapshot, accumulated)
    assert hints
    assert "Hyphen Connect" not in hints[0]
