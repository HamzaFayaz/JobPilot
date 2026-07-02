# Alibaba Cloud — ECS Deploy (Active)

**Status:** **Primary cloud target** — trial instance running (hackathon submission).  
**Previous:** AWS EC2 proof-of-deploy → [`aws-ec2-deploy.md`](./aws-ec2-deploy.md)  
**Last updated:** 2026-07-01  
**Hackathon requirement:** Agent backend on Alibaba Cloud ECS ([`jobpilot_prd.md`](../jobpilot_prd.md))

---

## Deploy strategy

| Phase | Platform | Status |
|-------|----------|--------|
| **Proof of deploy** | AWS EC2 | `[x]` Docker + GitHub Actions + DuckDNS |
| **Active / submit** | **Alibaba ECS (this doc)** | `[o]` migrate host + OAuth + HTTPS |
| **Local dev** | `dev.cmd` | `[x]` unchanged |

**Same stack on Alibaba:** Docker Compose (`web` + `api`), GitHub Actions rsync + deploy, SQLite on disk, DuckDNS domain.

---

## Instance spec (trial)

| Setting | Choice |
|---------|--------|
| **Region** | **Singapore** (`ap-southeast-1`) |
| **Instance** | **ecs.e-c1m2.xlarge** — 4 vCPU · 8 GiB |
| **Disk** | **ESSD Entry · 100 GiB** |
| **OS** | **Ubuntu 22.04 64-bit** |
| **Pre-installed apps** | **None** |
| **Count** | **1** |

---

## Connect to the instance (official Alibaba)

Alibaba ECS has **no default password**. Workbench and VNC both need the **instance username + password** (or SSH key).

**Official docs:**
- [Log on with Workbench](https://www.alibabacloud.com/help/en/ecs/user-guide/connect-to-a-linux-instance-by-using-a-password-or-key)
- [Connect with VNC](https://www.alibabacloud.com/help/en/ecs/user-guide/log-on-to-an-instance-by-using-vnc)
- [Username / password / keys](https://www.alibabacloud.com/help/en/ecs/user-guide/instance-logon-credential-management)

### Why Workbench / VNC asks for a password

| Fact | Detail |
|------|--------|
| **No default password** | Alibaba never assigns one — you set or reset it |
| **No separate VNC password** | Since July 2023, VNC uses the **same instance password** |
| **Default Linux username** | `root` (or `ecs-user` if chosen at creation) |

### Fix: reset instance password (console)

1. ECS Console → **Instances** → select your instance  
2. **All Actions** → **Reset Instance Password** (try **online** reset first)  
3. Set a strong password → confirm  
4. If offline reset required → instance **reboots**  
5. Connect again via Workbench or VNC with `root` + new password  

### Recommended connection methods (JobPilot deploy)

| Method | Use for | Notes |
|--------|---------|-------|
| **Workbench → Password-free login** | Quick console access | Easiest in browser; no SSH key needed |
| **SSH from your PC** | Deploy + `bootstrap-ec2.sh` | **Preferred for GitHub Actions** — bind key pair |
| **VNC** | Rescue / password verify | Use after reset to confirm OS login works |

### SSH key pair (for GitHub Actions deploy)

1. ECS Console → **Key Pairs** → Create (or use existing `.pem`)  
2. **Bind key pair** to instance (or set at creation)  
3. Security group: **22** from your IP + GitHub Actions needs SSH from internet (`0.0.0.0/0` for deploy key only — or self-hosted runner later)  
4. Default user for Ubuntu images: usually **`root`** — verify in instance details  

```bash
ssh -i your-alibaba-key.pem root@<PUBLIC_IP>
```

---

## Architecture (one ECS — same as AWS)

```
User's laptop                    Alibaba ECS (Singapore)
┌─────────────────────┐         ┌──────────────────────────┐
│ Chrome + Browser    │◄───────►│  web (nginx :80/:443)    │
│ Worker (local)      │  HTTPS  │  api (FastAPI :8000)     │
└─────────────────────┘         │  data/jobpilot.db        │
                                │  data/uploads/           │
                                └──────────────────────────┘
```

---

## What we need to wire JobPilot (checklist)

### From you (safe to share in chat)

```
Alibaba ECS:
- Public IP:
- Region: Singapore
- Instance ID:
- SSH username: root or ecs-user
- Elastic IP attached: yes/no
- Security group: 22, 80, 443 open
- DuckDNS updated to new IP: yes/no
```

### GitHub Secrets (update for Alibaba)

| Secret | Value |
|--------|--------|
| `EC2_HOST` | Alibaba **public / Elastic IP** |
| `EC2_USER` | `root` or `ecs-user` |
| `EC2_SSH_KEY` | Private key `.pem` content |
| `DOMAIN` | `jobpilot-hamza.duckdns.org` |
| `FRONTEND_URL` | `http://jobpilot-hamza.duckdns.org` → `https://` after SSL |
| `GOOGLE_REDIRECT_URI` | `https://jobpilot-hamza.duckdns.org/auth/google/callback` |
| `GH_OAUTH_REDIRECT_URI` | `http://jobpilot-hamza.duckdns.org/auth/github/callback` |
| App keys | `DASHSCOPE_API_KEY`, `GOOGLE_*`, `GH_OAUTH_*` (unchanged) |

### One-time on ECS

1. [ ] Reset password OR bind SSH key (see above)  
2. [ ] Security group: **22** (your IP), **80**, **443**  
3. [ ] Attach **Elastic IP** (stable URL)  
4. [ ] DuckDNS: point `jobpilot-hamza.duckdns.org` → **Alibaba Elastic IP**  
5. [ ] SSH in → `bash deploy/bootstrap-ec2.sh`  
6. [ ] Update GitHub Secrets → push/deploy (or workflow dispatch)  
7. [ ] Run `bash deploy/setup-https.sh` → Gmail on cloud  
8. [ ] Optional: copy `data/` from AWS if migrating profiles  

**Deploy files:** same as AWS — [`docker-compose.yml`](../docker-compose.yml), [`deploy/`](../deploy/), [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml)

---

## OAuth consoles (Alibaba + DuckDNS)

Reuse domain **`jobpilot-hamza.duckdns.org`** — update DuckDNS IP to Alibaba, not AWS.

### Google Cloud (Gmail)

**Credentials** → OAuth client → Authorized redirect URIs:

```
http://localhost:8000/auth/google/callback
https://jobpilot-hamza.duckdns.org/auth/google/callback
```

**Authorized JavaScript origins:**

```
http://localhost:5173
https://jobpilot-hamza.duckdns.org
```

Gmail **requires HTTPS** on cloud — run `deploy/setup-https.sh` after deploy.

### GitHub OAuth App

| Field | Value |
|-------|--------|
| **Homepage URL** | `http://jobpilot-hamza.duckdns.org` |
| **Authorization callback URL** | `http://jobpilot-hamza.duckdns.org/auth/github/callback` |

GitHub works on HTTP; Gmail needs HTTPS.

---

## Production `.env` (on ECS at `/opt/jobpilot/.env`)

Written automatically from GitHub Secrets on deploy. Target values:

```env
DOMAIN=jobpilot-hamza.duckdns.org
FRONTEND_URL=https://jobpilot-hamza.duckdns.org
GOOGLE_REDIRECT_URI=https://jobpilot-hamza.duckdns.org/auth/google/callback
GITHUB_REDIRECT_URI=http://jobpilot-hamza.duckdns.org/auth/github/callback
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

---

## Database & storage

| Data | Where |
|------|--------|
| Profiles, OAuth tokens | `data/jobpilot.db` on ECS disk |
| CV uploads | `data/uploads/` |
| **RDS / OSS** | Not needed for hackathon MVP |

---

## Migration from AWS

| Step | Action |
|------|--------|
| 1 | Start Alibaba ECS, bootstrap Docker |
| 2 | Update DuckDNS → Alibaba IP |
| 3 | Update GitHub Secrets `EC2_HOST` |
| 4 | Deploy from `main` |
| 5 | `scp` or copy `data/` from AWS (optional) |
| 6 | Re-test CV, GitHub, Gmail (after HTTPS) |
| 7 | Stop AWS instance to save cost |

---

## Do **not** choose / use

| Option | Reason |
|--------|--------|
| China mainland regions | ICP / verification complexity |
| WordPress / LNMP / BT-Panel AMIs | Wrong stack |
| Separate RDS for MVP | SQLite on disk is enough |
| Second ECS instance | One box runs web + api |

---

## Related docs

- [`aws-ec2-deploy.md`](./aws-ec2-deploy.md) — AWS proof-of-deploy (archive)  
- [`jobpilot_prd.md`](../jobpilot_prd.md) — mandatory Alibaba ECS  
- [`JobPilot-System-Design.md`](./JobPilot-System-Design.md) — topology  
- [`currently-working-feature.md`](../currently-working-feature.md) — active work
