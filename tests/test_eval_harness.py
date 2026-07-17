"""Fast tests for the explicit real-cost evaluation harness itself."""

import json
import shutil

from backend.app.config import settings
from backend.app.db import get_connection
from tests.evals.dataset import deterministic_dataset, semantic_dataset
from tests.evals.models import EvaluationCaseInput
from tests.evals.run_complete_pipeline import (
    _checkpoint_embedding_model_matches,
    _restore_phase1_checkpoint,
    _save_phase1_checkpoint,
    _write_reports,
)


def _case(phase: str) -> EvaluationCaseInput:
    return EvaluationCaseInput(
        phase=phase,
        case_name="shared_job_name",
        payload={"fixture": True},
        deterministic_checks={"contract_ok": True},
    )


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
