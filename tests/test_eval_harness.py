"""Fast tests for the explicit real-cost evaluation harness itself."""

import json
import shutil

from backend.app.config import settings
from backend.app.db import get_connection
from tests.evals.dataset import deterministic_dataset, semantic_dataset
from tests.evals.models import EvaluationCaseInput
from tests.evals.run_complete_pipeline import (
    RUN3_FOUR_JOB_CHECKPOINT_SCHEMA,
    RUN3_JOB_CHECKPOINT_SCHEMA,
    RUN3_PREJUDGE_CHECKPOINT_SCHEMA,
    _checkpoint_embedding_model_matches,
    _four_job_checkpoint_path,
    _job_checkpoint_path,
    _job_input_fingerprint,
    _load_matching_job_checkpoint,
    _prejudge_checkpoint_path,
    _restore_job_checkpoint_into_run,
    _restore_phase1_checkpoint,
    _run3_fingerprints,
    _save_phase1_checkpoint,
    _write_four_job_checkpoint,
    _write_job_checkpoint,
    _write_prejudge_checkpoint,
    _write_reports,
)


def _case(phase: str) -> EvaluationCaseInput:
    return EvaluationCaseInput(
        phase=phase,
        case_name="shared_job_name",
        payload={"fixture": True},
        deterministic_checks={"contract_ok": True},
    )


def _job_fixture(case_name: str = "job1_deerbiation") -> dict:
    return {
        "case_name": case_name,
        "title": "AI Engineer",
        "company": "Acme",
        "url": f"https://example.com/jobs/{case_name}",
        "platform": "linkedin",
        "description_text": "Required: Python.",
    }


def _envelope() -> dict:
    return {
        "schema_version": "job_package_analysis_v3",
        "raw_model_result": "{}",
        "raw_model_attempts": ["{}"],
        "parsed_model_result": {"current_cv_score": 70},
        "accepted_model_result": {"current_cv_score": 70},
        "enrich_result": {"current_cv_score": 70},
        "classified_result": {
            "current_cv_score": 70,
            "suggested_cv_score": 70,
            "summary": "ok",
        },
        "contract_validation": {"valid": True, "errors": []},
        "requirement_extraction": {"requirements": []},
        "retrieval_bundle": {"layer2b_readme_chunks": []},
        "retrieval": {
            "packed_chunk_ids": ["chunk-1"],
            "packed_project_ids": ["jobpilot"],
            "retrieval_supply": {},
            "fallback_reasons": [],
        },
        "error": None,
    }


def test_phase_prefixes_make_case_names_unique_and_reports_serialize(
    tmp_path, monkeypatch
):
    cases = [_case("phase_2_retrieval"), _case("phase_3_application")]
    deterministic = deterministic_dataset(cases).evaluate_sync(
        lambda raw: raw, progress=False
    )

    def fake_judge(raw):
        return {
            "phase": raw["phase"],
            "case_name": raw["case_name"],
            "criteria": {
                "grounding": {
                    "score": 3,
                    "verdict": "pass",
                    "reason": "Grounded.",
                }
            },
            "reasonable_current_score_range": (
                [60, 75] if raw["phase"] == "phase_3_application" else None
            ),
            "unsupported_claims": [],
            "hard_failures": [],
            "overall_verdict": "pass",
            "human_review_required": False,
        }

    semantic = semantic_dataset(cases).evaluate_sync(fake_judge, progress=False)
    monkeypatch.setattr(
        "tests.evals.run_complete_pipeline.settings.eval_results_dir", tmp_path
    )
    json_path, markdown_path = _write_reports(cases, deterministic, semantic)
    assert json_path.exists()
    assert markdown_path.exists()
    assert len({case.name for case in deterministic.cases}) == 2


def test_phase1_checkpoint_restores_database_faiss_profile_and_cases(
    test_db, tmp_path, monkeypatch
):
    results = tmp_path / "results"
    monkeypatch.setattr(settings, "eval_results_dir", results)
    settings.faiss_dir.mkdir(parents=True, exist_ok=True)
    (settings.faiss_dir / "1.index").write_bytes(b"index")
    (settings.faiss_dir / "1.meta.json").write_text(
        json.dumps(
            {
                "embedding_model": settings.embedding_model,
                "embedding_dims": settings.embedding_dimensions,
            }
        ),
        encoding="utf-8",
    )
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            ("checkpoint@example.com", "hash"),
        )
        user_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
        conn.commit()

    profile = {
        "cv_text": "Private CV",
        "skills": ["Python"],
        "target_roles": ["Engineer"],
        "projects": [],
    }
    cases = [_case("phase_1_cv_skills")]
    _save_phase1_checkpoint(user_id, profile, cases)

    settings.db_path.unlink()
    shutil.rmtree(settings.faiss_dir)
    restored = _restore_phase1_checkpoint()
    assert restored is not None
    restored_user_id, restored_profile, restored_cases = restored
    assert restored_user_id == user_id
    assert restored_profile == profile
    assert restored_cases[0].phase == "phase_1_cv_skills"
    assert (settings.faiss_dir / "1.index").read_bytes() == b"index"
    with get_connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1


def test_checkpoint_rejects_fallback_embedding_model(tmp_path):
    faiss = tmp_path / "faiss"
    faiss.mkdir()
    (faiss / "1.meta.json").write_text(
        json.dumps(
            {
                "embedding_model": settings.embedding_fallback_model,
                "embedding_dims": settings.embedding_dimensions,
            }
        ),
        encoding="utf-8",
    )
    assert _checkpoint_embedding_model_matches(tmp_path, 1) is False


def test_prejudge_checkpoint_preserves_cases_and_run_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "eval_results_dir", tmp_path)
    path = _write_prejudge_checkpoint(
        [_case("phase_3_application")],
        {"evaluation_run_id": 7, "trace_id": "abc"},
    )
    assert path == _prejudge_checkpoint_path()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == RUN3_PREJUDGE_CHECKPOINT_SCHEMA
    assert payload["cases"][0]["phase"] == "phase_3_application"
    assert payload["run_metadata"]["evaluation_run_id"] == 7
    assert (tmp_path / "run3-prejudge-checkpoint.json").exists()


def test_per_job_checkpoint_save_and_reuse(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "eval_results_dir", tmp_path)
    job = _job_fixture()
    fingerprints = {
        "implementation_commit": "abc",
        "prompt_schema_config": "cfg",
        "profile": "profile",
        "index": "index",
        "artifact": "artifact",
    }
    retrieval = _case("phase_2_retrieval")
    retrieval.case_name = job["case_name"]
    application = _case("phase_3_application")
    application.case_name = job["case_name"]
    path = _write_job_checkpoint(
        job=job,
        fingerprints=fingerprints,
        envelope=_envelope(),
        persisted={
            "status": "ready",
            "summary": "ok",
            "current_cv_score": 70,
            "suggested_cv_score": 70,
            "model_name": "test-model",
            "prompt_version": "enrich_job_v3",
            "profile_snapshot_hash": "sha256:test",
            "package_key": "pkg-key",
            "error": None,
        },
        retrieval_case=retrieval,
        application_case=application,
    )
    assert path == _job_checkpoint_path(job["case_name"])
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == RUN3_JOB_CHECKPOINT_SCHEMA
    assert payload["fingerprints"]["job_input"] == _job_input_fingerprint(job)
    reused = _load_matching_job_checkpoint(job, fingerprints)
    assert reused is not None
    assert reused["case_name"] == job["case_name"]


def test_per_job_checkpoint_rejects_stale_fingerprints(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "eval_results_dir", tmp_path)
    job = _job_fixture()
    fingerprints = {
        "implementation_commit": "abc",
        "prompt_schema_config": "cfg",
        "profile": "profile",
        "index": "index",
        "artifact": "artifact",
    }
    retrieval = _case("phase_2_retrieval")
    retrieval.case_name = job["case_name"]
    application = _case("phase_3_application")
    application.case_name = job["case_name"]
    _write_job_checkpoint(
        job=job,
        fingerprints=fingerprints,
        envelope=_envelope(),
        persisted={
            "status": "ready",
            "summary": "ok",
            "current_cv_score": 70,
            "suggested_cv_score": 70,
            "package_key": "pkg-key",
            "error": None,
        },
        retrieval_case=retrieval,
        application_case=application,
    )
    stale = dict(fingerprints)
    stale["implementation_commit"] = "different"
    assert _load_matching_job_checkpoint(job, stale) is None
    changed_job = dict(job)
    changed_job["description_text"] = "Changed description"
    assert _load_matching_job_checkpoint(changed_job, fingerprints) is None


def test_interrupted_run_resumes_only_unfinished_jobs(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "eval_results_dir", tmp_path)
    fingerprints = {
        "implementation_commit": "abc",
        "prompt_schema_config": "cfg",
        "profile": "profile",
        "index": "index",
        "artifact": "artifact",
    }
    finished = _job_fixture("job1_deerbiation")
    unfinished = _job_fixture("job2_deerbiation")
    retrieval = _case("phase_2_retrieval")
    retrieval.case_name = finished["case_name"]
    application = _case("phase_3_application")
    application.case_name = finished["case_name"]
    _write_job_checkpoint(
        job=finished,
        fingerprints=fingerprints,
        envelope=_envelope(),
        persisted={
            "status": "ready",
            "summary": "ok",
            "current_cv_score": 70,
            "suggested_cv_score": 70,
            "package_key": "pkg-1",
            "error": None,
        },
        retrieval_case=retrieval,
        application_case=application,
    )
    assert _load_matching_job_checkpoint(finished, fingerprints) is not None
    assert _load_matching_job_checkpoint(unfinished, fingerprints) is None


def test_four_job_and_prejudge_checkpoints(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "eval_results_dir", tmp_path)
    jobs = [_job_fixture(f"job{index}_deerbiation") for index in range(1, 5)]
    fingerprints = _run3_fingerprints(
        {"cv_text": "cv", "skills": [], "target_roles": [], "projects": []}
    )
    four_path = _write_four_job_checkpoint(
        jobs=jobs,
        fingerprints=fingerprints,
        job_artifacts=[
            {"case_name": job["case_name"], "source": "live"} for job in jobs
        ],
        run_id=9,
        persistence_state={"run_status": "completed", "expected_ready": 4},
    )
    assert four_path == _four_job_checkpoint_path()
    four_payload = json.loads(four_path.read_text(encoding="utf-8"))
    assert four_payload["schema_version"] == RUN3_FOUR_JOB_CHECKPOINT_SCHEMA
    assert four_payload["job_case_names"] == [job["case_name"] for job in jobs]

    cases = [_case("phase_1_cv_skills")]
    for job in jobs:
        cases.append(
            EvaluationCaseInput(
                phase="phase_2_retrieval",
                case_name=job["case_name"],
                payload={"job": job},
                deterministic_checks={"ok": True},
            )
        )
        cases.append(
            EvaluationCaseInput(
                phase="phase_3_application",
                case_name=job["case_name"],
                payload={"job": job},
                deterministic_checks={"ok": True},
            )
        )
    while len(cases) < 17:
        cases.append(
            EvaluationCaseInput(
                phase="phase_1_project_evidence",
                case_name=f"project_{len(cases)}",
                payload={},
                deterministic_checks={"ok": True},
            )
        )
    prejudge = _write_prejudge_checkpoint(cases, {"evaluation_run_id": 9})
    payload = json.loads(prejudge.read_text(encoding="utf-8"))
    assert len(payload["cases"]) == 17
    assert prejudge == _prejudge_checkpoint_path()


def test_restore_job_checkpoint_into_run_skips_paid_path(test_db, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "eval_results_dir", tmp_path)
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            ("resume@example.com", "hash"),
        )
        user_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
        conn.execute(
            "INSERT INTO search_runs (user_id, status) VALUES (?, 'running')",
            (user_id,),
        )
        run_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
        conn.commit()
    job = _job_fixture()
    fingerprints = {
        "implementation_commit": "abc",
        "prompt_schema_config": "cfg",
        "profile": "profile",
        "index": "index",
        "artifact": "artifact",
    }
    retrieval = _case("phase_2_retrieval")
    retrieval.case_name = job["case_name"]
    application = _case("phase_3_application")
    application.case_name = job["case_name"]
    _write_job_checkpoint(
        job=job,
        fingerprints=fingerprints,
        envelope=_envelope(),
        persisted={
            "status": "ready",
            "summary": "ok",
            "current_cv_score": 70,
            "suggested_cv_score": 70,
            "package_key": "pkg-key",
            "model_name": "test-model",
            "prompt_version": "enrich_job_v3",
            "profile_snapshot_hash": "sha256:test",
            "error": None,
        },
        retrieval_case=retrieval,
        application_case=application,
    )
    checkpoint = _load_matching_job_checkpoint(job, fingerprints)
    restored_cases = _restore_job_checkpoint_into_run(
        run_id=run_id,
        user_id=user_id,
        job=job,
        checkpoint=checkpoint,
    )
    assert len(restored_cases) == 2
    with get_connection() as conn:
        row = conn.execute(
            "SELECT status, analysis_json FROM job_packages WHERE run_id = ?",
            (run_id,),
        ).fetchone()
    assert row["status"] == "ready"
    assert json.loads(row["analysis_json"])["classified_result"]["current_cv_score"] == 70
