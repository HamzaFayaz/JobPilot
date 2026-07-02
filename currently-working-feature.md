# Currently Working On

What the team is actively doing **right now**, plus open questions that need decisions before implementation continues.

Update this file when focus shifts. Mirror status changes in [`progress.md`](progress.md) and [`frontend/progress.md`](frontend/progress.md).

---

## Active focus (2026-07-02)

### 1. LangGraph search + browser worker `[ ]` — next

**Goal:** Parent search graph + per-job sub-agents; `POST /search` with `user_id` from session.

**Architecture (locked):** [`System Design/browser-provider-abstraction.md`](System%20Design/browser-provider-abstraction.md) — Browser-Use v1, swappable WebBridge v2 via `BrowserProvider` only.

| Area | Status |
|------|--------|
| Browser provider spec + worker protocol | `[x]` documented |
| `BrowserUseProvider` + local worker | `[ ]` |
| `POST /search` + polling API | `[ ]` |
| Job packages + applications flow | `[ ]` |

---

### 2. Multi-user auth + per-user profiles `[x]` — complete

| Area | Status |
|------|--------|
| Email + password signup/login | `[x]` |
| JWT in httpOnly cookie | `[x]` |
| `users` table + bcrypt passwords | `[x]` |
| `profiles` + `oauth_tokens` scoped by `user_id` | `[x]` |
| Fernet encryption for `cv_text` + OAuth tokens | `[x]` |
| Signup + login UI (`/login`, `/signup`) | `[x]` |
| Protected routes + `credentials: 'include'` | `[x]` |
| GitHub connect bound to logged-in user | `[x]` |
| Uploads under `data/uploads/{user_id}/` | `[x]` |
| Legacy single-user migration (warn only) | `[x]` |

**Deploy note:** Set `JWT_SECRET` and `DATA_ENCRYPTION_KEY` in GitHub Secrets before next production deploy.

---

### 3. Alibaba ECS deploy `[x]` — complete

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
| Screens 4–8 (HITL, applications) | `[ ]` locked |
| HTTPS / Google OAuth | `[ ]` | Not needed without Gmail |
| Email verification / password reset | `[ ]` | Post-hackathon hardening |
| Rate limiting / audit logs | `[ ]` | Post-hackathon hardening |

---

## Decision log

| Date | Topic | Decision |
|------|-------|----------|
| 2026-07-02 | **Auth MVP** | Email/password only; GitHub connect after login (not primary login) |
| 2026-07-02 | **Session** | JWT in httpOnly cookie; all `/api/profile*` and `/api/github*` require auth |
| 2026-07-02 | **Encryption** | bcrypt passwords; Fernet for `cv_text` + OAuth tokens at app level |
| 2026-07-02 | **Browser automation** | **Browser-Use v1** behind `BrowserProvider`; WebBridge v2 = swap one layer ([spec](System%20Design/browser-provider-abstraction.md)) |
| 2026-07-02 | Gmail | **Cancelled** for MVP |
| 2026-07-02 | Public URL | **IP only** (`43.98.197.132`) |

---

## Next actions

1. Add `JWT_SECRET` + `DATA_ENCRYPTION_KEY` to GitHub Actions secrets for production
2. LangGraph search agent (`POST /search`, browser worker)
3. Job detail HITL screens (when agent phase ships)

**Last updated:** 2026-07-02
