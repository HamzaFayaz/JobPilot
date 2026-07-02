# Currently Working On

What the team is actively doing **right now**, plus open questions that need decisions before implementation continues.

Update this file when focus shifts. Mirror status changes in [`progress.md`](progress.md) and [`frontend/progress.md`](frontend/progress.md).

---

## Active focus — Main agent + sub-agents (2026-07-02)

**Branch:** `jobpilot-with-brosweruse`  
**Master build doc:** [`System Design/jobpilot-agent-build-guide.md`](System%20Design/jobpilot-agent-build-guide.md)  
**Browser layer spec:** [`System Design/browser-provider-abstraction.md`](System%20Design/browser-provider-abstraction.md)

### Goal

Ship the **LangGraph parent orchestrator** with:

1. **search_subgraph** — browser task via **JobPilot Search Helper** (Browser-Use v1)  
2. **application_subgraph** — per-job Qwen sub-agent (`enrich_job` → `job_packages`)  
3. **Async** `POST /api/search` + poll UI  
4. **Demo mode** on ECS for judges (mock jobs, no Helper install)

### Locked architecture (do not revisit without decision)

| Layer | What | Where |
|-------|------|--------|
| **Tier 1** | UI, API, LangGraph, DB, Qwen | **Alibaba ECS** |
| **Tier 2** | JobPilot Search Helper (pairing, poll tasks) | **User PC** — install once, run per session |
| **Tier 3** | `BrowserProvider` — Browser-Use now, WebBridge later | Inside Helper only |

**Rejected:** draw.io-style all-in-browser app · full local backend on user PC.

### Implementation phases (from build guide §7)

| Phase | Scope | Status |
|-------|--------|--------|
| **A** | Models, `BrowserProvider` stubs, DB tables, search API stubs | `[ ]` |
| **B** | Worker pairing + heartbeat + `worker/main.py` poll loop | `[ ]` |
| **C** | `BrowserUseProvider` + local smoke test | `[ ]` |
| **D** | LangGraph parent + **search_subgraph** | `[ ]` |
| **E** | **application_subgraph** + Qwen `enrich_job` + `Send` fan-out | `[ ]` |
| **F** | Run progress UI + demo mode + Helper `.exe` for demo | `[ ]` |
| **G** | WebBridge provider (post-hackathon) | `[ ]` |

### LangGraph components to build

| Component | Type | Status |
|-----------|------|--------|
| Parent orchestrator (`RunState`) | Main graph | `[ ]` |
| `init_run` | Node | `[ ]` |
| `search_subgraph` (`SearchState`) | Subgraph | `[ ]` |
| `prefilter` + cap N | Node | `[ ]` |
| `Send` → application_subgraph × N | Fan-out | `[ ]` |
| `application_subgraph` (`ApplicationState`) | Per-job sub-agent | `[ ]` |
| `persist` job_packages | Node | `[ ]` |
| Browser agent (Layer 3) | Opaque — `BrowserUseProvider` in Helper | `[ ]` |

### Search Helper (user-facing)

| Item | Status |
|------|--------|
| Architecture + UX documented | `[x]` |
| Pairing API + device tokens | `[ ]` |
| Task poll + result POST | `[ ]` |
| Windows `.exe` packaging | `[ ]` |
| UI: SearchHelperStatus + demo mode | `[ ]` |

### API endpoints (target)

| Endpoint | Status |
|----------|--------|
| `POST /api/search` | `[ ]` |
| `GET /api/runs/{runId}/status` | `[ ]` |
| `GET /api/jobs?runId=` | `[ ]` |
| `POST /api/worker/pair` | `[ ]` |
| `GET /api/worker/tasks/next` | `[ ]` |
| `POST /api/worker/tasks/{id}/result` | `[ ]` |

---

## Completed — Multi-user auth `[x]`

See [`jobpilot_multi_user_auth_plan.md`](.agent/plans/jobpilot_multi_user_auth_plan.md). Production: `http://43.98.197.132`.

---

## Completed — Alibaba ECS deploy `[x]`

Guide: [`System Design/alibaba-cloud-trial.md`](System%20Design/alibaba-cloud-trial.md)

---

## Not in focus right now

| Item | Notes |
|------|--------|
| Gmail send / connect UI | Cancelled for MVP |
| HITL screens (job detail, approve send) | After Phase E job list works |
| HTTPS | Not needed without Gmail |
| WebBridge provider | Phase G — swap one layer only |

---

## Decision log

| Date | Topic | Decision |
|------|-------|----------|
| 2026-07-02 | **Agent phase start** | Main LangGraph + search + application subgraphs per [build guide](System%20Design/jobpilot-agent-build-guide.md) |
| 2026-07-02 | **Deployment** | ECS + **JobPilot Search Helper** (install once, run per session) |
| 2026-07-02 | **Browser v1** | Browser-Use in Helper; WebBridge = provider swap later |
| 2026-07-02 | **Hackathon demo** | Mock search on site for judges; real search on presenter PC |
| 2026-07-02 | **Rejected** | Full client-side SPA · full local backend on PC |
| 2026-07-02 | Auth, Gmail, public URL | See prior entries in git history |

---

## Next actions

1. **Phase A** — `models/browser.py`, `search_store.py`, DB migration for `worker_*` tables  
2. **Phase B** — `routes/worker.py` + `worker/main.py` skeleton  
3. **Phase C** — `BrowserUseProvider.search_listings()`  
4. **Phase D–E** — LangGraph orchestrator + sub-agents  

**Last updated:** 2026-07-02
