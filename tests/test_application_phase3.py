"""Deterministic Phase 3 application-subgraph contract tests."""

import json
import importlib
from datetime import date
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from backend.app.db import get_connection
from backend.app.graph.subgraphs.application.nodes.classify_fit import classify_fit
from backend.app.graph.subgraphs.application.nodes.package_out import package_out
from backend.app.models.application import EnrichJobResult
from backend.app.services.application_llm import (
    ApplicationAnalysisError,
    _parse_result,
    analyze_job,
    build_messages,
)
from backend.app.services.application_validation import validate_application_contract
from backend.app.services.cv_evidence_spans import build_cv_evidence_spans
from backend.app.services.date_tenure import build_date_facts, completed_months


def _cv_ref() -> dict:
    return {
        "source_type": "cv",
        "quote": "Built LangGraph workflows",
        "cv_section": "Projects",
        "project_id": None,
        "project_name": None,
        "heading_path": None,
        "source_id": None,
        "cv_span_id": "cv:test",
    }


def _keep(slot_index: int = 0) -> dict:
    return {
        "slot_index": slot_index,
        "action": "keep",
        "current_project_name": f"Current {slot_index}",
        "swap_in_project_id": None,
        "swap_in_project_name": None,
        "target_requirement_ids": [],
        "evidence_refs": [],
        "swap_coverage": [],
        "rationale": "The current project remains relevant.",
        "impact": None,
    }


def _portfolio_ref() -> dict:
    return {
        "source_type": "readme_chunk",
        "quote": "Direct packed project evidence",
        "cv_section": None,
        "project_id": "other",
        "project_name": "Other",
        "heading_path": "Evidence",
        "source_id": "chunk:other",
        "cv_span_id": None,
    }


def _valid_result(*, slots: int = 1) -> dict:
    return {
        "analysis_status": "completed",
        "explicit_requirements": [
            {
                "requirement_id": "req_1",
                "retrieval_requirement_id": None,
                "job_quote": "experience with LangGraph",
                "job_source_start": 10,
                "job_source_end": 35,
                "text": "Experience with LangGraph",
                "importance": "required",
                "category": "skill",
                "status": "matched",
                "evidence_refs": [_cv_ref()],
                "date_fact_ids": [],
                "rationale": "The current CV explicitly names LangGraph.",
            }
        ],
        "inferred_requirements": [],
        "confidence": "medium",
        "current_cv_score": 70,
        "suggested_cv_score": 70,
        "current_score_rationale": "The required skill is visible.",
        "suggested_score_rationale": "No replacement improves the evidence.",
        "project_decisions": [_keep(index) for index in range(slots)],
        "limitations": [],
        "summary": "Moderate visible fit with grounded LangGraph evidence.",
    }


def _profile() -> dict:
    return {
        "cv_text": "Projects\n- Current 0 — Built LangGraph workflows\n",
        "skills": ["Python", "LangGraph", "FastAPI"],
        "target_roles": ["AI Engineer"],
        "projects": [
            {
                "id": "current",
                "name": "Current 0",
                "description": "Current project",
                "source": "github",
                "repo_full_name": "owner/current",
                "readme_md": "LangGraph",
                "portfolio_overview": "A workflow project.",
                "evidence_card": {},
                "chars_per_line": None,
            }
        ],
    }


def _job(index: int = 1) -> dict:
    return {
        "title": "AI Engineer",
        "company": "Acme",
        "url": f"https://example.com/jobs/{index}",
        "platform": "linkedin",
        "description_text": "Required: experience with LangGraph.",
    }


def _analysis_bundle() -> dict:
    return {
        "job": _job(),
        "profile": {
            "cv_text": _profile()["cv_text"],
            "skills": _profile()["skills"],
            "target_roles": _profile()["target_roles"],
            "cv_project_slots": [
                {
                    "slot_index": 0,
                    "cv_project_name": "Current 0",
                    "source_start": 9,
                    "source_end": len(_profile()["cv_text"]),
                    "chars_budget": 100,
                    "matched_portfolio_project_id": "current",
                }
            ],
            "cv_evidence_spans": [
                {
                    "source_id": "cv:test",
                    "content": "Built LangGraph workflows",
                    "source_start": 23,
                    "source_end": 48,
                    "section": "Projects",
                    "project_slot_id": "cv_slot_0",
                    "content_hash": "test",
                }
            ],
            "date_facts": [],
            "date_facts_as_of": "2026-07-17",
        },
        "layer1_portfolio_overviews": [
            {
                "source_id": "project:current:overview",
                "project_id": "current",
                "name": "Current 0",
            }
        ],
        "layer2a_evidence_cards": [],
        "layer2b_readme_chunks": [],
        "extracted_job_requirements": [],
        "requirement_extraction": {},
        "retrieval_debug": {},
    }


def test_schema_accepts_completed_and_insufficient_results():
    assert EnrichJobResult.model_validate(_valid_result()).current_cv_score == 70
    insufficient = _valid_result()
    insufficient.update(
        {
            "analysis_status": "insufficient_job_detail",
            "explicit_requirements": [],
            "confidence": "low",
            "current_cv_score": None,
            "suggested_cv_score": None,
        }
    )
    assert EnrichJobResult.model_validate(insufficient).current_cv_score is None


def test_schema_rejects_extras_and_invalid_keep_shape():
    payload = _valid_result()
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        EnrichJobResult.model_validate(payload)


def test_schema_allows_current_cv_evidence_on_keep_decision():
    payload = _valid_result()
    payload["project_decisions"][0]["evidence_refs"] = [_cv_ref()]
    assert EnrichJobResult.model_validate(payload).project_decisions[0].action == "keep"

    payload = _valid_result()
    payload["project_decisions"][0]["swap_in_project_id"] = "other"
    with pytest.raises(ValidationError):
        EnrichJobResult.model_validate(payload)


def test_parse_normalizes_keep_replacement_field_pollution():
    from backend.app.services.application_llm import _parse_result

    payload = _valid_result()
    payload["project_decisions"][0].update(
        {
            "target_requirement_ids": ["req_1"],
            "impact": "high",
            "swap_coverage": [],
            "evidence_refs": [_cv_ref()],
        }
    )
    parsed = _parse_result(json.dumps(payload))
    decision = parsed.project_decisions[0]
    assert decision.action == "keep"
    assert decision.target_requirement_ids == []
    assert decision.impact is None
    assert decision.swap_coverage == []


def test_model_bundle_strips_cv_content_hash():
    messages, _ = build_messages(_analysis_bundle())
    user_payload = json.loads(messages[1]["content"])
    span = user_payload["profile"]["cv_evidence_spans"][0]
    assert span["source_id"] == "cv:test"
    assert "content_hash" not in span
    assert "ILLUSTRATIVE SHAPE ONLY" in messages[0]["content"]
    assert '"action": "keep"' in messages[0]["content"]
    assert '"date_fact_ids": ["cv_date_01"]' in messages[0]["content"]


def test_validator_rejects_invalid_ids_and_accepts_valid_date_cv_portfolio_ids():
    context = {
        "job_description": "Required: 1+ year of experience in web development.",
        "cv_text": "Apr  2025 to Present Remote",
        "cv_evidence_sources": {
            "cv:730:750:fb5a4b1885dc": {
                "source_id": "cv:730:750:fb5a4b1885dc",
                "content": "Apr  2025 to Present",
            },
            "cv:751:791:83f51d87259a": {
                "source_id": "cv:751:791:83f51d87259a",
                "content": "Remote",
            },
        },
        "date_facts": [
            {
                "date_fact_id": "cv_date_01",
                "cv_span_id": "cv:730:750:fb5a4b1885dc",
                "quote": "Apr  2025 to Present",
            }
        ],
        "cv_project_slots": [
            {
                "slot_index": 0,
                "cv_project_name": "Current 0",
                "matched_portfolio_project_id": "current",
            }
        ],
        "cv_project_ids": ["current"],
        "portfolio_project_ids": ["jobpilot", "current"],
        "evidence_sources": {
            "ec498967-883e-4818-8d57-f2323d16f289": {
                "source_type": "readme_chunk",
                "project_id": "jobpilot",
                "content": "React FastAPI LangGraph",
            }
        },
    }
    invalid = _valid_result()
    invalid["explicit_requirements"][0]["job_quote"] = (
        "1+ year of experience in web development"
    )
    invalid["explicit_requirements"][0]["job_source_start"] = 10
    invalid["explicit_requirements"][0]["job_source_end"] = 50
    invalid["explicit_requirements"][0]["evidence_refs"] = [
        {
            **_cv_ref(),
            "cv_span_id": "cv_date_01",
            "quote": "Apr  2025 to Present",
        }
    ]
    invalid["explicit_requirements"][0]["date_fact_ids"] = ["cv_date_01"]
    invalid["suggested_cv_score"] = 80
    invalid["project_decisions"][0] = {
        "slot_index": 0,
        "action": "swap",
        "current_project_name": "Current 0",
        "swap_in_project_id": "jobpilot",
        "swap_in_project_name": "JobPilot",
        "target_requirement_ids": ["req_1"],
        "evidence_refs": [_cv_ref()],
        "swap_coverage": [
            {
                "requirement_id": "req_1",
                "proposed_status": "matched",
                "evidence_refs": [
                    {
                        **_portfolio_ref(),
                        "source_id": "b908b39b144d7db7c81e8ea67c0a354c9cd607cfa7a9a5847e48a67f353c2e4f",
                        "quote": "React FastAPI LangGraph",
                        "project_id": "jobpilot",
                    }
                ],
            }
        ],
        "rationale": "Swap for stronger web evidence.",
        "impact": "high",
    }
    errors = validate_application_contract(invalid, context)
    codes = {error["code"] for error in errors}
    assert "invalid_current_cv_source" in codes
    assert "swap_evidence_not_owned_by_replacement" in codes

    valid = _valid_result()
    valid["explicit_requirements"][0]["job_quote"] = (
        "1+ year of experience in web development"
    )
    valid["explicit_requirements"][0]["job_source_start"] = 10
    valid["explicit_requirements"][0]["job_source_end"] = 50
    valid["explicit_requirements"][0]["evidence_refs"] = [
        {
            **_cv_ref(),
            "cv_span_id": "cv:730:750:fb5a4b1885dc",
            "quote": "Apr  2025 to Present",
        }
    ]
    valid["explicit_requirements"][0]["date_fact_ids"] = ["cv_date_01"]
    valid["suggested_cv_score"] = 80
    valid["project_decisions"][0] = {
        "slot_index": 0,
        "action": "swap",
        "current_project_name": "Current 0",
        "swap_in_project_id": "jobpilot",
        "swap_in_project_name": "JobPilot",
        "target_requirement_ids": ["req_1"],
        "evidence_refs": [
            {
                **_cv_ref(),
                "cv_span_id": "cv:730:750:fb5a4b1885dc",
                "quote": "Apr  2025 to Present",
            }
        ],
        "swap_coverage": [
            {
                "requirement_id": "req_1",
                "proposed_status": "matched",
                "evidence_refs": [
                    {
                        **_portfolio_ref(),
                        "source_id": "ec498967-883e-4818-8d57-f2323d16f289",
                        "quote": "React FastAPI LangGraph",
                        "project_id": "jobpilot",
                    }
                ],
            }
        ],
        "rationale": "Swap for stronger web evidence.",
        "impact": "high",
    }
    assert validate_application_contract(valid, context) == []


def test_swap_coverage_is_portfolio_authority_not_decision_evidence():
    payload = _valid_result()
    payload["suggested_cv_score"] = 75
    payload["project_decisions"][0] = {
        "slot_index": 0,
        "action": "swap",
        "current_project_name": "Current 0",
        "swap_in_project_id": "other",
        "swap_in_project_name": "Other",
        "target_requirement_ids": ["req_1"],
        "evidence_refs": [_cv_ref()],
        "swap_coverage": [
            {
                "requirement_id": "req_1",
                "proposed_status": "matched",
                "evidence_refs": [_portfolio_ref()],
            }
        ],
        "rationale": "The packed replacement evidence supports the target.",
        "impact": "low",
    }
    assert EnrichJobResult.model_validate(payload).project_decisions[0].action == "swap"
    payload["project_decisions"][0]["swap_coverage"][0]["evidence_refs"] = [_cv_ref()]
    with pytest.raises(ValidationError):
        EnrichJobResult.model_validate(payload)


def test_model_bundle_exposes_only_packed_portfolio_source_ids():
    bundle = _analysis_bundle()
    bundle["layer1_portfolio_overviews"][0]["portfolio_overview"] = "Overview text"
    bundle["layer2a_evidence_cards"] = [
        {
            "source_id": "project:current:evidence_card",
            "project_id": "current",
            "evidence_card": {"claim": "Generated claim"},
        }
    ]
    bundle["layer2b_readme_chunks"] = [
        {
            "source_id": "chunk:other",
            "project_id": "other",
            "project_name": "Other",
            "heading_path": "Evidence",
            "content": "Direct packed project evidence",
            "source": "readme_chunk",
            "source_start": 0,
            "source_end": 30,
            "content_hash": "not-a-citable-id",
            "retrieval_provenance": {"req": {"rerank_score": 1.0}},
            "retrieved_requirement_ids": ["req_1"],
        }
    ]
    messages, _ = build_messages(bundle)
    user_payload = json.loads(messages[1]["content"])
    assert "layer2a_evidence_cards" not in user_payload
    assert "source_id" not in user_payload["layer1_portfolio_overviews"][0]
    assert "portfolio_overview" not in user_payload["layer1_portfolio_overviews"][0]
    packed = user_payload["layer2b_readme_chunks"][0]
    assert packed["source_id"] == "chunk:other"
    assert "content_hash" not in packed
    assert "retrieval_provenance" not in packed


@pytest.mark.parametrize("raw", ["", "```json\n{}\n```", "prefix {}"])
def test_strict_json_handling_rejects_empty_fenced_and_wrapped(raw):
    with pytest.raises(ApplicationAnalysisError):
        _parse_result(raw)


def test_application_call_uses_one_repair_retry(monkeypatch):
    bundle = {
        "job": _job(),
        "profile": {
            "cv_text": _profile()["cv_text"],
            "skills": _profile()["skills"],
            "target_roles": _profile()["target_roles"],
            "cv_project_slots": [
                {
                    "slot_index": 0,
                    "cv_project_name": "Current 0",
                    "chars_budget": 100,
                    "matched_portfolio_project_id": "current",
                }
            ],
            "cv_evidence_spans": [
                {
                    "source_id": "cv:test",
                    "content": "Built LangGraph workflows",
                    "source_start": 23,
                    "source_end": 48,
                    "section": "Projects",
                    "project_slot_id": "cv_slot_0",
                    "content_hash": "test",
                }
            ],
            "date_facts": [],
            "date_facts_as_of": "2026-07-17",
        },
        "layer1_portfolio_overviews": [
            {
                "source_id": "project:current:overview",
                "project_id": "current",
                "name": "Current 0",
            }
        ],
        "layer2a_evidence_cards": [],
        "layer2b_readme_chunks": [],
        "retrieval_debug": {},
    }
    monkeypatch.setattr(
        "backend.app.services.application_llm.retrieve_project_evidence",
        lambda user_id, job, profile: bundle,
    )
    monkeypatch.setattr(
        "backend.app.services.application_llm.settings.application_repair_retries_override",
        1,
    )
    responses = iter(["not json", json.dumps(_valid_result())])

    class Completions:
        def create(self, **kwargs):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content=next(responses))
                    )
                ]
            )

    client = SimpleNamespace(chat=SimpleNamespace(completions=Completions()))
    result, context, payload = analyze_job(1, _job(), _profile(), client=client)
    assert result["current_cv_score"] == 70
    assert context["portfolio_project_ids"] == ["current"]
    assert payload["validated_response"] == result


def test_application_call_repairs_contract_failure_once(monkeypatch):
    monkeypatch.setattr(
        "backend.app.services.application_llm.retrieve_project_evidence",
        lambda user_id, job, profile: _analysis_bundle(),
    )
    monkeypatch.setattr(
        "backend.app.services.application_llm.settings.application_repair_retries_override",
        1,
    )
    invalid = _valid_result()
    invalid["explicit_requirements"][0]["evidence_refs"][0]["cv_span_id"] = "cv:unknown"
    responses = iter([json.dumps(invalid), json.dumps(_valid_result())])

    class Completions:
        def create(self, **kwargs):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content=next(responses))
                    )
                ]
            )

    client = SimpleNamespace(chat=SimpleNamespace(completions=Completions()))
    result, _, payload = analyze_job(1, _job(), _profile(), client=client)
    assert result == _valid_result()
    assert payload["contract_validation"]["repair_count"] == 1
    assert len(payload["raw_attempts"]) == 2


def test_classify_fit_preserves_model_scores_and_narrative():
    original = _valid_result(slots=1)
    result = classify_fit(
        {
            "enrich_result": original,
            "job": _job(),
            "profile": _profile(),
            "validation_context": {
                "job_description": _job()["description_text"],
                "cv_text": _profile()["cv_text"] + "Built LangGraph workflows",
                "cv_project_slots": [
                    {
                        "slot_index": 0,
                        "cv_project_name": "Current 0",
                        "matched_portfolio_project_id": "current",
                    }
                ],
                "portfolio_project_ids": ["current", "other"],
                "evidence_sources": {},
            },
        }
    )
    classified = result["classified_result"]
    assert classified["current_cv_score"] == 70
    assert classified["suggested_cv_score"] == 70
    assert classified["summary"] == original["summary"]
    assert classified["current_score_rationale"] == original["current_score_rationale"]
    assert classified["project_decisions"][0]["action"] == "keep"
    assert classified["fit_tier"] == "moderate"
    assert classified["corrections"] == []


def test_contract_rejects_unknown_cv_span_without_mutating_model_result():
    payload = _valid_result()
    original = json.loads(json.dumps(payload))
    errors = validate_application_contract(
        payload,
        {
            "job_description": _job()["description_text"],
            "cv_evidence_sources": {},
            "cv_project_slots": [{"slot_index": 0}],
            "cv_project_ids": [],
            "portfolio_project_ids": ["current"],
            "evidence_sources": {},
            "date_facts": [],
        },
    )
    invalid_source = next(
        item for item in errors if item["code"] == "invalid_current_cv_source"
    )
    assert invalid_source["cv_span_id"] == "cv:test"
    assert "Date fact IDs" in invalid_source["instruction"]
    assert payload == original


def test_overlapping_date_ranges_are_not_double_counted():
    cv = "Jan 2024 to Dec 2024\nJun 2024 to Jun 2025"
    assert completed_months(cv, date(2025, 6, 30)) == 18
    facts = build_date_facts(cv, date(2025, 6, 30))
    assert all(
        cv[item["source_start"] : item["source_end"]] == item["quote"]
        for item in facts
    )
    assert all(item["cv_span_id"].startswith("cv:") for item in facts)


def test_cv_evidence_spans_preserve_crlf_nbsp_and_unicode_bullets():
    cv = "PROJECTS\r\n• JobPilot\u00a0— Built LangGraph workflows\r\nSKILLS\r\nPython"
    spans = build_cv_evidence_spans(cv)
    assert spans
    assert all(cv[item["source_start"] : item["source_end"]] == item["content"] for item in spans)
    assert len({item["source_id"] for item in spans}) == len(spans)
    assert any("JobPilot\u00a0—" in item["content"] for item in spans)


def test_package_out_upserts_structured_analysis(test_db):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            ("phase3@example.com", "hash"),
        )
        user_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
        conn.execute(
            "INSERT INTO search_runs (user_id, status) VALUES (?, 'running')",
            (user_id,),
        )
        run_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
        conn.commit()

    classified = {
        **_valid_result(),
        "passes_threshold": True,
        "fit_tier": "moderate",
        "fit_message": "Moderate fit.",
        "corrections": [],
    }
    state = {
        "run_id": run_id,
        "user_id": user_id,
        "job": _job(),
        "profile": _profile(),
        "enrich_result": _valid_result(),
        "classified_result": classified,
    }
    first = package_out(state)
    second = package_out(state)
    assert first["package_id"] == second["package_id"]
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT analysis_json, status FROM job_packages WHERE run_id = ?",
            (run_id,),
        ).fetchall()
    assert len(rows) == 1
    assert rows[0]["status"] == "ready"
    assert json.loads(rows[0]["analysis_json"])["classified_result"]["fit_tier"] == "moderate"


def test_parent_fan_out_persists_each_job_and_finalizes_once(test_db, monkeypatch):
    from backend.app.graph import orchestrator
    from backend.app.graph.nodes.persist import persist as real_persist

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            ("fanout@example.com", "hash"),
        )
        user_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
        conn.execute(
            "INSERT INTO search_runs (user_id, status) VALUES (?, 'running')",
            (user_id,),
        )
        run_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
        conn.commit()

    profile = _profile()
    jobs = [_job(1), _job(2), _job(3)]
    monkeypatch.setattr(
        orchestrator,
        "init_run",
        lambda state: {
            "role": "AI Engineer",
            "platform": "linkedin",
            "country": "Pakistan",
            "work_mode": "both",
            "max_listings": 3,
            "job_age": "week",
            "profile": profile,
            "status": "running",
            "errors": [],
        },
    )
    monkeypatch.setattr(
        orchestrator,
        "search_subgraph",
        lambda state: {"raw_listings": [], "errors": []},
    )
    monkeypatch.setattr(
        orchestrator,
        "prefilter",
        lambda state: {"listings": jobs, "matched_jobs": jobs},
    )
    enrich_node_module = importlib.import_module(
        "backend.app.graph.subgraphs.application.nodes.enrich_job"
    )
    monkeypatch.setattr(
        enrich_node_module,
        "analyze_job",
        lambda user_id, job, profile: (
            _valid_result(),
            {
                "cv_project_slots": [
                    {
                        "slot_index": 0,
                        "cv_project_name": "Current 0",
                        "matched_portfolio_project_id": "current",
                    }
                ],
                "portfolio_project_ids": ["current"],
                "evidence_sources": {},
            },
            {},
        ),
    )
    finalized = 0

    def counted_persist(state):
        nonlocal finalized
        finalized += 1
        return real_persist(state)

    monkeypatch.setattr(orchestrator, "persist", counted_persist)
    graph = orchestrator.build_parent_graph()
    graph.invoke(
        {
            "run_id": run_id,
            "user_id": user_id,
            "role": "",
            "platform": "linkedin",
            "country": "",
            "work_mode": "both",
            "max_listings": 3,
            "job_age": "week",
            "profile": profile,
            "listings": [],
            "raw_listings": [],
            "warnings": [],
            "matched_jobs": [],
            "packages": [],
            "errors": [],
            "status": "pending",
        }
    )
    with get_connection() as conn:
        package_count = conn.execute(
            "SELECT COUNT(*) FROM job_packages WHERE run_id = ?", (run_id,)
        ).fetchone()[0]
        run = conn.execute(
            "SELECT status, jobs_ready_count FROM search_runs WHERE id = ?", (run_id,)
        ).fetchone()
    assert package_count == 3
    assert finalized == 1
    assert run["status"] == "completed"
    assert run["jobs_ready_count"] == 3
