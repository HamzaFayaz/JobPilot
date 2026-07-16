# Phase 2 — RAG chunking pipeline eval corpus

Frozen README inputs and **per-project** chunking results for hierarchical
semantic chunking evaluation (before full retrieval / application subagent).

**Plan:** [`.agent/plans/jobpilot_project_evidence_phase2_plan.md`](../../../.agent/plans/jobpilot_project_evidence_phase2_plan.md)

**Tests:** [`tests/rag/test_chunking_pipeline.py`](../test_chunking_pipeline.py)

## Projects (one folder per repo)

| Slug | Source |
| --- | --- |
| `jobpilot` | This repo root `README.md` |
| `agentic-rag-sub-agents` | [HamzaFayaz/agentic-rag-sub-agents](https://github.com/HamzaFayaz/agentic-rag-sub-agents) |
| `voice-automation` | [HamzaFayaz/voice-automation](https://github.com/HamzaFayaz/voice-automation) |
| `whatsapp-mcp-assistant` | [HamzaFayaz/whatsapp-mcp-assistant](https://github.com/HamzaFayaz/whatsapp-mcp-assistant) |

Each project folder is **self-contained** — inputs and outputs stay together.

## Per-project layout

```text
{slug}/
  input-readme.md           # frozen input (committed)
  chunking-results.md       # primary human-readable eval report (generated)
  output-parents.json       # optional machine-readable parents
  output-units.json         # optional boundary units + vectors (eval only)
  output-chunks.json        # optional final chunks + storage vectors
  manifest.json             # counts, token stats, model config
```

### `chunking-results.md` (preferred output)

Markdown report for manual review. Sections:

1. **Summary** — parent count, unit count, chunk count, max tokens, model/dims
2. **Parents** — `heading_path`, token count, child count
3. **Units** — sentence/paragraph text, similarity to previous (no full vectors in md)
4. **Child chunks** — `heading_path`, token count, content preview, embed prefix

Full vectors stay in `output-units.json` / `output-chunks.json` when present.

## How to generate (after chunker ships)

```bash
pytest tests/rag/test_chunking_pipeline.py -v
```

The test writes/updates files under each `{slug}/` folder and fails on token cap
or heading-boundary violations.

## Manual review checklist

- [ ] Parents respect heading boundaries (no cross-heading merges)
- [ ] Child chunks ≤ 500 tokens (except atomic code/table blocks)
- [ ] `heading_path` correct for `###` subsections
- [ ] JobPilot: `Engineering highlights`, `API surface`, `Agentic architecture` present
- [ ] Re-run after chunking config changes; review `chunking-results.md` diffs
