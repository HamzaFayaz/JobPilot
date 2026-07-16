"""Phase 2 chunking pipeline eval — placeholder until readme_chunker ships.

Corpus: tests/rag/pipeline/{slug}/input-readme.md
Outputs: tests/rag/pipeline/{slug}/chunking-results.md (primary; JSON only if needed)

Run (after implementation):
    pytest tests/rag/test_chunking_pipeline.py -v
"""

from pathlib import Path

import pytest

PIPELINE_DIR = Path(__file__).resolve().parent / "pipeline"
PROJECT_SLUGS = [
    "jobpilot",
    "agentic-rag-sub-agents",
    "voice-automation",
    "whatsapp-mcp-assistant",
]


@pytest.mark.parametrize("slug", PROJECT_SLUGS)
def test_chunking_pipeline_eval(slug: str) -> None:
    """Generate and validate hierarchical semantic chunks for portfolio READMEs."""
    readme = PIPELINE_DIR / slug / "input-readme.md"
    assert readme.is_file(), f"Missing corpus input: {readme}"
    pytest.skip("readme_chunker not implemented — run eval after Phase 2 step B")
