# Currently Working On

What the team is actively doing **right now**, plus open questions that need decisions before implementation continues.

Update this file when focus shifts. Mirror status changes in [`progress.md`](progress.md) and [`frontend/progress.md`](frontend/progress.md).

---

## Active focus (2026-06-30)

### 1. Cloud deploy `[o]` — live on AWS

**Live:** http://jobpilot-hamza.duckdns.org  
**Guide:** [`System Design/aws-ec2-deploy.md`](System%20Design/aws-ec2-deploy.md)

| Step | Status |
|------|--------|
| EC2 + Elastic IP + Docker Compose | `[x]` |
| GitHub Actions push-to-deploy | `[x]` |
| DuckDNS domain | `[x]` |
| CV upload on cloud | `[x]` |
| GitHub OAuth on cloud | `[x]` |
| Google Console HTTPS redirect URI saved | `[x]` |
| **HTTPS (Let's Encrypt) for Gmail** | `[ ]` **next** |

**Tomorrow — enable Gmail on cloud:**

1. Confirm AWS security group port **443** open
2. SSH to EC2 → run `bash deploy/setup-https.sh` (see aws-ec2-deploy.md)
3. Update GitHub Secret `FRONTEND_URL` → `https://jobpilot-hamza.duckdns.org`
4. Redeploy and test Gmail connect

---

### 2. Search agents `[ ]` — after deploy stable

LangGraph search orchestration and real job search. See [`System Design/JobPilot-System-Design.md`](System%20Design/JobPilot-System-Design.md).

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
| 2026-06-30 | Cloud URL | DuckDNS `jobpilot-hamza.duckdns.org` → Elastic IP `13.251.74.225` |
| 2026-06-30 | Deploy | Docker Compose + GitHub Actions; secrets in GitHub Secrets |
| 2026-06-30 | Gmail on cloud | Requires HTTPS (Let's Encrypt); Google rejects IP-only redirect |
| 2026-06-29 | Frontend scope | Welcome, Profile, Search only (screens 4–8 deferred) |
| 2026-06-29 | Frontend stack | Vite + React + TypeScript + Tailwind |
| 2026-06-29 | CV format | `.docx` only; skills extracted via profile LLM (read-only UI) |
| 2026-06-29 | GitHub | OAuth + README import for project cards |
| 2026-06-29 | Gmail | OAuth connect/disconnect; send deferred to HITL phase |
| 2026-06-29 | Profile storage | SQLite via FastAPI (no localStorage in production path) |
| 2026-06-29 | Backend profile API | Shipped — CV, skills, roles, projects, OAuth |

---

## Next actions

1. **HTTPS setup** for Gmail OAuth on cloud
2. LangGraph search agent + `POST /search`
3. Screens 4–8 (run progress, jobs, HITL)

**Last updated:** 2026-06-30
