"""Tests for worker prompt budgets and listing merge."""

from worker.models import RawJobListing, WorkerTask
from worker.parse import merge_listings
from worker.prompts import (
    LINKEDIN_JOBS_STEP_FLOOR,
    build_linkedin_jobs_task,
    build_linkedin_posts_task,
    linkedin_jobs_steps,
    linkedin_phase_steps,
    listing_targets,
    max_steps_for_target,
)


def test_listing_targets_split():
    assert listing_targets(4) == (2, 2)
    assert listing_targets(1) == (1, 0)
    assert listing_targets(8) == (4, 4)


def test_max_steps_for_target_scales_with_listings():
    assert max_steps_for_target(0) == 0
    assert max_steps_for_target(2) == 6
    assert max_steps_for_target(4) == 12
    assert max_steps_for_target(10) == 15


def test_linkedin_phase_steps_uses_workflow_floor():
    assert linkedin_phase_steps(2, floor=LINKEDIN_JOBS_STEP_FLOOR) == 12
    assert linkedin_phase_steps(5, floor=LINKEDIN_JOBS_STEP_FLOOR) == 15
    assert linkedin_phase_steps(0, floor=LINKEDIN_JOBS_STEP_FLOOR) == 0
    assert linkedin_jobs_steps(2) == 12
    assert linkedin_jobs_steps(5) == 15


def test_posts_prompt_forbids_renavigate_and_requires_snapshot_before_click():
    task = WorkerTask(
        taskId="t1",
        runId=34,
        role="AI Engineer",
        platform="linkedin",
        country="Pakistan",
        workMode="both",
        maxListings=4,
        jobAge="week",
        maxJobAgeDays=7,
        skillsSummary="Python",
    )
    prompt = build_linkedin_posts_task(task, target=2)
    assert "do NOT call navigate to the search URL again" in prompt
    assert "snapshot the results list" in prompt.lower()


def test_jobs_prompt_reads_description_from_snapshot():
    task = WorkerTask(
        taskId="t1",
        runId=34,
        role="AI Engineer",
        platform="linkedin",
        country="Pakistan",
        workMode="both",
        maxListings=4,
        jobAge="week",
        maxJobAgeDays=7,
        skillsSummary="Python",
    )
    prompt = build_linkedin_jobs_task(task, target=2)
    assert "About the job" in prompt
    assert "window.location.href" in prompt
    assert "Do NOT use evaluate with CSS selectors" in prompt


def test_merge_listings_dedupes_by_url():
    listings = [
        RawJobListing(
            title="A",
            company="Co",
            url="https://example.com/1",
            source_platform="linkedin",
        ),
        RawJobListing(
            title="A duplicate",
            company="Co",
            url="https://example.com/1",
            source_platform="linkedin",
        ),
        RawJobListing(
            title="B",
            company="Co",
            url="https://example.com/2",
            source_platform="linkedin",
        ),
    ]
    merged = merge_listings(listings, max_listings=4)
    assert len(merged) == 2
    assert merged[0].title == "A"
    assert merged[1].title == "B"
