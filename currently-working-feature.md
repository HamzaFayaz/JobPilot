# Currently Working On

What the team is actively doing **right now**, plus open questions that need decisions before implementation continues.

Update this file when focus shifts. Mirror status changes in [`progress.md`](progress.md) and [`frontend/progress.md`](frontend/progress.md).

---

## Active focus (2026-06-29)

### 1. Frontend web app (Phase 1) `[x]` — shipped

**Plan:** [`.agent/plans/jobpilot_frontend_web_app_plan.md`](.agent/plans/jobpilot_frontend_web_app_plan.md)

Welcome, Profile, and Search are live in `frontend/` as a responsive Vite + React app.

| Step | Scope | Status |
|------|-------|--------|
| A0 | ui-ux-pro-max persist → `design-system/MASTER.md` | `[x]` |
| A | Vite + React + TS + Tailwind + AppShell + nav | `[x]` |
| B | Welcome, Profile, Search pages | `[x]` |
| C | Integration, a11y, ux validation | `[x]` |

**Run locally:** `cd frontend && npm run dev` → http://localhost:5173

---

### 2. Backend profile API `[ ]` — next up

**Plan:** `jobpilot_backend_profile_api_plan.md` (TBD)

| Step | Scope | Status |
|------|-------|--------|
| FastAPI scaffold + SQLite `profiles` | `data/jobpilot.db` | `[ ]` |
| `GET/PUT /profile`, `POST /profile/cv` | Replace localStorage mock | `[ ]` |
| Gmail OAuth `GET /auth/google` | Wire Profile Gmail strip | `[ ]` |

---

### 3. Gmail connection `[o]`

**Google Cloud OAuth:** Web app client + `.env` credentials — **done** (verified).

| Step | Status |
|------|--------|
| Google Cloud project + Gmail API | `[x]` |
| OAuth client + redirect URI in `.env` | `[x]` |
| `GET /auth/google` + callback (FastAPI) | `[ ]` — backend plan |
| Profile UI mock connect | `[x]` — frontend shipped |

---

### 4. GitHub connection `[x]` locked

**Decision:** Post-MVP. Profile shows **“Coming soon”**; manual projects only.

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
| 2026-06-29 | UI source | Stitch desktop = reference; responsive web rules |
| 2026-06-29 | Build plan naming | `jobpilot_frontend_web_app_plan.md` (not “phase 1”) |
| 2026-06-29 | UI quality | ui-ux-pro-max process; Stitch tokens override skill colors/fonts |
| 2026-06-29 | Nav shell | Left sidebar + mobile drawer; 4 items; Applications + Settings disabled |
| 2026-06-29 | CV format | `.docx` only (for future swap optimization) |
| 2026-06-29 | Target roles | Multiple on Profile; one per Search run |
| 2026-06-29 | Profile memory | DB long-term; localStorage for frontend build only |
| 2026-06-29 | GitHub | Coming soon; manual projects |
| 2026-06-29 | Gmail Google Console | OAuth client configured; backend routes deferred |
| 2026-06-29 | Frontend Phase 1 | Shipped — localStorage mock, mock search toast |

---

## Next actions

1. **Draft** `jobpilot_backend_profile_api_plan.md`
2. Scaffold FastAPI + `profiles` + Gmail OAuth
3. Swap frontend `localStorage` → API
4. Implement screens 4–8 after backend + search agent

**Last updated:** 2026-06-29
