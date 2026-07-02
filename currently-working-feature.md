# Currently Working On

What the team is actively doing **right now**, plus open questions that need decisions before implementation continues.

Update this file when focus shifts. Mirror status changes in [`progress.md`](progress.md) and [`frontend/progress.md`](frontend/progress.md).

---

## Active focus (2026-07-02)

### 1. Multi-user auth + per-user profiles `[o]`

**Goal:** Replace the single global profile with **login / signup** and **isolated data per user** (CV, skills, projects, GitHub tokens).

**Live deploy (unchanged):** http://43.98.197.132 — hackathon proof on Alibaba ECS.

| Area | Status |
|------|--------|
| Auth method decision (email/password vs OAuth-only vs both) | `[ ]` |
| `users` table + password hashing or OAuth identity mapping | `[ ]` |
| Session / JWT (or cookie) on API requests | `[ ]` |
| `profiles` + `oauth_tokens` scoped by `user_id` | `[ ]` |
| Signup + login UI (new routes) | `[ ]` |
| Profile API requires authenticated user | `[ ]` |
| GitHub connect stores token per user | `[ ]` |
| Migrate/remove single-row MVP assumptions | `[ ]` |

**Proposed scope (MVP):**

| Method | Purpose |
|--------|---------|
| **Email + password** | Sign up, log in, reset password (later) |
| **GitHub OAuth** | Optional login **or** link-after-signup (reuse existing GitHub app) |
| **Session** | HTTP-only cookie or Bearer JWT; all `/api/profile*` routes require auth |

**Data model (target):**

```
users          id, email, password_hash?, created_at
profiles       user_id (FK), cv_path, skills, target_roles, projects, ...
oauth_tokens   user_id (FK), provider, tokens, email/login
```

**Open questions:**

1. GitHub OAuth as **primary login** or only **profile import** after email signup?
2. Keep Welcome gate for logged-in users only, or redirect unauthenticated users to `/login`?
3. File uploads: `data/uploads/{user_id}/` per user on disk?

**References:** [`System Design/dev-time-hardening.md`](System%20Design/dev-time-hardening.md) §1 · [`System Design/design-decisions.md`](System%20Design/design-decisions.md)

---

### 2. Alibaba ECS deploy `[x]` — complete

| Step | Status |
|------|--------|
| ECS + Docker + GitHub Actions | `[x]` |
| Public IP `43.98.197.132` (no DuckDNS) | `[x]` |
| CV + GitHub on cloud | `[x]` |
| GitHub OAuth callback on IP | `[x]` user updated OAuth app |

Guide: [`System Design/alibaba-cloud-trial.md`](System%20Design/alibaba-cloud-trial.md)

---

## Not in focus right now

| Item | Status | Notes |
|------|--------|--------|
| **Gmail send / connect UI** | `[x]` cancelled | LinkedIn/Indeed use in-platform apply; backend routes remain unused |
| LangGraph search agents | `[ ]` | After auth + per-user profiles |
| Screens 4–8 (HITL, applications) | `[ ]` locked |
| HTTPS / Google OAuth | `[ ]` | Not needed without Gmail |

---

## Decision log

| Date | Topic | Decision |
|------|-------|----------|
| 2026-07-02 | **Next phase** | **Multi-user auth** — login/signup + `user_id` on profiles and OAuth tokens |
| 2026-07-02 | Gmail | **Cancelled** for MVP — removed from UI; no email-send flow for LinkedIn/Indeed |
| 2026-07-02 | Public URL | **IP only** (`43.98.197.132`) for deploy and hackathon proof |
| 2026-07-01 | Cloud platform | Alibaba ECS trial = hackathon target |
| 2026-06-30 | Deploy | Docker Compose + GitHub Actions |

---

## Next actions

1. Decide auth methods (email/password + optional GitHub login)
2. Add `users` table and migrate profile/OAuth storage to `user_id`
3. Build `/login` and `/signup` screens + protected routes
4. LangGraph search agent (after per-user data works)

**Last updated:** 2026-07-02
