# Currently Working On

What the team is actively doing **right now**, plus open questions that need decisions before implementation continues.

Update this file when focus shifts. Mirror status changes in [`progress.md`](progress.md) and [`frontend/progress.md`](frontend/progress.md).

---

## Active focus (2026-07-01)

### 1. Alibaba ECS deploy `[o]` — hackathon cloud (trial running)

**Guide:** [`System Design/alibaba-cloud-trial.md`](System%20Design/alibaba-cloud-trial.md)  
**Domain (reuse):** `jobpilot-hamza.duckdns.org` → point to **Alibaba Elastic IP**  
**Stack:** Same Docker Compose + GitHub Actions as AWS proof-of-deploy

| Step | Status |
|------|--------|
| Alibaba trial ECS running (Singapore) | `[x]` |
| Reset password / SSH key (Workbench asks for password — no default) | `[ ]` **you** |
| Security group 22, 80, 443 | `[ ]` verify |
| Elastic IP on Alibaba | `[ ]` |
| DuckDNS → Alibaba IP | `[ ]` |
| `bootstrap-ec2.sh` on ECS | `[ ]` |
| GitHub Secrets → Alibaba host + SSH key | `[ ]` |
| Deploy via GitHub Actions | `[ ]` |
| CV + GitHub on Alibaba URL | `[ ]` |
| HTTPS (`setup-https.sh`) for Gmail | `[ ]` |
| Google + GitHub OAuth consoles updated | `[o]` partial |

**Connect issue (Workbench / VNC):** Alibaba has **no default password**.  
Console → instance → **All Actions → Reset Instance Password** → login as `root` (or `ecs-user`).  
Official: [Workbench login](https://www.alibabacloud.com/help/en/ecs/user-guide/connect-to-a-linux-instance-by-using-a-password-or-key) · [VNC](https://www.alibabacloud.com/help/en/ecs/user-guide/log-on-to-an-instance-by-using-vnc)

**Share when ready (no secrets):** public IP, SSH username, Elastic IP yes/no.

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
| 2026-07-01 | Domain | Reuse DuckDNS `jobpilot-hamza.duckdns.org`; repoint IP to Alibaba |
| 2026-07-01 | Gmail OAuth | Web app needs HTTPS + redirect URI (not mobile-style); same on Alibaba |
| 2026-06-30 | Deploy | Docker Compose + GitHub Actions; secrets in GitHub Secrets |
| 2026-06-29 | Backend profile API | Shipped locally + proven on AWS |

---

## Next actions

1. Reset Alibaba password / bind SSH key → bootstrap ECS  
2. Update DuckDNS + GitHub Secrets → deploy  
3. HTTPS + Gmail on `jobpilot-hamza.duckdns.org`  
4. LangGraph search agent  

**Last updated:** 2026-07-01
