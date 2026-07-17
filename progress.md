# JobPilot — Project Progress

Overall status for the full JobPilot product (frontend, backend, agents, integrations).

**Detailed frontend checklist:** [`frontend/progress.md`](frontend/progress.md)  
**Active work & open questions:** [`currently-working-feature.md`](currently-working-feature.md)

**Build plans:** [`.agent/plans/`](.agent/plans/) — naming: `jobpilot_<domain>_<scope>_plan.md`

> **Current focus (hackathon — July 20):** **Phase 2 retrieval done** (chunking, FAISS/FTS5, `retrieve_project_evidence`). **Next:** **Phase 3 application subagent** (`enrich_job` → `classify_fit` → `package_out`) + graph wiring. **After full flow works:** validate chunking/retrieval quality before tuning token limits — see [Post-flow validation](#post-flow-validation-chunking--retrieval). Start at **[`currently-working-feature.md`](currently-working-feature.md)**. Worker search logic stays **frozen**.

---

## Status legend

| Mark | Meaning |
|------|---------|
| `[x]` | **Complete** |
| `[o]` | **In progress** |
| `[ ]` | **Not started** |

---

## Project phases (high level)

| Phase | Scope | Status |
|-------|--------|--------|
| **0 — Design** | Stitch UI, design system, screen exports | `[x]` |
| **1 — Frontend (locked)** | Welcome, Profile, Search (responsive web) | `[x]` |
| **2 — Data & auth** | Single-user profile + GitHub OAuth (MVP) | `[x]` |
| **2b — Multi-user auth** | Login, signup, per-user profiles + tokens | `[x]` |
| **3 — Backend core** | FastAPI profile API, CV upload, GitHub import | `[x]` |
| **4 — Agents** | LangGraph search + per-job sub-agents | `[o]` |
| **5 — HITL flow** | Job detail, send, applications memory | `[ ]` |
| **6 — Deploy** | Alibaba ECS (public IP) | `[x]` |

---

## Active build plan

| Plan | Purpose | Status |
|------|---------|--------|
| [`jobpilot_stitch_ui_plan.md`](.agent/plans/jobpilot_stitch_ui_plan.md) | Stitch desktop UI design + exports | `[x]` |
| [`jobpilot_frontend_web_app_plan.md`](.agent/plans/jobpilot_frontend_web_app_plan.md) | Vite React app: Welcome, Profile, Search | `[x]` |
| [`jobpilot_backend_profile_api_plan.md`](.agent/plans/jobpilot_backend_profile_api_plan.md) | FastAPI + SQLite + CV/GitHub (single-user MVP) | `[x]` |
| [`jobpilot_multi_user_auth_plan.md`](.agent/plans/jobpilot_multi_user_auth_plan.md) | Login, signup, per-user profiles + encryption | `[x]` |
| [`browser-provider-abstraction.md`](System%20Design/browser-provider-abstraction.md) | Kimi WebBridge provider layer + worker protocol (Browser-Use deprecated) | `[x]` spec |
| [`kimi-webbridge-provider.md`](System%20Design/kimi-webbridge-provider.md) | **Active** — WebBridge setup, API, migration from Browser-Use | `[x]` spec |
| [`jobpilot-agent-build-guide.md`](System%20Design/jobpilot-agent-build-guide.md) | **Active** — LangGraph + Search Helper build phases | `[x]` spec |

**Active implementation:** [`docs/discussion/search-subgraph-discussion-and-finalization.md`](docs/discussion/search-subgraph-discussion-and-finalization.md) on branch `jobpilot-with-brosweruse`. Build guide: [`jobpilot-agent-build-guide.md`](System%20Design/jobpilot-agent-build-guide.md).

---

## Workstreams

### Design & UI reference

| Item | Status |
|------|--------|
| Stitch project + 8 desktop screens | `[x]` |
| `.stitch/DESIGN.md` design tokens | `[x]` |
| `frontend/UI Design/` exports (PNG + HTML) | `[x]` |
| Frontend scope locked (screens 1–3 only) | `[x]` |
| Responsive web UI rules documented | `[x]` |
| ui-ux-pro-max skill installed (`.cursor/skills/`) | `[x]` |
| `design-system/MASTER.md` (Stitch overrides) | `[x]` |

### Frontend — Welcome, Profile, Search

| Screen | Route | Status |
|--------|-------|--------|
| Welcome / setup gate | `/` | `[x]` |
| Profile setup | `/profile` | `[x]` |
| New search | `/search` | `[x]` |

| Foundation | Status |
|------------|--------|
| Vite + React + TypeScript + Tailwind (locked) | `[x]` |
| AppShell: sidebar desktop + drawer mobile | `[x]` |
| Nav: Profile, Search, Applications†, Settings† (†disabled) | `[x]` |
| Heroicons; brand **JobPilot** | `[x]` |
| Profile store + gate rules | `[x]` |
| CV `.docx` upload → API; skills read-only from LLM | `[x]` |
| GitHub OAuth + repo import | `[x]` |
| Gmail OAuth (UI + send) | `[x]` cancelled — out of scope for LinkedIn/Indeed |
| API layer (fetch → FastAPI; DB-backed profile/search state) | `[x]` |

→ Task-level detail: [`frontend/progress.md`](frontend/progress.md) · Build plan: [`jobpilot_frontend_web_app_plan.md`](.agent/plans/jobpilot_frontend_web_app_plan.md)

### Backend & database

| Item | Status | Notes |
|------|--------|--------|
| Profile schema agreed (incl. `target_roles`, `.docx`) | `[x]` | Documented in frontend web app plan |
| SQLite MVP (`data/jobpilot.db`) | `[x]` | `users`, `profiles` per `user_id`, `oauth_tokens` composite PK |
| `GET/PUT /api/profile`, `POST /api/profile/cv` | `[x]` | CV parse + LLM skills; auth required |
| Gmail OAuth routes | `[x]` cancelled | Backend exists; UI removed; send not planned |
| GitHub OAuth + repo import | `[x]` | README → project cards; per-user tokens |
| `users` table + login/signup | `[x]` | Email/password + JWT httpOnly cookie |
| Profile + tokens scoped by `user_id` | `[x]` | Fernet encryption for cv_text + OAuth tokens |
| Future tables (`search_runs`, `job_packages`, `job_applications`) | `[x]` | Schema stubs with `user_id` |
| `POST /search` + polling | `[x]` | Graph + worker execution live for LinkedIn Posts |

### Integrations

| Integration | Purpose | In frontend screens? | Status |
|-------------|---------|----------------------|--------|
| **GitHub** | Auto-import repos | GitHubImport on Profile | `[x]` OAuth + README import |
| **Gmail** | Email send on approve | — | `[x]` cancelled |
| **LinkedIn / Indeed** | Job search (browser worker) | Search screen picks platform | `[x]` LinkedIn **Posts** E2E · `[ ]` Indeed deferred · `[ ]` LinkedIn Jobs deferred |

### Agents & orchestration

| Item | Status |
|------|--------|
| Build guide (ECS + Search Helper + LangGraph phases) | `[x]` spec — [`jobpilot-agent-build-guide.md`](System%20Design/jobpilot-agent-build-guide.md) |
| Search agent design locked | `[x]` — [`search-subgraph-discussion-and-finalization.md`](docs/discussion/search-subgraph-discussion-and-finalization.md) |
| Phase A contracts (models, states, stub APIs) | `[x]` — [`phase-a-step-1-contracts.md`](docs/phase-a-step-1-contracts.md) |
| `langgraph` dependency | `[x]` — `requirements.txt` |
| Parent graph skeleton (nodes + edges) | `[x]` — `backend/app/graph/orchestrator.py` |
| `init_run` node | `[x]` — load run + profile, set `running` |
| ECS search subgraph (`enqueue` → `wait` → listings in `job_packages`) | `[x]` LinkedIn Posts E2E |
| `worker_tasks` + worker API routes | `[x]` |
| Wire `POST /api/search` → background graph | `[x]` |
| `prefilter` node (normalize, dedupe, drop applied → `matched_jobs`) | `[x]` — [`listing_prefilter.py`](backend/app/services/listing_prefilter.py) |
| Project evidence Phase 1 (import: card + portfolio overview) | `[x]` — [`profile_llm.py`](backend/app/services/profile_llm.py), [`project_evidence.py`](backend/app/models/project_evidence.py) |
| Project evidence Phase 2 (chunking + retrieval) | `[x]` — [`readme_chunker.py`](backend/app/services/readme_chunker.py), [`retrieve_project_evidence.py`](backend/app/services/retrieve_project_evidence.py) |
| JobPilot Search Helper (Kimi WebBridge + Qwen) | `[x]` `.exe` built |
| Per-job application sub-agent (`enrich_job`) | `[o]` **next** — [`application/graph.py`](backend/app/graph/subgraphs/application/graph.py) |
| Fan-out (`Send` × N application subgraph) | `[x]` wired in [`orchestrator.py`](backend/app/graph/orchestrator.py) |
| Qwen / model integration | `[x]` profile LLM (CV skills, evidence card) · `[ ]` enrich_job |

**Worker → graph path:** Worker `POST …/result` → `worker_tasks` → `wait_for_listings` → **prefilter** → `matched_jobs` → fan-out → application subgraph → `job_packages` + `search_runs`.

### Post-flow validation (chunking & retrieval)

**Do not tune chunking limits until the end-to-end job flow is complete** (import → search → prefilter → `retrieve_project_evidence` → `enrich_job` → `job_packages`).

| Checkpoint | When | Action |
|------------|------|--------|
| **E2E retrieval quality** | After Phase 3 wiring | Run real job listings against imported portfolio; confirm layer 2b chunks hit the right `heading_path` sections (e.g. Engineering highlights, API surface). |
| **Semantic child splits** | Same | Portfolio README eval had **no section > 500 tokens** — semantic merging was not exercised. Re-check only if `enrich_job` misses detail from dense sections. |
| **Token limit tuning** | Only if retrieval weak | Try lowering `child_max_tokens` (e.g. 500 → 350) or re-run chunking eval **with** `DASHSCOPE_API_KEY` on a long section. Do not reduce limits preemptively. |

Build results: [`.agent/results/jobpilot_project_evidence_phase2_build_results.md`](.agent/results/jobpilot_project_evidence_phase2_build_results.md) · Chunking eval: [`tests/rag/pipeline/`](tests/rag/pipeline/)

### Documentation

| Doc | Status |
|-----|--------|
| `System Design/JobPilot-System-Design.md` | `[x]` |
| `System Design/design-decisions.md` | `[x]` |
| `System Design/dev-time-hardening.md` | `[x]` |
| `docs/discussion/search-subgraph-discussion-and-finalization.md` | `[x]` locked — search agent build agreement |
| `docs/discussion/discussion-agentic-design.md` | `[x]` |
| [`kimi-webbridge-provider.md`](System%20Design/kimi-webbridge-provider.md) | `[x]` — WebBridge replaces Browser-Use |
| `System Design/JobPilot-Frontend-Design.md` | `[ ]` |

---

## Profile data map

Long-term memory (DB-backed current state):

| Screen | User data | Storage |
|--------|-----------|---------|
| Welcome | Checklist state (derived from profile) | Profile record |
| Profile | CV `.docx`, skills[], target_roles[], projects[] | `profiles` + `data/uploads/` (per `user_id` after auth) |
| Search | Saved `search_role` + `search_platform`, plus per-run snapshot | `profiles` for current preference; `search_runs` on submit |

---

## Deferred screens (locked out of current frontend build)

| Screen | Route | Status |
|--------|-------|--------|
| Run in progress | `/runs/:runId` | `[ ]` locked |
| Job results list | `/runs/:runId/jobs` | `[ ]` locked |
| Job detail HITL | `/jobs/:id` | `[ ]` locked |
| Applications | `/applications` | `[ ]` locked (nav visible, disabled) |
| Settings | `/settings` | `[ ]` locked (nav visible, disabled) |

---

### Cloud deploy

#### Alibaba ECS (active — hackathon)

| Item | Status |
|------|--------|
| Trial ECS running (Singapore) | `[x]` |
| Docker bootstrap + GitHub Actions deploy | `[x]` |
| Public IP `43.98.197.132` | `[x]` |
| CV + GitHub on cloud | `[x]` |
| Guide | [`System Design/alibaba-cloud-trial.md`](System%20Design/alibaba-cloud-trial.md) |

#### AWS EC2 (proof — can stop)

| Item | Status |
|------|--------|
| Docker Compose + GitHub Actions auto-deploy | `[x]` |
| Superseded by Alibaba | `[x]` |

---

## Summary

| Area | Complete | In progress | Not started |
|------|----------|-------------|-------------|
| Design | 7 | 0 | 0 |
| Frontend web app | 13 | 0 | 0 |
| Backend & DB | 11 | 0 | 0 |
| Agents | 11 | 1 | application enrich + persist refactor |
| Integrations | 1 | 0 | search platforms |
| Deploy | 5 | 0 | 0 |

**Last updated:** 2026-07-17
