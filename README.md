# JobPilot

**Your AI job application copilot — search, tailor, and apply with human approval before anything is sent.**

[![Status: Under Active Development](https://img.shields.io/badge/status-under%20active%20development-amber?style=flat-square)](./progress.md)
[![Stack: React + FastAPI](https://img.shields.io/badge/stack-React%20%7C%20FastAPI%20%7C%20LangGraph-blue?style=flat-square)](#tech-stack)
[![LLM: Qwen Cloud](https://img.shields.io/badge/LLM-Qwen%20Cloud-purple?style=flat-square)](https://home.qwencloud.com)

---

## Overview

JobPilot is a browser-based assistant for developers who want **high-quality job applications at scale**. It connects to your profile (CV, GitHub, skills), searches job platforms, scores listings against your background, drafts tailored applications, and sends email — **only after you approve each step**.

> **This repository is under active construction.** Core onboarding and profile APIs are live locally; search agents, HITL job flows, and production deploy are in progress. See [Current status](#current-status) below.

---

## The problem

A serious job search means scanning multiple platforms, reading every JD, tailoring your CV, and writing unique emails — often 10–20 times per day. Generic bulk applications convert poorly; fully manual tailoring does not scale.

**JobPilot is the middle path:** AI handles search, scoring, and drafting; you stay in control with a human-in-the-loop (HITL) gate before anything is sent.

---

## Current status

| Area | Status |
|------|--------|
| Design system & UI reference | ✅ Complete |
| Welcome, Profile, Search screens | ✅ Complete |
| FastAPI profile API + SQLite | ✅ Complete |
| CV upload → LLM skill extraction | ✅ Complete |
| GitHub OAuth + repo import | ✅ Complete |
| Multi-user login / signup | 🚧 Next |
| LangGraph search agents | 🚧 Planned |
| Job scoring & CV rewrite per JD | 🚧 Planned |
| HITL approve → platform apply | 🚧 Planned |
| Production deploy (Alibaba ECS) | ✅ Live — http://43.98.197.132 |

**Live progress:** [`progress.md`](./progress.md) · **Active work:** [`currently-working-feature.md`](./currently-working-feature.md)

---

## Full product vision (when complete)

Everything JobPilot will do at launch:

### Profile & onboarding
- **CV upload** (`.docx`) with automatic skill extraction via profile LLM
- **Target roles** — user-defined roles used per search run
- **GitHub import** — OAuth connect, select repos, README → project cards + merged skills
- **Gmail connect** — OAuth for sending approved applications
- **Profile gate** — unlock Search when CV, skills, and projects meet minimum requirements
- **Settings** — read-only skills, editable project cards

### Search & agents
- **Multi-platform search** — LinkedIn, Indeed (browser worker in user's real Chrome session)
- **LangGraph orchestration** — parent graph + per-job sub-agents
- **Job scoring** — match score per listing against skills, CV, and projects
- **CV optimization** — recommend project swaps per JD (word-count aware)
- **Real-time run progress** — polling `/search` runs with status updates

### Human-in-the-loop (HITL)
- **Approve before send** — review cover letter and email for every application
- **Job detail screen** — listing, score, proposed CV changes, draft email
- **One-click reject** — skip jobs that are not a fit
- **Applications memory** — track what was applied to avoid duplicates

### Integrations
- **Gmail API** — send approved emails with CV attachment
- **GitHub API** — repo list, README fetch, project summarization
- **Qwen Cloud (Dashscope)** — scoring, CV rewrite, email drafting, profile extraction
- **Browser-Use** — control user's Chrome for platform search (no headless detection)

### Platform & ops (post-MVP)
- CV storage on Alibaba Cloud OSS (optional; files on instance disk for MVP)
- Managed database (RDS) — optional; SQLite on instance disk for hackathon
- Multi-user auth (out of hackathon MVP scope)

**Deploy guides:** [`System Design/aws-ec2-deploy.md`](System%20Design/aws-ec2-deploy.md) (active) · [`System Design/alibaba-cloud-trial.md`](System%20Design/alibaba-cloud-trial.md) (hackathon submit)

**Live demo:** http://43.98.197.132

---

## How it works (architecture)

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  React UI   │────▶│  FastAPI     │────▶│  SQLite / DB    │
│  :5173      │     │  :8000       │     │  profiles, OAuth│
└─────────────┘     └──────┬───────┘     └─────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         Qwen LLM    Gmail API    GitHub API
              │
              ▼
    LangGraph agents + Browser-Use (planned)
```

**Principle:** Agent logic runs server-side; browser automation uses the user's real logged-in Chrome session on a residential IP.

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Database | SQLite (local MVP) → RDS (production) |
| LLM | Qwen Cloud via OpenAI-compatible Dashscope API |
| Agents | LangGraph (planned) |
| Browser | Browser-Use (planned) |
| Auth | Google OAuth (Gmail), GitHub OAuth |

---

## Quick start

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Qwen Cloud API key](https://home.qwencloud.com)
- Google & GitHub OAuth apps (optional; for Gmail/GitHub features)

### 1. Clone and configure

```bash
git clone <repo-url>
cd JobPilot
cp .env.example .env
# Edit .env — add DASHSCOPE_API_KEY, GOOGLE_*, GITHUB_*
```

### 2. Setup (first time)

**Windows:**
```bat
setup.cmd
```

**Manual:**
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cd frontend && npm install
```

### 3. Run locally

**Windows (recommended):**
```bat
dev.cmd
```

**Manual (two terminals):**
```bash
# Terminal 1 — API
uvicorn backend.app.main:app --reload --port 8000

# Terminal 2 — UI
cd frontend && npm run dev
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| Health | http://localhost:8000/health |

---

## Project structure

```
JobPilot/
├── backend/           # FastAPI app (profile, OAuth, GitHub import)
├── frontend/          # Vite React SPA
├── config/            # LLM defaults (llm.yaml)
├── data/              # SQLite DB + CV uploads (gitignored)
├── System Design/     # Architecture & design decisions
├── .agent/plans/      # Build plans for /build command
├── dev.cmd            # Start backend + frontend (Windows)
├── setup.cmd          # First-time setup (Windows)
├── progress.md        # Project progress tracker
└── jobpilot_prd.md    # Product requirements
```

---

## API surface (current)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/profile` | Full profile + OAuth flags |
| `PUT` | `/api/profile` | Update roles & projects |
| `POST` | `/api/profile/cv` | Upload `.docx`, extract skills |
| `GET` | `/auth/google` | Start Gmail OAuth |
| `DELETE` | `/api/auth/google` | Disconnect Gmail |
| `GET` | `/auth/github` | Start GitHub OAuth |
| `GET` | `/api/github/repos` | List user repos |
| `POST` | `/api/github/import` | Import READMEs → projects |

Search, job packages, and send endpoints are **planned** — see [`jobpilot_prd.md`](./jobpilot_prd.md).

---

## Documentation

| Document | Purpose |
|----------|---------|
| [`jobpilot_prd.md`](./jobpilot_prd.md) | Product requirements & MVP scope |
| [`progress.md`](./progress.md) | Phase checklist & status |
| [`currently-working-feature.md`](./currently-working-feature.md) | What we are building now |
| [`System Design/`](./System%20Design/) | System design & decisions |
| [`frontend/progress.md`](./frontend/progress.md) | Frontend screen checklist |

---

## Key principles

1. **HITL first** — nothing is sent without explicit user approval
2. **Privacy** — profile data is used only to personalize search and drafts
3. **Real browser** — job platform automation uses the user's Chrome, not headless bots
4. **Developer-centric** — built for engineers with GitHub projects and technical CVs

---

## Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| 0 | Design & UI reference | ✅ |
| 1 | Welcome, Profile, Search UI | ✅ |
| 2 | Profile API, OAuth, LLM extraction | ✅ |
| 3 | `POST /search`, LangGraph agents | 🚧 Next |
| 4 | Job results, HITL, Gmail send | 🚧 |
| 5 | Applications tracking UI | 🚧 |
| 6 | Production deploy (http://43.98.197.132) | `[x]` Alibaba ECS |

---

## Contributing

This project is in active development for the **Qwen Cloud Global AI Hackathon** (Track 4: Autopilot Agent). Contribution guidelines will be added as the codebase stabilizes.

---

## License

License TBD. All rights reserved during active development.

---

<p align="center">
  <strong>JobPilot</strong> — built with human approval at every step.
  <br />
  <sub>Under active development · Last updated June 2026</sub>
</p>
