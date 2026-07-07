# JobPilot — Project Progress

Overall status for the full JobPilot product (frontend, backend, agents, integrations).

**Detailed frontend checklist:** [`frontend/progress.md`](frontend/progress.md)  
**Active work & open questions:** [`currently-working-feature.md`](currently-working-feature.md)

**Build plans:** [`.agent/plans/`](.agent/plans/) — naming: `jobpilot_<domain>_<scope>_plan.md`

> **Current focus (hackathon — 2 days left):** LinkedIn **Posts** worker works end-to-end and is **frozen** (don't change the worker/agent logic). Next step is packaging it as a downloadable **`.exe`**. Scope, locked decisions, and the exe plan live in **[`currently-working-feature.md`](currently-working-feature.md)** — start there. Jobs-phase deferral rationale in [`job-section-issue.md`](job-section-issue.md); phase flags in [`worker/prompts.py`](worker/prompts.py). Details are not duplicated here on purpose.

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
| `POST /search` + polling | `[o]` | DB-backed API wiring done; graph/worker execution still pending |

### Integrations

| Integration | Purpose | In frontend screens? | Status |
|-------------|---------|----------------------|--------|
| **GitHub** | Auto-import repos | GitHubImport on Profile | `[x]` OAuth + README import |
| **Gmail** | Email send on approve | — | `[x]` cancelled |
| **LinkedIn / Indeed** | Job search (browser worker) | Search screen picks platform | `[o]` LinkedIn Posts working; Indeed deferred → [`currently-working-feature.md`](currently-working-feature.md) |

### Agents & orchestration

| Item | Status |
|------|--------|
| Build guide (ECS + Search Helper + LangGraph phases) | `[x]` spec — [`jobpilot-agent-build-guide.md`](System%20Design/jobpilot-agent-build-guide.md) |
| Search agent design locked | `[x]` — [`search-subgraph-discussion-and-finalization.md`](docs/discussion/search-subgraph-discussion-and-finalization.md) |
| Phase A contracts (models, states, stub APIs) | `[x]` — [`phase-a-step-1-contracts.md`](docs/phase-a-step-1-contracts.md) |
| `langgraph` dependency | `[x]` — `requirements.txt` |
| Parent graph skeleton (nodes + edges) | `[x]` — `backend/app/graph/orchestrator.py` |
| `init_run` node | `[x]` — load run + profile, set `running` |
| ECS search subgraph (`enqueue` → `wait` → `normalize` → `drop_applied`) | `[ ]` **next** |
| `worker_tasks` + worker API routes | `[ ]` |
| Wire `POST /api/search` → background graph | `[ ]` deferred |
| `prefilter` node | `[ ]` |
| JobPilot Search Helper (Kimi WebBridge + Qwen) | `[o]` working (LinkedIn Posts) — **frozen** for hackathon → [`currently-working-feature.md`](currently-working-feature.md) |
| Per-job application sub-agent (`enrich_job`) | `[ ]` |
| Qwen / model integration | `[x]` profile LLM (CV skills, README) · `[ ]` enrich_job |

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
| Backend & DB | 10 | 1 | search subgraph + worker |
| Agents | 5 | 1 | search subgraph, Helper, application |
| Integrations | 1 | 0 | search platforms |
| Deploy | 5 | 0 | 0 |

**Last updated:** 2026-07-07
