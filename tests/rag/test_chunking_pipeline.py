"""Phase 2 chunking pipeline eval — hierarchical semantic chunks for portfolio READMEs.

Corpus: tests/rag/pipeline/{slug}/input-readme.md
Outputs: tests/rag/pipeline/{slug}/chunking-results.md

Run:
    pytest tests/rag/test_chunking_pipeline.py -v
"""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.services.readme_chunker import chunk_readme, count_tokens

PIPELINE_DIR = Path(__file__).resolve().parent / "pipeline"
PROJECT_SLUGS = [
    "jobpilot",
    "agentic-rag-sub-agents",
    "voice-automation",
    "whatsapp-mcp-assistant",
]

JOBPILOT_EXPECTED_HEADINGS = {
    "Engineering highlights",
    "API surface",
    "Agentic architecture",
}


def _format_chunking_report(slug: str, readme: str, result) -> str:
    lines = [
        f"# Chunking results — {slug}",
        "",
        "## Summary",
        f"- Parents: {len(result.parents)}",
        f"- Boundary units: {len(result.units)}",
        f"- Child chunks: {len(result.chunks)}",
        f"- README chars: {len(readme)}",
        "",
        "## Parents",
    ]
    for parent in result.parents:
        lines.append(
            f"- `{parent.heading_path}` — {count_tokens(parent.content)} tokens"
        )
    lines.extend(["", "## Child chunks"])
    for chunk in result.chunks:
        lines.append(
            f"### {chunk.heading_path} (chunk {chunk.chunk_index}, "
            f"{chunk.token_count} tokens, {chunk.chunk_type})"
        )
        preview = chunk.content[:400].replace("\n", " ")
        if len(chunk.content) > 400:
            preview += "..."
        lines.append(preview)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


@pytest.mark.parametrize("slug", PROJECT_SLUGS)
def test_chunking_pipeline_eval(slug: str) -> None:
    """Generate and validate hierarchical semantic chunks for portfolio READMEs."""
    readme_path = PIPELINE_DIR / slug / "input-readme.md"
    assert readme_path.is_file(), f"Missing corpus input: {readme_path}"

    readme = readme_path.read_text(encoding="utf-8")
    project_name = slug.replace("-", " ").title()
    result = chunk_readme(readme, project_name=project_name, embed_fn=None)

    assert result.parents, f"No parent sections parsed for {slug}"
    assert result.chunks, f"No child chunks produced for {slug}"

    for chunk in result.chunks:
        assert chunk.token_count <= 500 or "```" in chunk.content, (
            f"{slug}: chunk exceeds 500 tokens ({chunk.token_count}) "
            f"at {chunk.heading_path}"
        )
        assert chunk.heading_path
        assert chunk.embed_text.startswith(f"Project: {project_name}")

    if slug == "jobpilot":
        paths = {c.heading_path for c in result.chunks}
        parent_paths = {p.heading_path for p in result.parents}
        all_paths = paths | parent_paths
        for expected in JOBPILOT_EXPECTED_HEADINGS:
            assert any(expected in path for path in all_paths), (
                f"Missing expected JobPilot section: {expected}"
            )

    report = _format_chunking_report(slug, readme, result)
    out_path = PIPELINE_DIR / slug / "chunking-results.md"
    out_path.write_text(report, encoding="utf-8")
    assert out_path.is_file()
