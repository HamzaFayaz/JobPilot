# Currently Working On

What the team is actively doing **right now**, plus open questions that need decisions before implementation continues.

Update this file when focus shifts. Mirror status changes in [`progress.md`](progress.md) and [`frontend/progress.md`](frontend/progress.md).

---

## Active focus (2026-07-02)

### 1. Alibaba ECS deploy `[x]` — hackathon cloud

**Guide:** [`System Design/alibaba-cloud-trial.md`](System%20Design/alibaba-cloud-trial.md)  
**Live URL:** `http://43.98.197.132` (public IP — no DuckDNS)  
**Stack:** Docker Compose + GitHub Actions

| Step | Status |
|------|--------|
| Alibaba trial ECS running (Singapore) | `[x]` |
| SSH key + security group 22, 80, 443 | `[x]` |
| `bootstrap-ec2.sh` + GitHub Actions deploy | `[x]` |
| CV + profile API on cloud | `[x]` |
| GitHub OAuth on public IP | `[o]` update OAuth app callback |
| Gmail send | `[ ]` deferred — not needed for LinkedIn/Indeed |

---

### 2. AWS EC2 `[x]` — proof complete (can stop)

| Item | Status |
|------|--------|
| Docker + GitHub Actions | `[x]` |
| CV + GitHub on cloud | `[x]` |
| DuckDNS + Google redirect URI saved | `[x]` |
| HTTPS for Gmail | `[ ]` deferred — do on Alibaba |

---

### 3. Search agents `[ ]` — after Alibaba stable

LangGraph search orchestration. See [`System Design/JobPilot-System-Design.md`](System%20Design/JobPilot-System-Design.md).

---

## Not in focus right now

| Item | Status |
|------|--------|
| Screens 4–8 | `[ ]` locked |
| LangGraph agents + browser worker | `[ ]` |
| `POST /search` + polling | `[ ]` |
| Gmail send | `[ ]` |

---

## Decision log

| Date | Topic | Decision |
|------|-------|----------|
| 2026-07-01 | Cloud platform | **Alibaba ECS trial** = active hackathon target; AWS = proof only |
| 2026-07-02 | Public URL | **Public IP only** (`43.98.197.132`) — DuckDNS removed; hackathon proof uses IP |
| 2026-07-02 | Gmail send | Deferred — LinkedIn/Indeed use in-platform apply, not email |
| 2026-06-30 | Deploy | Docker Compose + GitHub Actions; secrets in GitHub Secrets |
| 2026-06-29 | Backend profile API | Shipped locally + proven on AWS |

---

## Next actions

1. Update GitHub OAuth app callback to `http://43.98.197.132/auth/github/callback`  
2. LangGraph search agent  
