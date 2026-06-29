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
| **1 — Frontend (locked)** | Welcome, Profile, Search (responsive web) | `[o]` |
| **2 — Data & auth** | Database schema, profile storage, Gmail OAuth | `[o]` |
| **3 — Backend core** | FastAPI, `POST /profile`, `POST /search`, polling | `[ ]` |
| **4 — Agents** | LangGraph search + per-job sub-agents | `[ ]` |
| **5 — HITL flow** | Job detail, send, applications memory | `[ ]` |
| **6 — Deploy** | ECS / Alibaba RDS + OSS (post-hackathon) | `[ ]` |

---

## Active build plan

| Plan | Purpose | Status |
|------|---------|--------|
| [`jobpilot_stitch_ui_plan.md`](.agent/plans/jobpilot_stitch_ui_plan.md) | Stitch desktop UI design + exports | `[x]` |
| [`jobpilot_frontend_web_app_plan.md`](.agent/plans/jobpilot_frontend_web_app_plan.md) | Vite React app: Welcome, Profile, Search | `[o]` |
| `jobpilot_backend_profile_api_plan.md` | FastAPI + SQLite + Gmail OAuth (TBD) | `[ ]` |

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
| `design-system/MASTER.md` (Stitch overrides) | `[ ]` |

### Frontend — Welcome, Profile, Search

| Screen | Route | Status |
|--------|-------|--------|
| Welcome / setup gate | `/` | `[o]` |
| Profile setup | `/profile` | `[o]` |
| New search | `/search` | `[o]` |

| Foundation | Status |
|------------|--------|
| Vite + React + TypeScript + Tailwind (locked) | `[ ]` |
| AppShell: sidebar desktop + drawer mobile | `[ ]` |
| Nav: Profile, Search, Applications†, Settings† (†disabled) | `[ ]` |
| Heroicons; brand **JobPilot** | `[ ]` |
| Profile store + gate rules | `[ ]` |
| CV `.docx` only; target roles; skills/projects editable | `[ ]` |
| GitHub “Coming soon”; Gmail mock connect | `[ ]` |
| Mock API (localStorage until backend) | `[ ]` |

→ Task-level detail: [`frontend/progress.md`](frontend/progress.md) · Build plan: [`jobpilot_frontend_web_app_plan.md`](.agent/plans/jobpilot_frontend_web_app_plan.md)

### Backend & database

| Item | Status | Notes |
|------|--------|--------|
| Profile schema agreed (incl. `target_roles`, `.docx`) | `[x]` | Documented in frontend web app plan |
| Database choice & schema for profile data | `[o]` | Implement in backend plan (TBD) |
| `POST /profile` (CV, skills, projects, roles) | `[ ]` | After frontend ships |
| SQLite MVP (`data/jobpilot.db`) | `[ ]` | Planned per system design |
| `search_runs`, `job_packages`, `applied_jobs` tables | `[ ]` | Phase 3+ |
| `oauth_tokens` table (Gmail) | `[ ]` | Backend plan |

### Integrations

| Integration | Purpose | In frontend screens? | Status |
|-------------|---------|----------------------|--------|
| **Gmail OAuth** | Send approved applications | Profile mock connect | `[o]` Google Console + `.env` done; backend `[ ]` |
| **GitHub** | Auto-import repos | “Coming soon” on Profile | `[x]` locked post-MVP |
| **LinkedIn / Indeed** | Job search (browser worker) | Search screen picks platform | `[ ]` agent phase |

### Agents & orchestration

| Item | Status |
|------|--------|
| LangGraph parent graph + subgraphs | `[ ]` |
| Browser-Use search agent | `[ ]` |
| Per-job application sub-agent | `[ ]` |
| Qwen / model integration | `[ ]` (test scripts only) |

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
| Design | 6 | 0 | 1 (MASTER.md) |
| Frontend web app | 0 | 3 screens + plan | foundation |
| Backend & DB | 1 (schema doc) | 1 | APIs, agents |
| Integrations | 1 (GitHub scope) | 1 (Gmail) | search platforms |

**Last updated:** 2026-06-29
