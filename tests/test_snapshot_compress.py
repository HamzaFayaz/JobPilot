"""Tests for WebBridge snapshot semantic compression."""

import json
from pathlib import Path

from worker.snapshot_compress import compress_snapshot

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
    refs = {node["ref"] for node in compressed["nodes"]}
    blob = json.dumps(compressed, ensure_ascii=False)

    assert "search/results/content" in compressed["url"].lower()
    assert "We're Hiring" in blob
    assert "AI Engineer | Lahore" in blob
    assert "@e130" in refs
    assert "Jobs, 0 new notifications" not in blob
    assert len(compressed["nodes"]) < 40


def test_compress_output_shape_has_no_children():
    compressed = compress_snapshot(_load_fixture_snapshot(RUN28_FIXTURE))
    assert "nodes" in compressed
    assert "tree" not in compressed
    for node in compressed["nodes"]:
        assert set(node.keys()) == {"ref", "role", "name"}
        assert node["ref"].startswith("@e")

