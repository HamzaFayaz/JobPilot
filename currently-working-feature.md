# Currently Working On

What the team is actively doing **right now**, plus open questions that need decisions before implementation continues.

Update this file when focus shifts. Mirror status changes in [`progress.md`](progress.md) and [`frontend/progress.md`](frontend/progress.md).

---

## Active focus (2026-06-29)

### 1. Execute frontend web app build plan `[o]`

**Plan:** [`.agent/plans/jobpilot_frontend_web_app_plan.md`](.agent/plans/jobpilot_frontend_web_app_plan.md)  
**Run:** `/build .agent/plans/jobpilot_frontend_web_app_plan.md`

Building Welcome, Profile, and Search as a **responsive website** (Stitch desktop = reference only).

| Step | Scope | Status |
|------|-------|--------|
| A0 | ui-ux-pro-max persist → `design-system/MASTER.md` | `[ ]` |
| A | Vite + React + TS + Tailwind + AppShell + nav | `[ ]` |
| B | 3 parallel subagents (Welcome, Profile, Search pages) | `[ ]` |
| C | Integration, a11y, ux validation | `[ ]` |

| Screen | Route | Status |
|--------|-------|--------|
| Welcome | `/` | `[o]` |
| Profile | `/profile` | `[o]` |
| Search | `/search` | `[o]` |

**Locked for this build:**
- **Vite + React + TypeScript + Tailwind** (not Next.js)
- **Heroicons**; brand **JobPilot**
- **Left sidebar** (desktop) + **drawer** (mobile): Profile, Search, Applications†, Settings†
- CV **`.docx` only**; skills, **target roles**, projects — add/edit/remove
- **GitHub:** “Coming soon” · **Gmail:** mock connect (Google OAuth backend later)
- Profile: **localStorage** mock until backend plan ships
- **Git commit after every single file change**

**References:** `frontend/UI Design/01-welcome|02-profile|03-search/` · [`frontend/progress.md`](frontend/progress.md) · [`.cursor/skills/ui-ux-pro-max/SKILL.md`](.cursor/skills/ui-ux-pro-max/SKILL.md)

---

### 2. Database — long-term memory `[o]` (schema locked; build deferred)

Profile data is **long-term memory** in SQLite (later Postgres). Schema documented in frontend web app plan; **implementation waits** for `jobpilot_backend_profile_api_plan.md` (TBD).

| Data | Source screen | Decision |
|------|---------------|----------|
| CV `.docx` + parsed text | Profile | `data/uploads/` local; replaceable file |
| Skills (string list) | Profile | JSON column on `profiles` |
| Target roles (string list) | Profile | JSON column `target_roles` |
| Projects (name + description) | Profile | JSON array on `profiles` |
| Gmail connection | Profile | `oauth_tokens` table |

**Open (minor):**
- [ ] `POST /profile` on every Save vs debounced auto-save?
- [ ] Single `profiles` row (single-user MVP) — **recommended yes**

---

### 3. Gmail connection `[o]`

**Google Cloud OAuth:** Web app client + `.env` credentials — **done** (verified).

| Step | Status |
|------|--------|
| Google Cloud project + Gmail API | `[x]` |
| OAuth client + redirect URI in `.env` | `[x]` |
| `GET /auth/google` + callback (FastAPI) | `[ ]` — backend plan |
| Profile UI mock connect | `[ ]` — frontend plan Phase B |

---

### 4. GitHub connection `[x]` locked

**Decision:** Post-MVP. Profile shows **“Coming soon”**; manual projects only.

---

## Not in focus right now

| Item | Status |
|------|--------|
| Screens 4–8 (run progress, jobs, HITL, applications, settings page) | `[ ]` locked |
| Backend FastAPI + SQLite implementation | `[ ]` — next plan TBD |
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

---

## Next actions

1. **Run** `/build .agent/plans/jobpilot_frontend_web_app_plan.md` (Phase A0 → A → B → C)
2. After frontend ships, **draft** `jobpilot_backend_profile_api_plan.md`
3. Scaffold FastAPI + `profiles` + Gmail OAuth
4. Swap frontend `localStorage` → API

**Last updated:** 2026-06-29
