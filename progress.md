# JobPilot — Project Progress

Overall status for the full JobPilot product (frontend, backend, agents, integrations).

**Detailed frontend checklist:** [`frontend/progress.md`](frontend/progress.md)  
**Active work & open questions:** [`currently-working-feature.md`](currently-working-feature.md)

**Build plans:** [`.agent/plans/`](.agent/plans/) — naming: `jobpilot_<domain>_<scope>_plan.md`

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
| **2 — Data & auth** | Database schema, profile storage, Gmail OAuth | `[x]` |
| **3 — Backend core** | FastAPI profile API, CV upload, GitHub import | `[o]` |
| **4 — Agents** | LangGraph search + per-job sub-agents | `[ ]` |
| **5 — HITL flow** | Job detail, send, applications memory | `[ ]` |
| **6 — Deploy** | AWS EC2 (active) → Alibaba ECS (submit) | `[o]` |

---

## Active build plan

| Plan | Purpose | Status |
|------|---------|--------|
| [`jobpilot_stitch_ui_plan.md`](.agent/plans/jobpilot_stitch_ui_plan.md) | Stitch desktop UI design + exports | `[x]` |
| [`jobpilot_frontend_web_app_plan.md`](.agent/plans/jobpilot_frontend_web_app_plan.md) | Vite React app: Welcome, Profile, Search | `[x]` |
| [`jobpilot_backend_profile_api_plan.md`](.agent/plans/jobpilot_backend_profile_api_plan.md) | FastAPI + SQLite + CV/Gmail/GitHub | `[x]` |

**Execute frontend build:** `/build .agent/plans/jobpilot_frontend_web_app_plan.md`

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
| Gmail OAuth connect/disconnect | `[x]` |
| API layer (fetch → FastAPI; mock flag optional) | `[x]` |

→ Task-level detail: [`frontend/progress.md`](frontend/progress.md) · Build plan: [`jobpilot_frontend_web_app_plan.md`](.agent/plans/jobpilot_frontend_web_app_plan.md)

### Backend & database

| Item | Status | Notes |
|------|--------|--------|
| Profile schema agreed (incl. `target_roles`, `.docx`) | `[x]` | Documented in frontend web app plan |
| SQLite MVP (`data/jobpilot.db`) | `[x]` | `profiles` + `oauth_tokens` |
| `GET/PUT /api/profile`, `POST /api/profile/cv` | `[x]` | CV parse + LLM skills |
| Gmail OAuth routes | `[x]` | Connect/disconnect; send deferred |
| GitHub OAuth + repo import | `[x]` | README → project cards |
| `POST /search` + polling | `[ ]` | Agent phase |

### Integrations

| Integration | Purpose | In frontend screens? | Status |
|-------------|---------|----------------------|--------|
| **Gmail OAuth** | Send approved applications | Profile connect/disconnect | `[x]` Google + backend routes |
| **GitHub** | Auto-import repos | GitHubImport on Profile | `[x]` OAuth + README import |
| **LinkedIn / Indeed** | Job search (browser worker) | Search screen picks platform | `[ ]` agent phase |

### Agents & orchestration

| Item | Status |
|------|--------|
| LangGraph parent graph + subgraphs | `[ ]` |
| Browser-Use search agent | `[ ]` |
| Per-job application sub-agent | `[ ]` |
| Qwen / model integration | `[x]` profile LLM (CV skills, README) |

### Documentation

| Doc | Status |
|-----|--------|
| `System Design/JobPilot-System-Design.md` | `[x]` |
| `System Design/design-decisions.md` | `[x]` |
| `System Design/dev-time-hardening.md` | `[x]` |
| `System Design/JobPilot-Frontend-Design.md` | `[ ]` |

---

## Profile data map

Long-term memory (DB when backend ships; localStorage during frontend build):

| Screen | User data | Storage |
|--------|-----------|---------|
| Welcome | Checklist state (derived from profile) | Profile record |
| Profile | CV `.docx`, skills[], target_roles[], projects[], Gmail flag | `profiles` + `data/uploads/` |
| Search | One role from profile + platform | `search_runs` on submit (later); form ephemeral until then |

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

## Summary

| Area | Complete | In progress | Not started |
|------|----------|-------------|-------------|
| Design | 7 | 0 | 0 |
| Frontend web app | 11 | 0 | 0 |
| Backend & DB | 6 | 1 | search agents |
| Integrations | 2 | 0 | search platforms |

**Last updated:** 2026-06-29
