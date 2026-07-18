# JobPilot — Project Progress

Overall status for the full JobPilot product (frontend, backend, agents, integrations).

**Detailed frontend checklist:** [`frontend/progress.md`](frontend/progress.md)  
**Active work & open questions:** [`currently-working-feature.md`](currently-working-feature.md)

**Build plans:** [`.agent/plans/`](.agent/plans/) — naming: `jobpilot_<domain>_<scope>_plan.md`

> **Current focus:** Application **analysis** is done (scores + keep/swap plans, Run 3 ~79/100). **Next backend:** **create Suggested CV** from those plans (not a separate CV Tailor / DOCX workflow). **Next frontend:** per-job application progress UI (`04-run-progress/`). Start at **[`currently-working-feature.md`](currently-working-feature.md)**. Worker search logic stays **frozen**.

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
| **4 — Agents** | LangGraph search + per-job application sub-agents | `[x]` analysis · `[ ]` Suggested CV · `[o]` application UI |
| **5 — HITL flow** | Job detail, send, applications memory | `[ ]` (CV Tailor / edit-cv **not needed**) |
| **6 — Deploy** | Alibaba ECS (public IP) | `[x]` |

---

## Active build plan

| Plan | Purpose | Status |
|------|---------|--------|
| [`jobpilot_stitch_ui_plan.md`](.agent/plans/jobpilot_stitch_ui_plan.md) | Stitch desktop UI design + exports | `[x]` |
| [`jobpilot_frontend_web_app_plan.md`](.agent/plans/jobpilot_frontend_web_app_plan.md) | Vite React app: Welcome, Profile, Search | `[x]` |
| [`jobpilot_backend_profile_api_plan.md`](.agent/plans/jobpilot_backend_profile_api_plan.md) | FastAPI + SQLite + CV/GitHub (single-user MVP) | `[x]` |
| [`jobpilot_multi_user_auth_plan.md`](.agent/plans/jobpilot_multi_user_auth_plan.md) | Login, signup, per-user profiles + encryption | `[x]` |
| [`jobpilot_phase2_recall_phase3_llm_authority_plan.md`](.agent/plans/jobpilot_phase2_recall_phase3_llm_authority_plan.md) | Retrieval recall + LLM-authority application | `[x]` Run 3 baseline |
| [`browser-provider-abstraction.md`](System%20Design/browser-provider-abstraction.md) | Kimi WebBridge provider layer + worker protocol | `[x]` spec |
| [`kimi-webbridge-provider.md`](System%20Design/kimi-webbridge-provider.md) | WebBridge setup, API, migration from Browser-Use | `[x]` spec |
| [`jobpilot-agent-build-guide.md`](System%20Design/jobpilot-agent-build-guide.md) | LangGraph + Search Helper build phases | `[x]` spec |

**Active implementation:** **Suggested CV** creation (backend), then per-job application **UI**. Graph: [`orchestrator.py`](backend/app/graph/orchestrator.py). Tracking: [`currently-working-feature.md`](currently-working-feature.md).

---

## Workstreams

### Design & UI reference

| Item | Status |
|------|--------|
| Stitch project + 8 desktop screens | `[x]` |
| `.stitch/DESIGN.md` design tokens | `[x]` |
| `frontend/UI Design/` exports (PNG + HTML) | `[x]` |
| Frontend screens 1–3 shipped | `[x]` |
| Unlock screen 4 for application progress | `[o]` |
| Responsive web UI rules documented | `[x]` |
| ui-ux-pro-max skill installed (`.cursor/skills/`) | `[x]` |
| `design-system/MASTER.md` (Stitch overrides) | `[x]` |

### Frontend — Welcome, Profile, Search

| Screen | Route | Status |
|--------|-------|--------|
| Welcome / setup gate | `/` | `[x]` |
| Profile setup | `/profile` | `[x]` |
| New search | `/search` | `[x]` |
| Run / application progress (per-job cards) | `/search` or `/runs/:runId` | `[o]` **next** — ref `UI Design/04-run-progress/` |

| Foundation | Status |
|------------|--------|
| Vite + React + TypeScript + Tailwind (locked) | `[x]` |
| AppShell: sidebar desktop + drawer mobile | `[x]` |
| Nav: Profile, Search, Applications†, Settings† (†disabled) | `[x]` |
| Heroicons; brand **JobPilot** | `[x]` |
| Profile store + gate rules | `[x]` |
| CV `.docx` upload → API; skills read-only from LLM | `[x]` |
| GitHub OAuth + repo import | `[x]` |
| Gmail OAuth (UI + send) | `[x]` cancelled |
| API layer (fetch → FastAPI) | `[x]` |

→ Task-level detail: [`frontend/progress.md`](frontend/progress.md)

### Backend & database

| Item | Status | Notes |
|------|--------|--------|
| Profile schema + SQLite MVP | `[x]` | |
| `GET/PUT /api/profile`, `POST /api/profile/cv` | `[x]` | |
| GitHub OAuth + repo import + evidence index | `[x]` | |
| Multi-user auth | `[x]` | |
| `search_runs` / `job_packages` | `[x]` | Live |
| `POST /search` + polling | `[x]` | Graph + worker + application fan-out |

### Integrations

| Integration | Purpose | Status |
|-------------|---------|--------|
| **GitHub** | Auto-import repos | `[x]` |
| **Gmail** | Email send | `[x]` cancelled |
| **LinkedIn / Indeed** | Job search | `[x]` LinkedIn Posts · `[ ]` Indeed / LinkedIn Jobs deferred |

### Agents & orchestration

| Item | Status |
|------|--------|
| Search subgraph + Search Helper | `[x]` |
| `prefilter` → `matched_jobs` | `[x]` |
| Fan-out (`Send` × N application subgraph) | `[x]` parallel per job |
| Application analysis (`enrich_job` → `classify_fit` → `package_out`) | `[x]` Max + `enrich_job_v4` — scores + keep/swap plans |
| **Suggested CV** creation (from swap plans) | `[ ]` **next backend** |
| CV Tailor (full DOCX / edit-cv HITL) | `[x]` cancelled — **not needed** |
| `persist` (finalize run) | `[x]` |
| Application-agent **UI** (per-job live cards) | `[o]` next frontend |
| Run 3 accuracy baseline | `[x]` ~79/100 — [`evals/system/`](evals/system/) |

**Worker → graph path:** listings → prefilter → **parallel** application subgraphs → packages → **`persist`**. Suggested CV still missing after analysis.

### Post-flow validation

Analysis → package path works. **Suggested CV** is the remaining application-backend gap. Retrieve/rerank noise reduction is optional backlog ([`optimization/system-accuracy-improvements.md`](optimization/system-accuracy-improvements.md)).

### Documentation

| Doc | Status |
|-----|--------|
| System Design core docs | `[x]` |
| `evals/system/` Run 3 accuracy | `[x]` |
| `optimization/system-accuracy-improvements.md` | `[x]` backlog |
| `System Design/JobPilot-Frontend-Design.md` | `[ ]` |

---

## Deferred screens

| Screen | Route | Status |
|--------|-------|--------|
| Run in progress (per-job application cards) | `/runs/:runId` or enrich `/search` | `[o]` **unlock — next UI** |
| Job results list | `/runs/:runId/jobs` | `[ ]` can merge with run progress |
| Job detail HITL | `/jobs/:id` | `[ ]` locked |
| Applications | `/applications` | `[ ]` locked |
| Settings | `/settings` | `[ ]` locked |

---

### Cloud deploy

| Item | Status |
|------|--------|
| Alibaba ECS Singapore + Actions deploy | `[x]` |
| Public IP `43.98.197.132` | `[x]` |

---

## Summary

| Area | Complete | In progress | Not started |
|------|----------|-------------|-------------|
| Design | 7 | 0 | 0 |
| Frontend web app | 13 | 1 (application progress UI) | HITL screens |
| Backend & DB | 11 | 0 | 0 |
| Agents | backend done | application UI | — |
| Integrations | LinkedIn Posts | 0 | other platforms |
| Deploy | 5 | 0 | 0 |

**Last updated:** 2026-07-18
