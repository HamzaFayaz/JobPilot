# Currently Working On

What the team is actively doing **right now**, plus open questions that need decisions before implementation continues.

Update this file when focus shifts. Mirror status changes in [`progress.md`](progress.md) and [`frontend/progress.md`](frontend/progress.md).

---

## Active focus (2026-06-29)

### 1. Backend profile API `[x]` — shipped

**Plan:** [`.agent/plans/jobpilot_backend_profile_api_plan.md`](.agent/plans/jobpilot_backend_profile_api_plan.md)

FastAPI backend with SQLite profile storage, CV upload + LLM skill extraction, Gmail/GitHub OAuth, and GitHub repo import.

| Step | Scope | Status |
|------|-------|--------|
| FastAPI scaffold + SQLite | `data/jobpilot.db` | `[x]` |
| `GET/PUT /api/profile`, `POST /api/profile/cv` | Replaced localStorage | `[x]` |
| Gmail OAuth connect/disconnect | Profile Gmail strip | `[x]` |
| GitHub OAuth + repo import | GitHubImport component | `[x]` |

**Run locally:**
- Backend: `uvicorn backend.app.main:app --reload --port 8000`
- Frontend: `cd frontend && npm run dev` → http://localhost:5173

---

### 2. Search agents + `POST /search` `[ ]` — next up

LangGraph search orchestration and real job search are deferred to the agent phase.

---

## Not in focus right now

| Item | Status |
|------|--------|
| Screens 4–8 (run progress, jobs, HITL, applications, settings page) | `[ ]` locked |
| LangGraph agents + browser worker | `[ ]` |
| `POST /search` + polling | `[ ]` |
| Gmail send (`POST /jobs/{id}/send`) | `[ ]` |

---

## Decision log

| Date | Topic | Decision |
|------|-------|----------|
| 2026-06-29 | Frontend scope | Welcome, Profile, Search only (screens 4–8 deferred) |
| 2026-06-29 | Frontend stack | Vite + React + TypeScript + Tailwind |
| 2026-06-29 | CV format | `.docx` only; skills extracted via profile LLM (read-only UI) |
| 2026-06-29 | GitHub | OAuth + README import for project cards |
| 2026-06-29 | Gmail | OAuth connect/disconnect; send deferred to HITL phase |
| 2026-06-29 | Profile storage | SQLite via FastAPI (no localStorage in production path) |
| 2026-06-29 | Backend profile API | Shipped — CV, skills, roles, projects, OAuth |

---

## Next actions

1. LangGraph search agent + `POST /search`
2. Screens 4–8 (run progress, jobs, HITL)
3. Gmail send on job approval

**Last updated:** 2026-06-29
