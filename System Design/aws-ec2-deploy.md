# AWS EC2 — JobPilot Deploy (Active)

**Status:** **Primary cloud target** for build, test, and demo while Alibaba trial is unavailable.  
**Last updated:** 2026-06-29  
**Pattern:** **One EC2 instance** — same layout as Alibaba ECS (frontend static + backend API + SQLite on disk).

---

## Strategy

| Stage | Where | Purpose |
|-------|--------|---------|
| **Dev** | Local (`dev.cmd`) | Fast iteration |
| **Cloud test / demo** | **AWS EC2 (this doc)** | Prove features on a real URL |
| **Hackathon submit** | Alibaba ECS | Required for judging — migrate when account works ([`alibaba-cloud-trial.md`](./alibaba-cloud-trial.md)) |

Develop on AWS first; **port to Alibaba** is a host swap (same nginx + uvicorn + SQLite layout).

---

## Recommended EC2 configuration

**Sprint:** ~15–16 days · **one instance only** · no separate RDS.

| Setting | Choice | Why |
|---------|--------|-----|
| **Region** | **ap-southeast-1 (Singapore)** | Close to Dashscope intl API; matches planned Alibaba region |
| **Instance** | **t3.large** (2 vCPU · 8 GiB) | Smooth FastAPI + LangGraph; ~$0.08–0.10/hr |
| **Alternate** | **t3.xlarge** (4 vCPU · 16 GiB) | Closer to Alibaba **ecs.e-c1m2.xlarge** (4C8G) if agents need more CPU |
| **OS** | **Ubuntu 22.04 LTS** | Python 3.10+, nginx, standard FastAPI deploy path |
| **Storage** | **30–50 GiB gp3** root volume | OS + app + `data/jobpilot.db` + `data/uploads/` |
| **Count** | **1** | Frontend + backend on same box |

### Do **not** add (for MVP)

| Option | Reason |
|--------|--------|
| **RDS** | SQLite on EC2 disk is enough for hackathon |
| **Second EC2** | One box hosts everything |
| **WordPress / LAMP AMI** | Wrong stack — use Docker Compose (see below) |

---

## Architecture (Docker Compose on one server)

```
User's laptop                 AWS EC2 (Singapore)
┌──────────────────┐         ┌─────────────────────────────────┐
│ Chrome + Browser │◄───────►│  web container (nginx :80)      │
│ Worker (local)   │  HTTP   │    /     → React static build   │
└──────────────────┘         │    /api  → api container :8000  │
                             │  api container (FastAPI)        │
                             │    data/jobpilot.db (volume)    │
                             │    data/uploads/ (CV files)     │
                             └─────────────────────────────────┘
                                        │
                                   Qwen Dashscope API
                                   Gmail / GitHub OAuth
```

- **Two containers:** `web` (React + nginx) and `api` (FastAPI).
- **EC2 runs:** Docker Compose — **not** the browser.
- **Browser-Use** stays on the user's machine.

---

## Security group (inbound)

| Port | Source | Purpose |
|------|--------|---------|
| **22** | Your IP only | SSH |
| **80** | `0.0.0.0/0` | HTTP (or 443 if TLS) |
| **443** | `0.0.0.0/0` | HTTPS (recommended with Let's Encrypt) |

Do **not** expose port 8000 publicly — the `web` container proxies to `api` on the internal Docker network.

---

## Local Docker (optional)

```bash
cp .env.example .env   # fill in keys
docker compose up --build
```

Open http://localhost — same layout as production.

---

## `.env` on EC2 (production)

```env
# App
FRONTEND_URL=https://your-domain-or-ec2-dns
API_HOST=0.0.0.0
API_PORT=8000

# Qwen (works from AWS)
DASHSCOPE_API_KEY=sk-...
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen3.7-plus
PROFILE_LLM_MODEL=qwen-turbo

# OAuth — update redirect URIs in Google/GitHub consoles to this host
GOOGLE_REDIRECT_URI=https://your-domain/auth/google/callback
GITHUB_REDIRECT_URI=https://your-domain/auth/github/callback

GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

**OAuth note:** Replace `http://localhost:8000/...` with your EC2 public URL (or Elastic IP + domain).

---

**Live URL:** http://jobpilot-hamza.duckdns.org (HTTP) · https://jobpilot-hamza.duckdns.org (after HTTPS setup)

---

## HTTPS for Gmail OAuth `[ ]` — next step

Google OAuth **requires HTTPS** on a real domain. Raw IP and HTTP-only DuckDNS work for CV + GitHub; **Gmail needs Let's Encrypt**.

| Item | Status |
|------|--------|
| DuckDNS `jobpilot-hamza.duckdns.org` → Elastic IP | `[x]` |
| Google Console redirect `https://jobpilot-hamza.duckdns.org/auth/google/callback` | `[x]` |
| GitHub OAuth callback on DuckDNS | `[x]` |
| AWS security group port **443** open | `[ ]` verify |
| Let's Encrypt cert on EC2 | `[ ]` run `deploy/setup-https.sh` |
| `FRONTEND_URL` switched to `https://` in GitHub Secrets | `[ ]` after cert |

### Run HTTPS setup (one time, on EC2)

```bash
ssh -i your-key.pem ubuntu@13.251.74.225
cd /opt/jobpilot
export DOMAIN=jobpilot-hamza.duckdns.org
export CERTBOT_EMAIL=you@example.com
bash deploy/setup-https.sh
```

Then update GitHub Secrets:

| Secret | Value |
|--------|--------|
| `FRONTEND_URL` | `https://jobpilot-hamza.duckdns.org` |

Redeploy (push to `main` or `gh workflow run deploy.yml`). Test Gmail at https://jobpilot-hamza.duckdns.org/profile.

---

## Automated deploy (GitHub Actions)

**Push to `main` → cloud updates automatically.** No manual SSH per change.

| File | Purpose |
|------|---------|
| [`docker-compose.yml`](../docker-compose.yml) | `web` + `api` services |
| [`deploy/Dockerfile.api`](../deploy/Dockerfile.api) | FastAPI container image |
| [`deploy/Dockerfile.web`](../deploy/Dockerfile.web) | React build + nginx container image |
| [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) | rsync → `docker compose build` → restart |
| [`deploy/bootstrap-ec2.sh`](../deploy/bootstrap-ec2.sh) | One-time Docker install on EC2 |
| [`deploy/setup-https.sh`](../deploy/setup-https.sh) | One-time Let's Encrypt HTTPS (Gmail OAuth) |
| [`deploy/nginx-docker-ssl.conf.template`](../deploy/nginx-docker-ssl.conf.template) | HTTPS nginx config template |

**GitHub Secrets** (private repo — ~360 min for 6 deploys/day × 10 days):

| Secret | Value |
|--------|--------|
| `EC2_HOST` | Elastic IP or public DNS |
| `EC2_USER` | `ubuntu` |
| `EC2_SSH_KEY` | Private deploy key (from bootstrap script) |

---

## Setup checklist (one-time)

1. [ ] Launch **Ubuntu 22.04** · **t3.large** · **ap-southeast-1** · 30–50 GiB gp3
2. [ ] Attach **Elastic IP** (stable URL for OAuth)
3. [ ] Security group: 22 (your IP), 80, 443
4. [ ] SSH in, run bootstrap:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/YOUR_USER/JobPilot/main/deploy/bootstrap-ec2.sh | bash
   ```
   Or clone the repo and run `bash deploy/bootstrap-ec2.sh`
5. [ ] Add GitHub Secrets: `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`
6. [ ] Create `/opt/jobpilot/.env` from `.env.example` — set `FRONTEND_URL`, OAuth redirect URIs, API keys
7. [ ] Update Google Cloud + GitHub OAuth apps with production callback URLs
8. [ ] Push to `main` — GitHub Actions deploys automatically
9. [ ] Smoke test: `/health`, `/api/profile`, Gmail connect, CV upload

---

## Database & files (no extra AWS services)

| Data | Location on EC2 |
|------|-----------------|
| Profile, OAuth tokens | `data/jobpilot.db` (SQLite) |
| CV uploads | `data/uploads/` |
| Frontend build | `frontend/dist/` |

All on the **root EBS volume** — no RDS, no S3 required for MVP.

---

## Cost estimate (~16 days)

| Instance | ~384 hrs | Rough cost |
|----------|----------|------------|
| t3.large | 384 × ~$0.083 | **~$32** |
| t3.xlarge | 384 × ~$0.166 | **~$64** |

Plus minimal EBS + egress. Use **AWS Free Tier** if your account qualifies (t2/t3.micro limited — may be tight for agents).

---

## Migrate to Alibaba later

Same steps on **one ECS** instance in Singapore:

1. Copy `data/` (SQLite + uploads)
2. Copy `.env` (update `FRONTEND_URL`, redirect URIs, optional OSS vars)
3. Same nginx + uvicorn layout

See [`alibaba-cloud-trial.md`](./alibaba-cloud-trial.md).

---

## Related docs

- [`alibaba-cloud-trial.md`](./alibaba-cloud-trial.md) — hackathon submission target
- [`JobPilot-System-Design.md`](./JobPilot-System-Design.md) — local browser worker invariant
- [`../README.md`](../README.md) — project overview
