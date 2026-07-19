"""Tests for GitHub import README storage and per-user data isolation."""

from unittest.mock import patch

from tests.conftest import login, signup

from backend.app.services.oauth_store import save_token
from backend.app.services.profile_store import (
    get_profile,
    get_project_readme,
    get_stored_projects,
    merge_github_import,
    update_profile,
)
from backend.app.models.profile import ProfileUpdate, Project


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
    )


def _seed_github_project(user_id: int, project_id: str = "proj-1") -> None:
    merge_github_import(
        user_id,
        [
            {
                "id": project_id,
                "name": "JobPilot",
                "description": _long_description(),
                "source": "github",
                "repo_full_name": "alice/jobpilot",
                "readme_md": SAMPLE_README,
            }
        ],
        ["Python", "React"],
    )


@patch("backend.app.routes.github.profile_llm.build_project_evidence")
@patch("backend.app.routes.github.github_service.get_readme")
def test_github_import_stores_readme_server_side(mock_readme, mock_evidence, client):
    user = signup(client, "alice@example.com")
    save_token(user["id"], "github", access_token="gh-test-token", email="alice")

    mock_readme.return_value = SAMPLE_README
    mock_evidence.return_value = {
        "name": "JobPilot",
        "description": _long_description(),
        "repo_skills": ["Python", "FastAPI"],
        "portfolio_overview": "JobPilot: FastAPI and LangGraph job-search platform.",
        "evidence_card": {
            "project_purpose": "AI job application copilot.",
            "tech_stack": ["Python", "FastAPI"],
            "architecture": ["ECS API with desktop Search Helper."],
            "key_features": ["LangGraph orchestration."],
            "role_relevance": ["Backend engineering"],
            "evidence": [{"claim": "Uses LangGraph.", "source_section": "Stack"}],
            "supported_metrics": [],
            "limitations_or_unknowns": [],
        },
    }

    response = client.post(
        "/api/github/import",
        json={"repos": ["alice/jobpilot"]},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["projectsIndexingStatus"] == "pending"
    assert body["projects"] == []

    ready = client.get("/api/profile").json()
    assert ready["projectsIndexingStatus"] == "ready"
    assert len(ready["projects"]) == 1
    project = ready["projects"][0]
    assert project["name"] == "JobPilot"
    assert project["repoFullName"] == "alice/jobpilot"
    assert "readmeMd" not in project
    assert "readme_md" not in project
    assert len(project["description"].splitlines()) >= 5

    stored = get_stored_projects(user["id"])
    assert len(stored) == 1
    assert stored[0].readme_md == SAMPLE_README
    assert stored[0].repo_full_name == "alice/jobpilot"


def test_profile_update_preserves_readme(client):
    user = signup(client, "bob@example.com")
    _seed_github_project(user["id"], "proj-bob")

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
                    repo_full_name="bob/jobpilot",
                )
            ]
        ),
    )

    stored_after = get_stored_projects(user["id"])[0]
    assert stored_after.name == "JobPilot Renamed"
    assert stored_after.description == "Updated description line."
    assert stored_after.readme_md == SAMPLE_README
    assert stored_after.repo_full_name == "bob/jobpilot"


def test_users_cannot_access_each_others_profile_data(client):
    user_a = signup(client, "usera@example.com")
    _seed_github_project(user_a["id"], "proj-a")

    client.post("/api/auth/logout")
    user_b = signup(client, "userb@example.com")

    profile_b = client.get("/api/profile").json()
    assert profile_b["projects"] == []
    assert profile_b["skills"] == []

    profile_a = get_profile(user_a["id"])
    assert len(profile_a.projects) == 1
    assert profile_a.projects[0].name == "JobPilot"

    assert get_stored_projects(user_b["id"]) == []
    assert get_project_readme(user_b["id"], "proj-a") is None

    stored_a = get_stored_projects(user_a["id"])
    assert stored_a[0].readme_md == SAMPLE_README


def test_users_cannot_read_another_users_readme_by_project_id(client):
    user_a = signup(client, "carol@example.com")
    _seed_github_project(user_a["id"], "proj-carol")

    user_b = signup(client, "dave@example.com")

    assert get_project_readme(user_a["id"], "proj-carol") == SAMPLE_README
    assert get_project_readme(user_b["id"], "proj-carol") is None


def test_login_session_only_sees_own_profile(client):
    user_a = signup(client, "eve@example.com")
    _seed_github_project(user_a["id"], "proj-eve")

    client.post("/api/auth/logout")
    signup(client, "frank@example.com")

    response = client.get("/api/profile")
    assert response.status_code == 200
    assert response.json()["projects"] == []

    client.post("/api/auth/logout")
    login(client, "eve@example.com")

    response = client.get("/api/profile")
    assert response.status_code == 200
    assert len(response.json()["projects"]) == 1
    assert "readmeMd" not in response.text
