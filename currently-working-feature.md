# Currently Working On

**Status:** Search subgraph + Search Helper **done** for hackathon scope (LinkedIn **Posts** only).  
**Next:** **Application subagent** — discuss design and data contract **before** uploading the worker build.

---

## Start here (new chat)

### 1. Discuss application subagent

The search path is working end-to-end. Before distributing the Search Helper `.exe`, align on how the **application subgraph** consumes listing data.

| Topic | Question |
|-------|----------|
| **Application subagent** | Implement `enrich_job` → `score_threshold_gate` → `package_out` in [`backend/app/graph/subgraphs/application/graph.py`](backend/app/graph/subgraphs/application/graph.py) (not implemented yet). |
| **Data contract** | Does the worker’s `RawJobListing` payload need changes, or only backend orchestration (`prefilter`, `matched_jobs`, application nodes)? |
| **Worker upload** | If contract is OK → upload [`worker/dist/JobPilot-SearchHelper.exe`](worker/dist/JobPilot-SearchHelper.exe) and integrate with JobPilot cloud. **No worker/agent logic changes** unless the discussion says otherwise. |

### 2. Where worker sends data (verify before upload)

```
Search Helper (worker)
  POST /api/worker/tasks/{taskId}/result
  Body: { listings: RawJobListing[], warnings: string[] }
       ↓
ECS API  backend/app/routes/worker.py → worker_store.complete_worker_task()
       ↓
SQLite   worker_tasks.result_json  (status = completed)
       ↓
Search subgraph  wait_for_listings() polls wait_for_worker_task_result()
       ↓
Parent graph  persist() → search_store.save_raw_listings_as_packages()
       ↓
SQLite   job_packages  (title, company, url, platform, description_text, status=ready)
         search_runs   (jobs_ready_count, status=completed)
```

**Worker client:** [`worker/api_client.py`](worker/api_client.py) · **Models:** [`worker/models.py`](worker/models.py)  
**Backend store:** [`backend/app/services/worker_store.py`](backend/app/services/worker_store.py) · [`backend/app/services/search_store.py`](backend/app/services/search_store.py)  
**Graph:** [`backend/app/graph/subgraphs/search/graph.py`](backend/app/graph/subgraphs/search/graph.py) · [`backend/app/graph/orchestrator.py`](backend/app/graph/orchestrator.py)

**Open decision:** Application subagent reads from `job_packages` / `RunState` — confirm fields are enough for enrich + score, or extend worker listing shape / `persist` step first.

---

## Search subgraph — done (hackathon scope)

| Item | Status |
|------|--------|
| LinkedIn **Posts** phase | ✅ Working E2E (website search → worker → listings on ECS) |
| Search Helper desktop UI + `.exe` | ✅ [`worker/dist/JobPilot-SearchHelper.exe`](worker/dist/JobPilot-SearchHelper.exe) |
| Worker/agent logic | **Frozen** — do not edit `agent_loop.py`, `prompts.py`, etc. unless data-contract discussion requires it |
| LinkedIn **Jobs** phase | ⏸ Deferred — disabled in [`worker/prompts.py`](worker/prompts.py) ([`job-section-issue.md`](job-section-issue.md)) |
| **Indeed** | ⏸ Deferred — handle later if time |
| `prefilter` / scoring / `matched_jobs` | ✅ normalize, dedupe, drop applied |

UI polish plan (reference only): [`worker/SEARCH_HELPER_UI_PLAN.md`](worker/SEARCH_HELPER_UI_PLAN.md)

---

## Locked decisions (unchanged)

- **Posts phase only** in worker — Jobs phase off in `prompts.py`
- **LinkedIn only** for live search — Indeed later
- Packaging shell + UI OK to edit; search loop is frozen after contract sign-off

---

## Background

- Worker packaging → [`worker/README.md`](worker/README.md)
- WebBridge → [`System Design/kimi-webbridge-provider.md`](System%20Design/kimi-webbridge-provider.md)
- Search design → [`docs/discussion/search-subgraph-discussion-and-finalization.md`](docs/discussion/search-subgraph-discussion-and-finalization.md)
- Jobs deferral → [`job-section-issue.md`](job-section-issue.md)
