"""Tests for Phase 1 project evidence generation at GitHub import."""

import json
from unittest.mock import patch

import pytest

from backend.app.models.profile import ProfileUpdate, Project
from backend.app.models.project_evidence import ProjectEvidenceCard, ProjectEvidenceResult
from backend.app.services import profile_llm
from backend.app.services.oauth_store import save_token
from backend.app.services.profile_store import get_stored_projects, merge_github_import, update_profile
from tests.conftest import signup

from backend.app.services.profile_llm import EVIDENCE_SYSTEM_PROMPT, ProjectEvidenceError


SAMPLE_README = """# JobPilot

A full-stack job application copilot.

## Stack
- Python, FastAPI, React, TypeScript
- LangGraph for agent orchestration
- SQLite for per-user profile storage

## Architecture
Event-driven API with encrypted CV storage and GitHub README import.
"""


def _long_description() -> str:
    return (
        "Job search automation platform for developers.\n"
        "Built with FastAPI, React, and LangGraph agents.\n"
        "Uses SQLite with per-user row isolation for all profile data.\n"
        "GitHub README import stores full markdown for CV tailoring.\n"
        "Human-in-the-loop approval before any application is sent.\n"
        "Search Helper uses Kimi WebBridge for LinkedIn post extraction.\n"
    )


def _sample_evidence_payload() -> dict:
    return {
        "name": "JobPilot",
        "description": _long_description(),
        "repo_skills": ["Python", "FastAPI", "LangGraph", "React"],
        "portfolio_overview": (
            "JobPilot: FastAPI and LangGraph job-search platform with a desktop "
            "browser worker and human-approved application workflow."
        ),
        "evidence_card": {
            "project_purpose": "AI job application copilot for developers.",
            "tech_stack": ["Python", "FastAPI", "React", "LangGraph", "SQLite"],
            "architecture": [
                "Three-tier deployment with ECS API and desktop Search Helper.",
            ],
            "key_features": [
                "LangGraph orchestration with search and application subgraphs.",
            ],
            "role_relevance": ["Backend engineering", "Agentic systems"],
            "evidence": [
                {
                    "claim": "Uses LangGraph for agent orchestration.",
                    "source_section": "Stack",
                }
            ],
            "supported_metrics": [],
            "limitations_or_unknowns": ["Candidate contribution not stated in README."],
        },
    }


def test_evidence_models_validate_sample_payload():
    result = ProjectEvidenceResult.model_validate(_sample_evidence_payload())
    assert result.name == "JobPilot"
    assert result.evidence_card.tech_stack[0] == "Python"
    assert result.evidence_card.evidence[0].source_section == "Stack"


def test_build_project_evidence_parses_valid_json():
    payload = _sample_evidence_payload()
    with patch.object(profile_llm, "_client") as mock_client_factory:
        mock_client = mock_client_factory.return_value
        mock_client.chat.completions.create.return_value = type(
            "Completion",
            (),
            {"choices": [type("Choice", (), {"message": type("Msg", (), {"content": json.dumps(payload)})()})()]},
        )()

        result = profile_llm.build_project_evidence(SAMPLE_README, "alice/jobpilot", "CV text")

    assert result["portfolio_overview"].startswith("JobPilot:")
    assert result["evidence_card"]["project_purpose"]
    assert "LangGraph" in result["evidence_card"]["tech_stack"]


def test_build_project_evidence_coerces_string_lists():
    payload = _sample_evidence_payload()
    payload["evidence_card"]["architecture"] = "Single architecture paragraph from the model."
    payload["evidence_card"]["role_relevance"] = "Backend and agent engineering relevance."
    with patch.object(profile_llm, "_client") as mock_client_factory:
        mock_client = mock_client_factory.return_value
        mock_client.chat.completions.create.return_value = type(
            "Completion",
            (),
            {"choices": [type("Choice", (), {"message": type("Msg", (), {"content": json.dumps(payload)})()})()]},
        )()

        result = profile_llm.build_project_evidence(SAMPLE_README, "alice/jobpilot", "CV text")

    assert result["evidence_card"]["architecture"] == [
        "Single architecture paragraph from the model."
    ]


def test_build_project_evidence_rejects_invalid_json():
    with patch.object(profile_llm, "_client") as mock_client_factory:
        mock_client = mock_client_factory.return_value
        mock_client.chat.completions.create.return_value = type(
            "Completion",
            (),
            {"choices": [type("Choice", (), {"message": type("Msg", (), {"content": "not json"})()})()]},
        )()

        with pytest.raises(ProjectEvidenceError):
            profile_llm.build_project_evidence(SAMPLE_README, "alice/jobpilot", "CV text")


def test_build_project_evidence_rejects_incomplete_shape():
    bad_payload = {"name": "OnlyName"}
    with patch.object(profile_llm, "_client") as mock_client_factory:
        mock_client = mock_client_factory.return_value
        mock_client.chat.completions.create.return_value = type(
            "Completion",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {"message": type("Msg", (), {"content": json.dumps(bad_payload)})()},
                    )()
                ]
            },
        )()

        with pytest.raises(ProjectEvidenceError):
            profile_llm.build_project_evidence(SAMPLE_README, "alice/jobpilot", "CV text")


@patch("backend.app.routes.github.profile_llm.build_project_evidence")
@patch("backend.app.routes.github.github_service.get_readme")
def test_github_import_stores_evidence_server_side(mock_readme, mock_evidence, client):
    user = signup(client, "evidence@example.com")
    save_token(user["id"], "github", access_token="gh-test-token", email="evidence")

    mock_readme.return_value = SAMPLE_README
    mock_evidence.return_value = _sample_evidence_payload()

    response = client.post("/api/github/import", json={"repos": ["alice/jobpilot"]})
    assert response.status_code == 200, response.text
    body = response.json()
    # Import returns immediately; projects appear after the background job.
    assert body["projectsIndexingStatus"] == "pending"
    assert body["projects"] == []

    mock_evidence.assert_called_once()

    ready = client.get("/api/profile").json()
    assert ready["projectsIndexingStatus"] == "ready"
    assert len(ready["projects"]) == 1
    project = ready["projects"][0]
    assert project["name"] == "JobPilot"
    assert "portfolioOverview" not in project
    assert "evidenceCard" not in project
    assert "readmeMd" not in project

    stored = get_stored_projects(user["id"])[0]
    assert stored.readme_md == SAMPLE_README
    assert stored.portfolio_overview is not None
    assert isinstance(stored.evidence_card, ProjectEvidenceCard)
    assert stored.evidence_card.tech_stack[0] == "Python"


def test_profile_update_preserves_evidence_fields(client):
    user = signup(client, "preserve@example.com")
    payload = _sample_evidence_payload()
    merge_github_import(
        user["id"],
        [
            {
                "id": "proj-evidence",
                "name": payload["name"],
                "description": payload["description"],
                "source": "github",
                "repo_full_name": "alice/jobpilot",
                "readme_md": SAMPLE_README,
                "portfolio_overview": payload["portfolio_overview"],
                "evidence_card": payload["evidence_card"],
            }
        ],
        payload["repo_skills"],
    )

    stored_before = get_stored_projects(user["id"])[0]
    update_profile(
        user["id"],
        ProfileUpdate(
            projects=[
                Project(
                    id=stored_before.id,
                    name="JobPilot Renamed",
                    description="Updated description line.",
                    source="github",
                    repo_full_name="alice/jobpilot",
                )
            ]
        ),
    )

    stored_after = get_stored_projects(user["id"])[0]
    assert stored_after.name == "JobPilot Renamed"
    assert stored_after.portfolio_overview == payload["portfolio_overview"]
    assert stored_after.evidence_card is not None
    assert stored_after.evidence_card.project_purpose == payload["evidence_card"]["project_purpose"]
    assert stored_after.readme_md == SAMPLE_README


def test_evidence_system_prompt_is_documented_constant():
    assert "source-grounded project evidence" in EVIDENCE_SYSTEM_PROMPT
    assert "portfolio_overview" in EVIDENCE_SYSTEM_PROMPT
    assert "limitations_or_unknowns" in EVIDENCE_SYSTEM_PROMPT
