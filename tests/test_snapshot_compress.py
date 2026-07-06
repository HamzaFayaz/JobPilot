"""Tests for WebBridge snapshot semantic compression."""

import json
from pathlib import Path

from worker.snapshot_compress import (
    compress_snapshot,
    count_jobs_in_search_snapshot,
    extract_job_description_from_snapshot,
    extract_posts_from_search_snapshot,
    job_detail_metadata,
    snapshot_has_job_detail_panel,
)

RUN28_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "worker"
    / "debug_snapshots"
    / "run-28"
    / "jobs"
    / "step-06-snapshot.json"
)

RUN32_JOBS_SEARCH_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "worker"
    / "debug_snapshots"
    / "run-32"
    / "jobs"
    / "full"
    / "step-21-snapshot.json"
)

RUN33_POSTS_SEARCH_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "worker"
    / "debug_snapshots"
    / "run-33"
    / "posts"
    / "full"
    / "step-06-snapshot.json"
)

RUN35_POSTS_SEARCH_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "worker"
    / "debug_snapshots"
    / "run-35"
    / "posts"
    / "full"
    / "step-02-snapshot.json"
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


def _load_fixture_snapshot(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    result = payload["result"]
    if isinstance(result.get("data"), dict):
        return result
    return result


def test_compress_run28_jobs_page_retains_job_signals():
    compressed = compress_snapshot(_load_fixture_snapshot(RUN28_FIXTURE))
    blob = json.dumps(compressed, ensure_ascii=False).lower()

    assert "linkedin.com/jobs" in compressed["url"].lower()
    assert "ai engineer" in blob
    assert "easy apply" in blob
    assert "strativ" in blob

    assert "hamza fayaz" not in blob
    assert "earl of eton" not in blob
    assert "13 new notifications" not in blob

    assert len(compressed["nodes"]) < 80
    assert len(json.dumps(compressed)) < len(json.dumps(_load_fixture_snapshot(RUN28_FIXTURE))) / 10


def test_compress_run32_jobs_search_retains_all_result_rows():
    compressed = compress_snapshot(_load_fixture_snapshot(RUN32_JOBS_SEARCH_FIXTURE))
    refs = {node["ref"] for node in compressed["nodes"]}
    blob = json.dumps(compressed, ensure_ascii=False)

    expected_refs = {"@e29", "@e31", "@e33", "@e35", "@e37", "@e39", "@e41"}
    assert expected_refs.issubset(refs)

    assert "AI Engineer | Hyphen Connect | APAC (Remote)" in blob
    assert "AI Specialist (Remote) | Hire Feed" in blob

    assert "@e55" not in refs
    assert '"name": "Remote"' not in blob

    assert "linkedin.com/jobs/search" in compressed["url"].lower()
    assert len(compressed["nodes"]) < 30


def test_compress_run33_posts_search_retains_hiring_posts():
    compressed = compress_snapshot(_load_fixture_snapshot(RUN33_POSTS_SEARCH_FIXTURE))
    blob = json.dumps(compressed, ensure_ascii=False)

    assert "search/results/content" in compressed["url"].lower()
    assert "posts" in compressed
    assert compressed["hiringOpenings"] >= 1
    assert any("We're Hiring" in post.get("title", "") for post in compressed["posts"])
    assert "Jobs, 0 new notifications" not in blob
    assert len(compressed["nodes"]) < 40


def test_extract_posts_run35_includes_company_page_and_filters_debate():
    posts = extract_posts_from_search_snapshot(_load_fixture_snapshot(RUN35_POSTS_SEARCH_FIXTURE))
    titles = [post["title"] for post in posts]
    openings = [post for post in posts if post["isJobOpening"]]

    assert any("Physicist-ML" in title or "CyberWissen" in post["company"] for title, post in zip(titles, posts))
    assert any("We're Hiring" in title for title in titles)
    assert all(not post["isJobOpening"] or "Question to Pakistan" not in post["descriptionText"] for post in posts)
    assert len(openings) >= 2


def test_extract_posts_run36_preserves_full_post_body_not_capped_at_2000():
    posts = extract_posts_from_search_snapshot(_load_fixture_snapshot(RUN36_POSTS_SEARCH_FIXTURE))
    hashmove = next(
        post
        for post in posts
        if "HashMove" in post.get("descriptionText", "") and post.get("isJobOpening")
    )
    assert len(hashmove["descriptionText"]) > 1900
    assert not hashmove["descriptionText"].endswith("…")
    assert "#FutureOfAI" in hashmove["descriptionText"]


def test_compress_run36_posts_search_reports_hiring_openings():
    compressed = compress_snapshot(_load_fixture_snapshot(RUN36_POSTS_SEARCH_FIXTURE))
    assert compressed["hiringOpenings"] >= 2
    devorbis_posts = [
        post
        for post in compressed["posts"]
        if "devorbis.com" in post.get("descriptionText", "").lower()
    ]
    assert devorbis_posts
    assert all(len(post["descriptionText"]) > 200 for post in devorbis_posts)


def test_count_jobs_in_search_snapshot_run32():
    count = count_jobs_in_search_snapshot(_load_fixture_snapshot(RUN32_JOBS_SEARCH_FIXTURE))
    assert count >= 7


def test_compress_output_shape_has_no_children():
    compressed = compress_snapshot(_load_fixture_snapshot(RUN28_FIXTURE))
    assert "nodes" in compressed
    assert "tree" not in compressed
    for node in compressed["nodes"]:
        assert set(node.keys()) == {"ref", "role", "name"}
        assert node["ref"].startswith("@e")


def test_run33_has_job_detail_panel_and_full_jd():
    snapshot = _load_fixture_snapshot(RUN33_JOB_DETAIL_FIXTURE)
    assert snapshot_has_job_detail_panel(snapshot)
    description = extract_job_description_from_snapshot(snapshot)
    assert len(description) >= 500
    assert "machine learning" in description.lower()
    meta = job_detail_metadata(snapshot)
    assert meta["jobDetailReady"] is True
    assert meta["jobDescriptionChars"] == len(description)


def test_run40_job_detail_panel_missing_before_retry():
    snapshot = _load_fixture_snapshot(RUN40_JOB_DETAIL_FIXTURE)
    assert not snapshot_has_job_detail_panel(snapshot)
    assert extract_job_description_from_snapshot(snapshot) == ""
    meta = job_detail_metadata(snapshot)
    assert meta["jobDetailReady"] is False
    assert meta["jobDescriptionChars"] == 0

