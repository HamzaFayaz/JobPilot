# JobPilot — Project Progress

Overall status for the full JobPilot product (frontend, backend, agents, integrations).

**Detailed frontend checklist:** [`frontend/progress.md`](frontend/progress.md)  
**Active work & open questions:** [`currently-working-feature.md`](currently-working-feature.md)

**Build plans:** [`.agent/plans/`](.agent/plans/) — naming: `jobpilot_<domain>_<scope>_plan.md`

> **Current focus:** Search → analysis → Applications inbox is **done**. **Next (last major product step before send):** user-triggered **tailored CV** (`tailor_cv`) — see [`docs/discussion/enrich-job-to-cv-tailoring-handoff.md`](docs/discussion/enrich-job-to-cv-tailoring-handoff.md) and [`currently-working-feature.md`](currently-working-feature.md). Worker search logic stays **frozen**; WebBridge versions locked.

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
| **4 — Agents** | LangGraph search + per-job application analysis | `[x]` |
| **5 — HITL flow** | Applications inbox + decisions | `[x]` · **Tailored CV** `[o]` **next** · Send `[ ]` |
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
| [`cloud-browser-agent.md`](System%20Design/cloud-browser-agent.md) | Cloud Qwen ReAct; Helper = WebBridge executor | `[x]` |
| [`browser-provider-abstraction.md`](System%20Design/browser-provider-abstraction.md) | Kimi WebBridge provider layer + worker protocol | `[x]` |
| [`kimi-webbridge-provider.md`](System%20Design/kimi-webbridge-provider.md) | WebBridge setup, API, version lock | `[x]` |
| [`enrich-job-to-cv-tailoring-handoff.md`](docs/discussion/enrich-job-to-cv-tailoring-handoff.md) | Analysis ↔ tailored CV boundary | `[x]` design · `[o]` **implement next** |
| [`jobpilot-agent-build-guide.md`](System%20Design/jobpilot-agent-build-guide.md) | LangGraph + Search Helper build phases | `[x]` spec |

**Active implementation:** **Tailored CV** (`tailor_cv`) — user-triggered draft from persisted swap plans. Tracking: [`currently-working-feature.md`](currently-working-feature.md).

---

## Workstreams

### Design & UI reference

| Item | Status |
|------|--------|
| Stitch project + 8 desktop screens | `[x]` |
| `.stitch/DESIGN.md` design tokens | `[x]` |
| `frontend/UI Design/` exports (PNG + HTML) | `[x]` |
| Frontend screens 1–3 + Applications | `[x]` |
| Tailored CV preview / download UI | `[ ]` **next** |
| Responsive web UI rules documented | `[x]` |
| ui-ux-pro-max skill installed (`.cursor/skills/`) | `[x]` |
| `design-system/MASTER.md` (Stitch overrides) | `[x]` |

### Frontend — Welcome, Profile, Search, Applications

| Screen | Route | Status |
|--------|-------|--------|
| Welcome / setup gate | `/` | `[x]` |
| Profile setup | `/profile` | `[x]` |
| New search | `/search` | `[x]` |
| Applications inbox (list + detail + decisions) | `/applications` | `[x]` |
| Settings (Search Helper pair + skills/projects) | `/settings` | `[x]` |
| Tailored CV generate / preview / download | job detail / Applications | `[ ]` **next** |

| Foundation | Status |
|------------|--------|
| Vite + React + TypeScript + Tailwind (locked) | `[x]` |
| AppShell: sidebar desktop + drawer mobile | `[x]` |
| Nav: Profile, Search, Applications, Settings | `[x]` |
| Profile store + gate; CV upload; GitHub import | `[x]` |
| Background GitHub import + Search “preparing” wait | `[x]` |
| Per-user `runNumber` display | `[x]` |
| Gmail OAuth (UI + send) | `[ ]` deferred after tailored CV |
| API layer (fetch → FastAPI) | `[x]` |

→ Task-level detail: [`frontend/progress.md`](frontend/progress.md)

### Backend & database

| Item | Status | Notes |
|------|--------|--------|
| Profile schema + SQLite + multi-user | `[x]` | |
| GitHub import + evidence + **background** indexing status | `[x]` | Projects hidden until ready |
| Dual JD (`description_text` raw + `display_description_text`) | `[x]` | Analysis uses raw |
| Listing rewrite (format + apply hints) | `[x]` | |
| `search_runs` / `job_packages` + decisions | `[x]` | |
| Cloud browser agent (`backend/app/services/browser_agent/`) | `[x]` | Server Dashscope |
| Worker thin executor (cloud) + local fallback | `[x]` | |
| Per-user `runNumber` on run APIs | `[x]` | Global `id` unchanged |
| **Tailored CV** API + draft storage | `[ ]` **next** | |

### Integrations

| Integration | Purpose | Status |
|-------------|---------|--------|
| **GitHub** | Auto-import repos | `[x]` |
| **Gmail** | Email send | `[ ]` after tailored CV |
| **LinkedIn / Indeed** | Job search | `[x]` LinkedIn Posts · `[ ]` Indeed / LinkedIn Jobs deferred |
| **Kimi WebBridge** | Browser tools | `[x]` locked daemon `v1.10.0` + ext `1.11.3` |

### Agents & orchestration

| Item | Status |
|------|--------|
| Search subgraph + Search Helper | `[x]` |
| Cloud ReAct on backend (default) | `[x]` |
| `prefilter` → `matched_jobs` | `[x]` |
| Fan-out application subgraph | `[x]` |
| Application analysis (`enrich_job` → `classify_fit` → `package_out`) | `[x]` scores + keep/swap **plans** |
| **Tailored CV** (`tailor_cv` — user-triggered, not in graph) | `[o]` **next / last before send** |
| `persist` (finalize run) | `[x]` |
| Run 3 accuracy baseline | `[x]` ~79/100 — [`evals/system/`](evals/system/) |

**Worker → graph path:** listings → prefilter → **parallel** application subgraphs → packages → **`persist`**.  
**Missing:** generate layout-preserving draft CV from approved swap plans.

### Post-flow validation

Analysis → Applications path works. **Tailored CV** is the remaining HITL gap before attach/send. Optional accuracy backlog: [`optimization/system-accuracy-improvements.md`](optimization/system-accuracy-improvements.md).

### Documentation

| Doc | Status |
|-----|--------|
| System Design core + cloud browser agent | `[x]` |
| CV tailoring handoff | `[x]` design — implement next |
| `evals/system/` Run 3 accuracy | `[x]` |
| `optimization/system-accuracy-improvements.md` | `[x]` backlog |

---

## Deferred screens / features

| Item | Status |
|------|--------|
| Tailored CV generate / preview / download | `[o]` **next** |
| Job detail HITL (send) | `[ ]` after tailored CV |
| Indeed / LinkedIn Jobs platforms | `[ ]` |

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
| Frontend | Applications + Search + Settings | Tailored CV UI | Send |
| Backend & DB | Search, analysis, cloud agent, import | Tailored CV API | — |
| Agents | Search + application analysis | `tailor_cv` | — |
| Integrations | LinkedIn Posts + WebBridge | 0 | Gmail send |
| Deploy | 5 | 0 | 0 |

**Last updated:** 2026-07-18
