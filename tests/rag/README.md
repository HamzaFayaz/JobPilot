# RAG pipeline tests (Phase 2)

Chunking and retrieval eval lives here — not under `docs/fixtures/`.

| Path | Purpose |
| --- | --- |
| [`pipeline/`](pipeline/) | Frozen README inputs + generated chunking eval outputs (per project) |
| [`test_chunking_pipeline.py`](test_chunking_pipeline.py) | Pytest entry — runs chunking eval when chunker is implemented |

**Plan:** [`.agent/plans/jobpilot_project_evidence_phase2_plan.md`](../../.agent/plans/jobpilot_project_evidence_phase2_plan.md)
