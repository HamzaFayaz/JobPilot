"""Unit tests for Phase 2 readme chunker and retrieval."""

from tests.conftest import signup

from backend.app.services.cv_parser import extract_text_from_docx
from backend.app.services.evidence_indexing import index_project_evidence
from backend.app.services.job_requirement_queries import extract_requirement_queries
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
from tests.evals.dataset import load_cv_path, load_projects


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
        assert SAMPLE_README[chunk.source_start : chunk.source_end] == chunk.content


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
    assert cv[slots[0]["source_start"] : slots[0]["source_end"]] == slots[0]["cv_excerpt"]


def test_cv_slots_handle_unicode_bullets_unknowns_and_section_boundary():
    cv = (
        "SELECTED PROJECTS\r\n"
        "• JobPilot — agent workflow\r\n"
        "• Unknown Tool — independent project\r\n"
        "SKILLS\r\nJobPilot mentioned outside projects"
    )
    slots = parse_cv_project_slots(cv, [{"id": "p1", "name": "JobPilot"}])
    assert [slot["matched_portfolio_project_id"] for slot in slots] == ["p1", None]
    assert all("SKILLS" not in slot["cv_excerpt"] for slot in slots)


def test_fenced_heading_offsets_and_short_reason_are_exact():
    readme = "# Root\r\n\r\n```md\r\n# not a heading\r\n```\r\n\r\nSmall prose."
    result = chunk_readme(readme, project_name="Offsets", embed_fn=None)
    assert len(result.parents) == 1
    assert "# not a heading" in result.parents[0].content
    assert all(
        readme[chunk.source_start : chunk.source_end] == chunk.content
        for chunk in result.chunks
    )
    assert all(
        chunk.token_count >= 120 or chunk.short_chunk_reason
        for chunk in result.chunks
    )


def test_requirement_queries_preserve_products_and_filter_application_text():
    description = """
Requirements
- Must have Azure AI Foundry and Azure OpenAI experience.
- Preferred experience with AWS Step Functions.
- Apply by emailing jobs@example.com.
"""
    queries = extract_requirement_queries("AI Engineer", description)
    texts = [item["query"] for item in queries if not item["is_fallback"]]
    assert any("Azure AI Foundry" in text and "Azure OpenAI" in text for text in texts)
    assert any("AWS Step Functions" in text for text in texts)
    assert all("jobs@example.com" not in text for text in texts)
    assert queries[-1]["is_fallback"]


def test_real_cv_yields_four_ordered_project_slots():
    cv_path = load_cv_path()
    cv_text = (
        extract_text_from_docx(cv_path)
        if cv_path.suffix.lower() == ".docx"
        else cv_path.read_text(encoding="utf-8")
    )
    slots = parse_cv_project_slots(cv_text, load_projects())
    lines = cv_text.splitlines()
    project_line = next(
        (index for index, line in enumerate(lines) if line.strip() == "PROJECTS"),
        0,
    )
    assert len(slots) == 4, lines[project_line : project_line + 20]
    assert [slot["slot_index"] for slot in slots] == [0, 1, 2, 3]
    assert all(
        cv_text[slot["source_start"] : slot["source_end"]] == slot["cv_excerpt"]
        for slot in slots
    )


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
        user_id,
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
