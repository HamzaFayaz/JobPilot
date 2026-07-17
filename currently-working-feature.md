# Currently Working On

**Status:** **Phase 2 retrieval done.** **Now:** **Phase 3 — application subagent** (`enrich_job` → `classify_fit` → `package_out`) + graph wiring.

**After full E2E flow works:** validate chunking/retrieval quality before tuning `child_max_tokens` — see [`progress.md` § Post-flow validation](progress.md#post-flow-validation-chunking--retrieval).

**After retrieval:** Application subagent (`enrich_job` → `classify_fit` → `package_out`) — see [`application-subagent-ats-compatibility-discussion.md`](docs/discussion/application-subagent-ats-compatibility-discussion.md).

**Plan:** [`.agent/plans/jobpilot_project_evidence_phase2_plan.md`](.agent/plans/jobpilot_project_evidence_phase2_plan.md) · Phase 1 (done): [`jobpilot_project_evidence_phase1_plan.md`](.agent/plans/jobpilot_project_evidence_phase1_plan.md)

**Phase 2 storage:** [`docs/discussion/phase-2-retrieval-storage-design.md`](docs/discussion/phase-2-retrieval-storage-design.md)

---

## Start here (new chat)

### Phase 1 — Evidence at GitHub import `[x]`

| Item | Status |
|------|--------|
| `build_project_evidence()` + `EVIDENCE_SYSTEM_PROMPT` | ✅ [`profile_llm.py`](backend/app/services/profile_llm.py) |
| `ProjectEvidenceCard` / `ProjectEvidenceResult` models | ✅ [`project_evidence.py`](backend/app/models/project_evidence.py) |
| `StoredProject.portfolio_overview` + `evidence_card` | ✅ [`profile.py`](backend/app/models/profile.py) |
| GitHub import wiring | ✅ [`github.py`](backend/app/routes/github.py) |
| Preserve evidence on profile edit | ✅ [`profile_store.py`](backend/app/services/profile_store.py) |
| Tests | ✅ [`tests/test_project_evidence.py`](tests/test_project_evidence.py) |
| README fixture snapshot | ✅ [`docs/fixtures/evidence-card-mini-overview/`](docs/fixtures/evidence-card-mini-overview/) |

### Phase 2 — README retrieval pipeline `[x]`

**Plan:** [`.agent/plans/jobpilot_project_evidence_phase2_plan.md`](.agent/plans/jobpilot_project_evidence_phase2_plan.md) · Results: [`.agent/results/jobpilot_project_evidence_phase2_build_results.md`](.agent/results/jobpilot_project_evidence_phase2_build_results.md)

| Step | Area | Status |
|------|------|--------|
| Chunking | `readme_chunker.py` | ✅ |
| Storage | SQLite + FAISS + FTS5 | ✅ |
| Retrieval | `retrieve_project_evidence()` | ✅ |
| Tests | `tests/rag/` + chunking eval | ✅ |

### Phase 3 — Application subagent (current)

Prefilter produces `matched_jobs`. Fan-out is wired — each job gets `application_subgraph`.

| Step | File | Task |
|------|------|------|
| **`retrieve_project_evidence`** | new service | Called before `enrich_job` in application subgraph |
| **`enrich_job`** | [`backend/app/graph/subgraphs/application/graph.py`](backend/app/graph/subgraphs/application/graph.py) | One Qwen call — fit facts, `current_cv_score`, `suggested_cv_score`, `project_swaps[]` |
| **`classify_fit`** | same | Clamp scores, swap validation, `fit_tier` + `fit_message` (show all jobs, including below threshold) |
| **`package_out`** | same | Write enriched row to `job_packages` |
| **`persist` refactor** | [`backend/app/graph/orchestrator.py`](backend/app/graph/orchestrator.py) | Finalize run only — `package_out` owns inserts |

**Design:** [`docs/discussion/application-subagent-ats-compatibility-discussion.md`](docs/discussion/application-subagent-ats-compatibility-discussion.md)

### Locked prefilter (done)

- Normalize — field mapping, synthetic `linkedin-post://` URL when empty, title fallback from description
- Dedupe — real URL → apply email → synthetic URL → description hash
- Drop applied — `job_applications` by URL or title+company
- No skill filter, no cap N (worker already bounds listings)

**Code:** [`backend/app/services/listing_prefilter.py`](backend/app/services/listing_prefilter.py) · **Tests:** [`tests/test_prefilter.py`](tests/test_prefilter.py)

---

## End-to-end data flow

```
Search Helper (worker)
  POST /api/worker/tasks/{taskId}/result
       ↓
search_subgraph → prefilter → matched_jobs
       ↓
retrieve_project_evidence(job, profile)   ← DONE (wire into application subgraph in Phase 3)
       ↓
fan_out_applications → application_subgraph
  enrich_job (one LLM) → classify_fit → package_out
       ↓
persist → search_runs (status, jobs_ready_count)
```

**Profile side (build now, at import — not per search):**

```
GitHub import → readme_md + evidence_card + portfolio_overview
        ↓
(chunks/embeddings — Phase 2)
```

---

## Done (hackathon scope)

| Item | Status |
|------|--------|
| LinkedIn **Posts** search E2E | ✅ |
| Search Helper `.exe` | ✅ [`worker/dist/JobPilot-SearchHelper.exe`](worker/dist/JobPilot-SearchHelper.exe) |
| Prefilter | ✅ |
| Fan-out routing | ✅ [`orchestrator.py`](backend/app/graph/orchestrator.py) |
| Project evidence Phase 1 (import) | ✅ |
| Project evidence Phase 2 (retrieval) | ✅ |
| Application subagent | 🔨 **in progress** |
| LinkedIn **Jobs** phase | ⏸ deferred — [`job-section-issue.md`](job-section-issue.md) |
| **Indeed** | ⏸ deferred |

**Frozen:** worker search loop (`agent_loop.py`, `prompts.py`) — no edits unless listing contract changes.

---

## Background

- Project evidence → [`docs/discussion/project-evidence-retrieval-discussion.md`](docs/discussion/project-evidence-retrieval-discussion.md)
- Portfolio overview → [`docs/discussion/project-evidence-portfolio-overview-addendum.md`](docs/discussion/project-evidence-portfolio-overview-addendum.md)
- Application subagent → [`docs/discussion/application-subagent-ats-compatibility-discussion.md`](docs/discussion/application-subagent-ats-compatibility-discussion.md)
- Agent build guide → [`System Design/jobpilot-agent-build-guide.md`](System%20Design/jobpilot-agent-build-guide.md)
- WebBridge → [`System Design/kimi-webbridge-provider.md`](System%20Design/kimi-webbridge-provider.md)
- Search design → [`docs/discussion/search-subgraph-discussion-and-finalization.md`](docs/discussion/search-subgraph-discussion-and-finalization.md)
