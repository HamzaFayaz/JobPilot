# Alibaba Cloud — ECS Free Trial (JobPilot)

**Status:** **Hackathon submission target** — activate when account/trial is available.  
**Active cloud:** AWS EC2 until then → [`aws-ec2-deploy.md`](./aws-ec2-deploy.md)  
**Last updated:** 2026-06-29  
**Hackathon requirement:** Agent backend must run on Alibaba Cloud ECS ([`jobpilot_prd.md`](../jobpilot_prd.md))

---

## Deploy strategy

| Phase | Platform | Notes |
|-------|----------|-------|
| **Now** | Local + **AWS EC2** | Build and validate all features |
| **Submit** | **Alibaba ECS** | Same single-instance layout; swap host |

If trial is blocked (risk control on duplicate accounts), continue on AWS and migrate to Alibaba before the deadline.

---

## Confirmed trial selection (when account works)

| Setting | Your choice |
|---------|-------------|
| **Region** | **Singapore** |
| **Instance** | **ecs.e-c1m2.xlarge** — **4 vCPU · 8 GiB · Economy Type e** |
| **Disk** | **ESSD Entry · 100 GiB** |
| **OS** | **Ubuntu 22.04 64-bit** |
| **Pre-installed apps** | **None** (no WordPress, LNMP, Docker, BT-Panel) |
| **Quantity** | **1 instance** |
| **Trial credit** | USD 90 · ~**769 hours** at ~$0.117/hr · **$0.25/hr cap** |

**~16-day sprint cost:** 384 hrs × $0.117 ≈ **~$45** — fits within trial credit.

---

## Database & storage (no separate RDS)

| Data | Where |
|------|--------|
| Profiles, OAuth, search runs (MVP) | **SQLite** `data/jobpilot.db` on ECS **100 GiB disk** |
| CV `.docx` files | `data/uploads/` on same disk |
| **RDS** | Optional post-MVP — **not needed** for hackathon |
| **OSS** | Optional later for CV cloud storage |

Leftover credits *can* pay for RDS, but **not required** — SQLite on the ECS disk matches current code.

---

## Do **not** choose

| Option | Reason |
|--------|--------|
| **China (Shenzhen / Shanghai)** | Identity verification + ICP rules |
| **WordPress / LNMP / BT-Panel** | Wrong stack (PHP/MySQL panel) |
| **Separate RDS** | Unnecessary for 16-day MVP |
| **2nd ECS instance** | Frontend + backend share one box via nginx |

---

## Architecture (one ECS)

```
User's laptop                    Alibaba ECS (Singapore)
┌─────────────────────┐         ┌──────────────────────────┐
│ Chrome + Browser    │◄───────►│ Nginx → frontend + /api  │
│ Worker (local)      │  HTTPS  │ FastAPI + LangGraph      │
└─────────────────────┘         │ data/jobpilot.db         │
                                │ data/uploads/            │
                                └──────────────────────────┘
```

---

## Region `.env` (Singapore)

```env
ALIBABA_REGION=ap-southeast-1
ALIBABA_ECS_ZONE=ap-southeast-1a

# OSS (optional later)
ALIBABA_OSS_ENDPOINT=oss-ap-southeast-1.aliyuncs.com
ALIBABA_OSS_BUCKET=jobpilot-cv-sg

FRONTEND_URL=https://your-alibaba-domain
GOOGLE_REDIRECT_URI=https://your-alibaba-domain/auth/google/callback
GITHUB_REDIRECT_URI=https://your-alibaba-domain/auth/github/callback

QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

---

## Activation checklist

1. [ ] ECS: **Singapore · ecs.e-c1m2.xlarge · Ubuntu 22.04 · 100 GiB · no pre-installers**
2. [ ] Security group: **22** (your IP), **80/443**
3. [ ] Elastic IP for stable OAuth URLs
4. [ ] Same setup as AWS: Python 3.11, nginx, clone JobPilot, `pip install`, `npm run build`
5. [ ] Copy `data/` from AWS if migrating
6. [ ] Update OAuth redirect URIs to Alibaba public URL
7. [ ] Enable **Gmail API** in Google Cloud (same project as local)

---

## Account issues (risk control)

- Second accounts often hit **risk control** — use **one primary account** or hackathon organizer credits.
- Support: Console → **Work order / ticket** (not chat only).
- **Do not block development** — use local + AWS EC2 until resolved.

---

## Related docs

- [`aws-ec2-deploy.md`](./aws-ec2-deploy.md) — **active** cloud deploy guide
- [`jobpilot_prd.md`](../jobpilot_prd.md) — mandatory Alibaba ECS for submission
- [`JobPilot-System-Design.md`](./JobPilot-System-Design.md) — topology
