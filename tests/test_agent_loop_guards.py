"""Tests for agent loop empty-json guards."""

from worker.agent_loop import _reject_empty_json_reply, _stale_ref_failure


def test_posts_rejects_empty_without_opening_post():
    assert _reject_empty_json_reply(
        phase="posts",
        target=2,
        listings_found=0,
        llm_step=8,
        max_steps=40,
        min_steps=8,
        successful_post_clicks=0,
    )


def test_posts_allows_empty_after_successful_click_at_min_steps():
    assert not _reject_empty_json_reply(
        phase="posts",
        target=2,
        listings_found=0,
        llm_step=8,
        max_steps=40,
        min_steps=8,
        successful_post_clicks=1,
    )


def test_jobs_uses_llm_step_floor_not_bootstrap():
    assert _reject_empty_json_reply(
        phase="jobs",
        target=2,
        listings_found=0,
        llm_step=5,
        max_steps=40,
        min_steps=12,
        successful_post_clicks=0,
    )
    assert not _reject_empty_json_reply(
        phase="jobs",
        target=2,
        listings_found=0,
        llm_step=12,
        max_steps=40,
        min_steps=12,
        successful_post_clicks=0,
    )


def test_stale_ref_failure_detects_extension_error():
    payload = (
        '{"ok": false, "error": {"code": "extension_error", '
        '"message": "{\\"message\\":\\"Node with given id does not belong to the document\\"}"}}'
    )
    assert _stale_ref_failure(payload)
