"""Unit tests for Phase 2 readme chunker and retrieval."""

from tests.conftest import signup

from backend.app.services.evidence_indexing import index_project_evidence
from backend.app.services.readme_chunker import (
    build_embed_text,
    chunk_readme,
    count_tokens,
    parse_parent_sections,
)
from backend.app.services.retrieve_project_evidence import (
    parse_cv_project_slots,
    retrieve_project_evidence,
)


SAMPLE_README = """# JobPilot

Intro paragraph.

## Engineering highlights

FastAPI backend with LangGraph orchestration and worker task queue.

## API surface

- POST /api/search
- GET /api/runs/{id}

## Agentic architecture

Parent graph with search subgraph and application subgraphs.

```python
def hello():
    return "world"
```
"""


def test_count_tokens_positive():
    assert count_tokens("hello world") >= 2


def test_parse_parent_sections_heading_paths():
    parents = parse_parent_sections(SAMPLE_README)
    paths = {p.heading_path for p in parents}
    assert any("Engineering highlights" in p for p in paths)
    assert any("API surface" in p for p in paths)
    assert any("Agentic architecture" in p for p in paths)


def test_chunk_readme_respects_token_cap():
    result = chunk_readme(SAMPLE_README, project_name="JobPilot", embed_fn=None)
    assert result.chunks
    for chunk in result.chunks:
        assert chunk.token_count <= 500 or "```" in chunk.content


def test_build_embed_text_prefix():
    text = build_embed_text("JobPilot", ["FastAPI"], "API surface", "Routes listed.")
    assert "Project: JobPilot" in text
    assert "Stack: FastAPI" in text
    assert "Section: API surface" in text


def test_parse_cv_project_slots():
    cv = """Experience
Acme Corp — Engineer

Projects
- JobPilot — AI job copilot
- Voice automation assistant

Education
BS CS
"""
    projects = [{"id": "p1", "name": "JobPilot"}]
    slots = parse_cv_project_slots(cv, projects)
    assert len(slots) == 2
    assert slots[0]["matched_portfolio_project_id"] == "p1"


def test_index_and_retrieve_project_evidence(test_db, client):
    user = signup(client, "retrieval@example.com")
    user_id = user["id"]
    project = {
        "id": "proj-test",
        "name": "JobPilot",
        "repo_full_name": "alice/JobPilot",
        "readme_md": SAMPLE_README,
        "portfolio_overview": "Job search copilot.",
        "evidence_card": {
            "tech_stack": ["FastAPI", "LangGraph"],
            "evidence": [
                {
                    "claim": "Uses LangGraph orchestration.",
                    "source_section": "Engineering highlights",
                }
            ],
        },
    }
    meta = index_project_evidence(user_id, project)
    assert meta["chunk_count"] > 0

    bundle = retrieve_project_evidence(
        {
            "title": "Backend Engineer",
            "company": "Acme",
            "url": "https://example.com/job",
            "source_platform": "linkedin",
            "description_text": "FastAPI LangGraph Python backend engineer role.",
        },
        {
            "user_id": user_id,
            "cv_text": "Projects\n- JobPilot\n",
            "skills": ["Python"],
            "target_roles": ["Backend Engineer"],
            "projects": [project],
        },
    )
    assert bundle["layer1_portfolio_overviews"]
    assert bundle["layer2a_evidence_cards"]
    assert bundle["layer2b_readme_chunks"]
    headings = {c["heading_path"] for c in bundle["layer2b_readme_chunks"]}
    assert any("Engineering" in h or "API" in h or "Agentic" in h for h in headings)
