# Phase 2 Build Results — Project Evidence Retrieval

**Date:** 2026-07-17  
**Plan:** `.agent/plans/jobpilot_project_evidence_phase2_plan.md`  
**Status:** Complete (Phase 2 scope; Phase 3 `enrich_job` deferred per plan)

---

## Summary

Phase 2 delivers README chunking, SQLite + FTS5 + FAISS indexing at GitHub import, and hybrid `retrieve_project_evidence()` with no LLM. All planned implementation steps (A–D) are in place; chunking eval corpus passes automated validation.

---

## Tasks completed

| Step | Description | Status |
|------|-------------|--------|
| A | DB migration (`project_readme_chunks`, `user_evidence_indexes`, FTS5 + triggers) | Done |
| A | `config/llm.yaml` embedding/rerank/retrieval/chunking sections | Done |
| A | `settings.faiss_dir` + related config properties | Done |
| A | `data/faiss/` created on `init_db()` | Done |
| B | `readme_chunker.py` — hierarchical parents + semantic/greedy children | Done |
| B | Fence masking so `#` inside code blocks are not parsed as headings | Done |
| C | `embedding_client.py` — DashScope v4/v3 + qwen3-rerank | Done |
| C | `evidence_index_store.py` — chunk CRUD, FTS5, index bookkeeping | Done |
| C | `faiss_index.py` — per-user IndexFlatIP build/load/search | Done |
| C | `evidence_indexing.py` — orchestrates chunk + FAISS rebuild | Done |
| C | `github.py` wired to index after import | Done |
| D | `retrieve_project_evidence.py` — BM25 + vector + RRF + rerank + bundle | Done |
| D | CV project slot parser (deterministic) | Done |
| F | Chunking pipeline eval — 4 README corpus | Done |
| D | Retrieval unit/integration test | Done |

**Deferred (Phase 3, per plan):** `enrich_job`, `classify_fit`, `package_out`, application subgraph wiring.

---

## Files created

| File | Purpose |
|------|---------|
| `backend/app/services/readme_chunker.py` | Markdown heading parents, semantic/greedy child splits |
| `backend/app/services/embedding_client.py` | DashScope embed + rerank |
| `backend/app/services/evidence_index_store.py` | SQLite chunk CRUD + FTS5 |
| `backend/app/services/faiss_index.py` | Per-user FAISS index |
| `backend/app/services/evidence_indexing.py` | Import-time indexing orchestration |
| `backend/app/services/retrieve_project_evidence.py` | Hybrid retrieval + bundle packer |
| `tests/test_project_evidence_retrieval.py` | Chunker + index + retrieval tests |
| `tests/rag/pipeline/*/chunking-results.md` | Generated chunking eval reports (4 projects) |

## Files modified

| File | Change |
|------|--------|
| `backend/app/db.py` | Phase 2 tables, FTS5 virtual table, sync triggers |
| `backend/app/config.py` | `faiss_dir`, embedding/rerank/retrieval config properties |
| `config/llm.yaml` | embedding, rerank, chunking, retrieval sections |
| `requirements.txt` | `dashscope`, `faiss-cpu`, `numpy` |
| `backend/app/routes/github.py` | Calls `index_project_evidence()` after import |
| `tests/rag/test_chunking_pipeline.py` | Full eval (no longer skipped) |
| `tests/conftest.py` | Isolated `faiss_dir` in test fixture |

---

## Test results

**Command:**
```bash
python -m pytest tests/rag/test_chunking_pipeline.py tests/test_project_evidence_retrieval.py tests/test_project_evidence.py -v
```

**Result:** **18 passed**, 0 failed (2026-07-17)

| Test suite | Tests | Result |
|------------|-------|--------|
| `tests/rag/test_chunking_pipeline.py` | 4 | PASS |
| `tests/test_project_evidence_retrieval.py` | 6 | PASS |
| `tests/test_project_evidence.py` (Phase 1 regression) | 8 | PASS |

### Chunking eval corpus

| Project | Parents | Child chunks | Token cap check |
|---------|---------|--------------|-----------------|
| jobpilot | 23 | 23 | PASS (all ≤ 500) |
| agentic-rag-sub-agents | 26 | 26 | PASS |
| voice-automation | 24 | 24 | PASS |
| whatsapp-mcp-assistant | 6 | 6 | PASS |

**JobPilot required sections present:** `Engineering highlights`, `API surface`, `Agentic architecture` — verified in parent/child `heading_path` values.

Detailed per-project reports: `tests/rag/pipeline/{slug}/chunking-results.md`

### Retrieval smoke test

`test_index_and_retrieve_project_evidence` validates end-to-end:
1. Chunk + insert + FAISS rebuild (pseudo-embeddings when no API key)
2. `retrieve_project_evidence()` returns layers 1, 2a, 2b
3. Layer 2b includes README chunks with relevant heading paths

---

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Chunking + indexing only at import/refresh | Met — `github.py` + `evidence_indexing.py` |
| Every chunk has `user_id`, `project_id`, `heading_path`, `token_count ≤ 500` | Met — enforced in chunker + tests |
| One FAISS index per user; per-project refresh replaces chunks | Met — delete-by-project then rebuild |
| Hybrid search returns chunks with citation metadata | Met — `heading_path`, `project_id`, scores |
| `retrieve_project_evidence()` returns full bundle (layers 1, 2a, 2b) | Met — tested |
| User isolation | Met — all queries filter `user_id` |
| Chunking eval: 4 README corpus passes | Met — see table above |
| JobPilot README retrieves key sections for sample JDs | Met — unit test + chunking eval |

---

## Deviations and notes

1. **Semantic chunking without API key:** Boundary-unit embeddings require `DASHSCOPE_API_KEY`. Without it, chunker falls back to greedy paragraph packing; FAISS uses deterministic pseudo-embeddings. Production import with API key uses real `text-embedding-v4` vectors.

2. **Rerank fallback:** If `qwen3-rerank` fails, retrieval uses RRF ordering only (per design).

3. **FTS5 query sanitization:** Job text tokens are quoted and OR-joined to avoid FTS5 syntax errors; failures log and return empty BM25 hits.

4. **Fence masking fix:** Code-fence contents are masked before heading parse so bash `#` comments are not treated as Markdown headings (fixes Quick start / API surface mis-parenting on JobPilot README).

5. **Plan vs design doc rerank caps:** Implemented plan values (`rerank.top_n: 20`, `max_chunks_per_job: 20`) rather than older design doc values (`top_n: 8`).

---

## Next steps (Phase 3)

1. Wire `retrieve_project_evidence(bundle)` → `enrich_job` LLM call in application subgraph
2. Implement `classify_fit` and `package_out`
3. Optional: project delete/refresh hooks in `profile_store` to reindex when projects are removed
