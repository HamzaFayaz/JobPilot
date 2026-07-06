"""Tests for worker-owned job view page enrichment snapshots."""

import json
from pathlib import Path

from worker.snapshot_store import save_job_enrich_result


def test_save_job_enrich_result_writes_per_job_folder(tmp_path: Path):
    path = save_job_enrich_result(
        tmp_path,
        run_id=48,
        job_id="4433930433",
        tool_name="snapshot",
        args={},
        result={"ok": True, "data": {"url": "https://www.linkedin.com/jobs/view/4433930433/"}},
        compressed_result={"jobDetailReady": True, "jobDescriptionChars": 1200},
    )
    assert path is not None
    job_dir = tmp_path / "run-48" / "jobs" / "enrich" / "job-4433930433"
    assert (job_dir / "snapshot.json").exists()
    assert (job_dir / "snapshot-compressed.json").exists()
    compressed = json.loads((job_dir / "snapshot-compressed.json").read_text(encoding="utf-8"))
    assert compressed["jobId"] == "4433930433"
    assert compressed["compressed"]["jobDetailReady"] is True
