"""Explicit real-cost Phase 1-3 evaluation entry point.

Run with: python -m tests.evals.run_complete_pipeline
"""

from __future__ import annotations

import json
import hashlib
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from cryptography.fernet import Fernet
from fastapi import FastAPI

from backend.app.config import settings
from backend.app.db import get_connection, init_db
from backend.app.graph.subgraphs.application.nodes.classify_fit import classify_fit
from backend.app.observability import setup_observability, span
from backend.app.services import crypto
from backend.app.services.application_llm import analyze_job
from backend.app.services.cv_parser import extract_text_from_docx
from backend.app.services.evidence_indexing import index_project_evidence
from backend.app.services.profile_llm import build_project_evidence, extract_skills
from backend.app.services.profile_store import (
    get_stored_projects,
    merge_github_import,
    update_cv,
)
from tests.evals.dataset import (
    CORPUS_ROOT,
    deterministic_dataset,
    fixture_manifest,
    load_cv_path,
    load_jobs,
    load_projects,
    semantic_dataset,
)
from tests.evals.judge import judge_case
from tests.evals.models import EvaluationCaseInput

PHASE1_CHECKPOINT_SCHEMA = "jobpilot_phase1_checkpoint_v1"


def _results_dir() -> Path:
    path = settings.eval_results_dir
    return path if path.is_absolute() else CORPUS_ROOT.parents[1] / path


def _phase1_fingerprint() -> str:
    phase1_files = [
        item
        for item in fixture_manifest()
        if str(item["path"]).startswith(("cv/", "projects/"))
    ]
    identity = {
        "schema": PHASE1_CHECKPOINT_SCHEMA,
        "fixtures": phase1_files,
        "profile_model": settings.profile_model,
        "evidence_model": settings.evidence_model,
        "embedding_model": settings.embedding_model,
        "embedding_dimensions": settings.embedding_dimensions,
        "chunking": settings.chunking_config,
    }
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _checkpoint_dir() -> Path:
    return _results_dir() / "phase1-checkpoint"


def _restore_phase1_checkpoint() -> tuple[int, dict, list[EvaluationCaseInput]] | None:
    checkpoint = _checkpoint_dir()
    manifest_path = checkpoint / "manifest.json"
    database_path = checkpoint / "eval.db"
    profile_path = checkpoint / "profile.json"
    if not all(path.exists() for path in (manifest_path, database_path, profile_path)):
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("schema_version") != PHASE1_CHECKPOINT_SCHEMA
        or manifest.get("fingerprint") != _phase1_fingerprint()
    ):
        return None

    shutil.copy2(database_path, settings.db_path)
    checkpoint_faiss = checkpoint / "faiss"
    if settings.faiss_dir.exists():
        shutil.rmtree(settings.faiss_dir)
    if checkpoint_faiss.exists():
        shutil.copytree(checkpoint_faiss, settings.faiss_dir)
    else:
        settings.faiss_dir.mkdir(parents=True, exist_ok=True)

    saved = json.loads(profile_path.read_text(encoding="utf-8"))
    return (
        int(saved["user_id"]),
        saved["profile"],
        [
            EvaluationCaseInput.model_validate(case)
            for case in saved["phase1_cases"]
        ],
    )


def _save_phase1_checkpoint(
    user_id: int,
    profile: dict,
    phase1_cases: list[EvaluationCaseInput],
) -> None:
    checkpoint = _checkpoint_dir()
    checkpoint.mkdir(parents=True, exist_ok=True)
    shutil.copy2(settings.db_path, checkpoint / "eval.db")
    checkpoint_faiss = checkpoint / "faiss"
    if checkpoint_faiss.exists():
        shutil.rmtree(checkpoint_faiss)
    if settings.faiss_dir.exists():
        shutil.copytree(settings.faiss_dir, checkpoint_faiss)
    (checkpoint / "profile.json").write_text(
        json.dumps(
            {
                "user_id": user_id,
                "profile": profile,
                "phase1_cases": [
                    case.model_dump(mode="json") for case in phase1_cases
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (checkpoint / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": PHASE1_CHECKPOINT_SCHEMA,
                "fingerprint": _phase1_fingerprint(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "project_count": len(profile.get("projects") or []),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


@contextmanager
def isolated_storage():
    """Temporarily redirect all persistence to a disposable directory."""
    original = {
        "data_dir": settings.data_dir,
        "uploads_dir": settings.uploads_dir,
        "faiss_dir": settings.faiss_dir,
        "db_path": settings.db_path,
        "data_encryption_key": settings.data_encryption_key,
    }
    with tempfile.TemporaryDirectory(prefix="jobpilot-eval-") as directory:
        root = Path(directory)
        settings.data_dir = root
        settings.uploads_dir = root / "uploads"
        settings.faiss_dir = root / "faiss"
        settings.db_path = root / "eval.db"
        settings.data_encryption_key = Fernet.generate_key().decode()
        crypto._fernet = None
        try:
            init_db()
            yield root
        finally:
            for name, value in original.items():
                setattr(settings, name, value)
            crypto._fernet = None


def _create_fixture_user() -> int:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            ("complete-pipeline-eval@jobpilot.local", "not-a-login"),
        )
        user_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
        conn.execute("INSERT INTO profiles (user_id) VALUES (?)", (user_id,))
        conn.commit()
    return user_id


def _cv_text(path: Path) -> str:
    return (
        extract_text_from_docx(path)
        if path.suffix.lower() == ".docx"
        else path.read_text(encoding="utf-8")
    )


def _project_checks(result: dict) -> dict[str, bool]:
    card = result["evidence_card"]
    return {
        "schema_valid": bool(result["portfolio_overview"] and card),
        "required_card_fields": all(
            key in card
            for key in (
                "project_purpose",
                "tech_stack",
                "architecture",
                "key_features",
                "role_relevance",
                "evidence",
                "supported_metrics",
                "limitations_or_unknowns",
            )
        ),
        "evidence_claims_traceable": all(
            bool(item.get("claim") and item.get("source_section"))
            for item in card.get("evidence") or []
        ),
    }


def _retrieval_checks(bundle: dict) -> dict[str, bool]:
    chunks = bundle["layer2b_readme_chunks"]
    ids = [item.get("source_id") for item in chunks]
    max_total = int(settings.retrieval_config.get("max_chunks_per_job", 20))
    per_project: dict[str, int] = {}
    for chunk in chunks:
        project_id = chunk.get("project_id")
        per_project[project_id] = per_project.get(project_id, 0) + 1
    max_per_project = int(
        settings.retrieval_config.get("max_chunks_per_project", 3)
    )
    return {
        "chunk_metadata_complete": all(
            item.get("source_id")
            and item.get("project_id")
            and item.get("project_name")
            and item.get("heading_path")
            and item.get("content")
            for item in chunks
        ),
        "chunk_ids_unique": len(ids) == len(set(ids)),
        "total_cap_respected": len(chunks) <= max_total,
        "per_project_cap_respected": all(
            count <= max_per_project for count in per_project.values()
        ),
        "selected_projects_exist": set(
            bundle["retrieval_debug"]["selected_project_ids"]
        ).issubset(
            {
                item["project_id"]
                for item in bundle["layer1_portfolio_overviews"]
            }
        ),
    }


def _application_checks(result: dict, expected_slots: int) -> dict[str, bool]:
    scores = [result.get("current_cv_score"), result.get("suggested_cv_score")]
    decisions = result.get("project_decisions") or []
    return {
        "scores_valid": all(
            score is None or isinstance(score, int) and 0 <= score <= 100
            for score in scores
        ),
        "one_decision_per_slot": len(decisions) == expected_slots,
        "slot_order_valid": [item["slot_index"] for item in decisions]
        == list(range(expected_slots)),
        "actions_valid": all(
            item["action"] in ("keep", "swap") for item in decisions
        ),
        "replacement_ids_unique": len(
            [
                item["swap_in_project_id"]
                for item in decisions
                if item["action"] == "swap"
            ]
        )
        == len(
            {
                item["swap_in_project_id"]
                for item in decisions
                if item["action"] == "swap"
            }
        ),
        "all_keep_score_invariant": (
            result.get("suggested_cv_score") == result.get("current_cv_score")
            if all(item["action"] == "keep" for item in decisions)
            else True
        ),
    }


def _report_case(case) -> dict:
    raw = asdict(case)
    return {
        "name": raw["name"],
        "output": raw["output"],
        "metrics": raw["metrics"],
        "scores": raw["scores"],
        "labels": raw["labels"],
        "assertions": raw["assertions"],
        "task_duration": raw["task_duration"],
        "total_duration": raw["total_duration"],
        "trace_id": raw["trace_id"],
        "span_id": raw["span_id"],
        "evaluator_failures": raw["evaluator_failures"],
    }


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=CORPUS_ROOT.parents[1],
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _write_reports(
    cases: list[EvaluationCaseInput], deterministic_report, semantic_report
) -> tuple[Path, Path]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    results_dir = settings.eval_results_dir
    if not results_dir.is_absolute():
        results_dir = CORPUS_ROOT.parents[1] / results_dir
    results_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": timestamp,
        "git_commit": _git_commit(),
        "fixture_manifest": fixture_manifest(),
        "configuration": {
            "profile_model": settings.profile_model,
            "evidence_model": settings.evidence_model,
            "embedding_model": settings.embedding_model,
            "rerank_model": settings.rerank_model,
            "application_model": settings.application_model,
            "application_prompt_version": settings.application_prompt_version,
            "application_schema_version": settings.application_schema_version,
            "judge_model": settings.eval_judge_model,
            "judge_rubric_version": "jobpilot_rubric_v1",
            "same_family_judge_bias": (
                "Qwen Max judging Qwen-family outputs is supporting evidence, "
                "not objective ground truth."
            ),
        },
        "deterministic": [_report_case(case) for case in deterministic_report.cases],
        "semantic": [_report_case(case) for case in semantic_report.cases],
        "failures": {
            "deterministic": [asdict(item) for item in deterministic_report.failures],
            "semantic": [asdict(item) for item in semantic_report.failures],
        },
        "human_review_required": True,
    }
    if settings.eval_capture_full_payloads:
        payload["canonical_cases"] = [
            case.model_dump(mode="json") for case in cases
        ]
    json_path = results_dir / f"run-{timestamp}.json"
    md_path = results_dir / f"run-{timestamp}.md"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    verdicts = [
        case.output.get("overall_verdict", "error")
        for case in semantic_report.cases
    ]
    markdown = "\n".join(
        [
            f"# JobPilot evaluation — {timestamp}",
            "",
            f"- Git commit: `{payload['git_commit']}`",
            f"- Deterministic cases: {len(deterministic_report.cases)}",
            f"- Semantic judge cases: {len(semantic_report.cases)}",
            f"- Judge pass/warning/fail: {verdicts.count('pass')}/"
            f"{verdicts.count('warning')}/{verdicts.count('fail')}",
            f"- Judge model: `{settings.eval_judge_model}`",
            "- Same-family bias: Qwen Max judging Qwen outputs is not ground truth.",
            "- Human review is required before accepting this baseline.",
            "",
            f"Full machine-readable report: `{json_path.name}`",
        ]
    )
    md_path.write_text(markdown, encoding="utf-8")
    return json_path, md_path


def _prepare_phase1() -> tuple[int, dict, list[EvaluationCaseInput]]:
    restored = _restore_phase1_checkpoint()
    if restored is not None:
        user_id, profile, cases = restored
        print(
            "Phase 1: restored validated SQLite/FAISS checkpoint; "
            "skipping profile model calls and indexing",
            flush=True,
        )
        return user_id, profile, cases

    print("Phase 1: no valid checkpoint; building isolated profile", flush=True)
    user_id = _create_fixture_user()
    cv_path = load_cv_path()
    cv_text = _cv_text(cv_path)
    print("Phase 1: extracting CV skills (1 model call)", flush=True)
    skills = extract_skills(cv_text)
    print(f"Phase 1: extracted {len(skills)} skills", flush=True)
    update_cv(
        user_id,
        cv_path.name,
        str(cv_path),
        cv_text,
        skills,
        "ready",
    )
    cases: list[EvaluationCaseInput] = [
        EvaluationCaseInput(
            phase="phase_1_cv_skills",
            case_name="cv_skill_extraction",
            payload={"cv_text": cv_text, "skills": skills},
            deterministic_checks={
                "skills_nonempty": bool(skills),
                "skills_normalized": all(
                    isinstance(skill, str) and bool(skill.strip())
                    for skill in skills
                ),
            },
        )
    ]

    imported_projects: list[dict] = []
    projects_to_import = load_projects()
    for project_index, project in enumerate(projects_to_import, start=1):
        print(
            f"Phase 1: generating project evidence {project_index}/"
            f"{len(projects_to_import)} — {project['id']}",
            flush=True,
        )
        generated = build_project_evidence(
            project["readme_md"], project["repo_full_name"], cv_text[:3000]
        )
        imported = {**project, **generated}
        imported_projects.append(imported)
        cases.append(
            EvaluationCaseInput(
                phase="phase_1_project_evidence",
                case_name=project["id"],
                payload={
                    "readme": project["readme_md"],
                    "repository": project["repo_full_name"],
                    "generated": generated,
                },
                deterministic_checks=_project_checks(generated),
            )
        )
    merge_github_import(user_id, imported_projects, [])
    for project_index, project in enumerate(imported_projects, start=1):
        print(
            f"Phase 1: indexing project {project_index}/"
            f"{len(imported_projects)} — {project['id']}",
            flush=True,
        )
        index_project_evidence(user_id, project)

    projects = [
        {
            **project.model_dump(mode="json", by_alias=False),
            "chars_per_line": None,
        }
        for project in get_stored_projects(user_id)
    ]
    profile = {
        "cv_text": cv_text,
        "skills": skills,
        "target_roles": ["AI Engineer"],
        "projects": projects,
    }
    _save_phase1_checkpoint(user_id, profile, cases)
    print(
        f"Phase 1: checkpoint saved to {_checkpoint_dir()}",
        flush=True,
    )
    return user_id, profile, cases


def run() -> tuple[Path, Path]:
    if not settings.pydantic_evals_enabled:
        raise RuntimeError(
            "PYDANTIC_EVALS_ENABLED must be true to run real-cost evaluations."
        )
    if not settings.dashscope_api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is required for the real evaluation.")
    if settings.logfire_enabled:
        setup_observability(FastAPI())

    with isolated_storage(), span(
        "complete_pipeline_evaluation", evaluation_phase="phase_1_to_3"
    ):
        user_id, profile, cases = _prepare_phase1()
        jobs = load_jobs()
        for job_index, job in enumerate(jobs, start=1):
            print(
                f"Phases 2–3: analyzing job {job_index}/{len(jobs)} — "
                f"{job['case_name']}",
                flush=True,
            )
            result, validation_context, eval_payload = analyze_job(
                user_id, job, profile
            )
            bundle = eval_payload["bundle"]
            cases.append(
                EvaluationCaseInput(
                    phase="phase_2_retrieval",
                    case_name=job["case_name"],
                    payload={
                        "job": job,
                        "portfolio": bundle["layer1_portfolio_overviews"],
                        "evidence_cards": bundle["layer2a_evidence_cards"],
                        "selected_chunks": bundle["layer2b_readme_chunks"],
                        "retrieval_debug": bundle["retrieval_debug"],
                    },
                    deterministic_checks=_retrieval_checks(bundle),
                )
            )
            classified = classify_fit(
                {
                    "enrich_result": result,
                    "validation_context": validation_context,
                }
            )["classified_result"]
            cases.append(
                EvaluationCaseInput(
                    phase="phase_3_application",
                    case_name=job["case_name"],
                    payload={
                        "job": job,
                        "profile": profile,
                        "retrieved_evidence": {
                            "overviews": bundle["layer1_portfolio_overviews"],
                            "evidence_cards": bundle["layer2a_evidence_cards"],
                            "chunks": bundle["layer2b_readme_chunks"],
                        },
                        "model_result": result,
                        "classified_result": classified,
                    },
                    deterministic_checks=_application_checks(
                        classified,
                        len(validation_context["cv_project_slots"]),
                    ),
                )
            )

        print(
            f"Deterministic evaluation: running {len(cases)} cases",
            flush=True,
        )
        deterministic_report = deterministic_dataset(cases).evaluate_sync(
            lambda raw: raw,
            max_concurrency=1,
            progress=True,
        )
        failed_checks = [
            case.name
            for case in deterministic_report.cases
            if any(
                not result.value
                for result in case.assertions.values()
            )
        ]
        if failed_checks:
            raise RuntimeError(
                "Deterministic evaluation failed before semantic judging: "
                + ", ".join(failed_checks)
            )
        print(
            f"Semantic evaluation: judging {len(cases)} cases sequentially",
            flush=True,
        )
        semantic_report = semantic_dataset(cases).evaluate_sync(
            lambda raw: judge_case(
                EvaluationCaseInput.model_validate(raw)
            ).model_dump(mode="json"),
            max_concurrency=settings.eval_max_concurrency,
            progress=True,
        )
        reports = _write_reports(cases, deterministic_report, semantic_report)
        print("Evaluation complete: reports written", flush=True)
        return reports


if __name__ == "__main__":
    json_report, markdown_report = run()
    print(f"Wrote {json_report}")
    print(f"Wrote {markdown_report}")
