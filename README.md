# JobPilot

**JobPilot | Track 4 - Autopilot Agent**

AI job application copilot: LangGraph orchestration, distributed browser automation, and human-in-the-loop control.

### Required judge links (hackathon)

- **Qwen Cloud API (code):** [`backend/app/config.py`](./backend/app/config.py)  
  Base URL: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`  
  Models: [`config/llm.yaml`](./config/llm.yaml)

- **Alibaba Cloud deploy proof (code):**  
  - ECS notes: [`System Design/alibaba-cloud-trial.md`](./System%20Design/alibaba-cloud-trial.md)  
  - API image: [`deploy/Dockerfile.api`](./deploy/Dockerfile.api)  
  - Deploy workflow: [`.github/workflows/deploy.yml`](./.github/workflows/deploy.yml) (SSH/rsync + Docker to Alibaba ECS)  
  - Recent runs: [github.com/HamzaFayaz/JobPilot/actions](https://github.com/HamzaFayaz/JobPilot/actions)

- **Live demo:** [http://47.237.150.6](http://47.237.150.6)  
- **Track:** Track 4 - Autopilot Agent  
- **License:** [MIT](./LICENSE)

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Alibaba%20ECS-blue?style=flat-square)](http://47.237.150.6)
[![Qwen API](https://img.shields.io/badge/Qwen%20API-config.py-purple?style=flat-square)](./backend/app/config.py)
[![Alibaba Proof](https://img.shields.io/badge/Alibaba%20Proof-ECS%20deploy-orange?style=flat-square)](./System%20Design/alibaba-cloud-trial.md)
[![Deploy Workflow](https://img.shields.io/badge/Deploy-Alibaba%20ECS%20Actions-2088FF?style=flat-square)](./.github/workflows/deploy.yml)
[![Hackathon](https://img.shields.io/badge/Qwen%20Hackathon-Track%204%20Autopilot-success?style=flat-square)](#hackathon)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](./LICENSE)
[![Stack](https://img.shields.io/badge/stack-React%20%7C%20FastAPI%20%7C%20LangGraph-blue?style=flat-square)](#tech-stack)
[![Search](https://img.shields.io/badge/search-LinkedIn%20Posts-0A66C2?style=flat-square)](#features)

---

## Overview

JobPilot is a **multi-tier agentic system** built for developers who want high-quality job applications without manual grind on every listing. Users build a profile from their CV and GitHub, start a search from the web app, and a **cloud orchestrator** coordinates a **desktop Search Helper** that browses LinkedIn Posts in the user's real Chrome session. Listings return to the server, pass through normalization and deduplication, and flow into **per-job application sub-agents** that score, summarize, and package each opportunity.

The platform is optimized for **LinkedIn Posts** - the format where hiring managers and recruiters post roles directly in the feed.

| Tier | Components |
|------|------------|
| **Cloud (Alibaba ECS)** | React UI · FastAPI · LangGraph · SQLite · Qwen Cloud (DashScope) |
| **Desktop** | JobPilot Search Helper - Windows `.exe`, task queue client |
| **Browser** | Kimi WebBridge in the user's logged-in Chrome |

**Hackathon:** [Qwen Cloud Global AI Hackathon](https://qwencloud-hackathon.devpost.com/) - **Track 4: Autopilot Agent** (product build complete; packaging for submission).

---

## The problem

Technical job search at scale breaks down in two directions:

- **Manual:** reading every post, tailoring every CV, writing every email - accurate but exhausting
- **Bulk automation:** fast but low conversion, platform risk, no user control

JobPilot delivers the middle path: **agentic search, scoring, and drafting with human approval before anything is sent.**

---

## Features

- **Multi-user accounts** - signup, login, JWT httpOnly sessions, per-user data isolation
- **Profile intelligence** - CV upload (`.docx`), Qwen skill extraction, target roles, GitHub OAuth repo import
- **LinkedIn Posts search** - Search Helper captures hiring posts via Kimi WebBridge in real Chrome
- **LangGraph orchestration** - parent graph with search subgraph, prefilter, and parallel application subgraphs
- **Listing prefilter** - normalize, dedupe, drop already-applied jobs (no LLM cost)
- **Per-job application agents** - structured Qwen scoring, match summary, CV swap plans, draft email
- **Suggested CV** - user-approved, layout-preserving `.docx` drafts (never overwrites the master CV)
- **Search Helper downloads** - Windows `.exe` + supported CV template from Settings / Profile
- **Worker task queue** - device pairing, heartbeat, async `browser_search` tasks over HTTP
- **Run polling API** - `POST /api/search`, status polling, `job_packages` results per run
- **Encrypted storage** - Fernet for CV text and OAuth tokens; all tables scoped by `user_id`
- **Cloud deploy** - Docker Compose, Nginx, GitHub Actions on Alibaba ECS

---

## Agentic architecture

JobPilot uses a **deterministic LangGraph pipeline** - code routes between subgraphs. **Qwen Cloud** runs on the ECS backend (browser ReAct, scoring, suggested CV). The Search Helper executes **Kimi WebBridge** tools in the user's Chrome.

### Three-tier deployment

```mermaid
flowchart TB
 subgraph T1 ["Tier 1 - Alibaba ECS (cloud)"]
 UI["React SPA"]
 API["FastAPI"]
 LG["LangGraph orchestrator"]
 DB[("SQLite")]
 UI --> API --> LG --> DB
 end

 Qwen["Qwen Cloud / DashScope\ncompatible-mode/v1"]

 subgraph T2 ["Tier 2 - Search Helper (user PC)"]
 WH["Worker poll loop"]
 WH --> WBExec["WebBridge tool executor"]
 end

 subgraph T3 ["Tier 3 - Kimi WebBridge"]
 WB["HTTP :10086"]
 Chrome["User Chrome - LinkedIn Posts"]
 WB --> Chrome
 end

 API --> Qwen
 LG --> Qwen
 API <-->|"HTTPS task queue"| WH
 WBExec --> WB
 Chrome -->|"raw listings JSON"| WH
 WH -->|"POST /api/worker/tasks/{id}/result"| API
```

LinkedIn requires the user's home IP and logged-in session - ECS + Qwen orchestrate; the Search Helper + WebBridge execute in real Chrome.

### Parent graph pipeline

Current LangGraph parent run (code: [`orchestrator.py`](./backend/app/graph/orchestrator.py)). Suggested CV is **not** inside this graph - it runs later on explicit user approve.

```mermaid
flowchart TB
  START([START]) --> init["init_run"]
  init -->|failed| END1([END])
  init -->|ok| search["search_subgraph"]
  search --> pref["prefilter"]
  pref -->|no matched jobs| persist["persist"]
  pref -->|matched jobs| fan["fan_out: Send x N"]
  fan --> app1["application_subgraph\njob 1"]
  fan --> app2["application_subgraph\njob 2"]
  fan --> appN["application_subgraph\njob N"]
  app1 --> persist
  app2 --> persist
  appN --> persist
  persist --> END2([END])

  HITL["HITL later: approve swaps"] -.->|user action| tailor["tailor_cv\noutside parent graph"]
```

| Node | Layer | Responsibility |
|------|-------|----------------|
| `init_run` | Parent | Load profile snapshot, validate gates, set run status |
| `search_subgraph` | Subgraph | Enqueue Helper task → wait for listings (Qwen ReAct + WebBridge) |
| `prefilter` | Parent | Normalize → dedupe → drop already-applied |
| `fan_out` / `Send` | Parent | Parallel per-job `application_subgraph` |
| `application_subgraph` | Subgraph | Enrich → classify fit → package `job_packages` |
| `persist` | Parent | Finalize run status and counts |
| `tailor_cv` | API / HITL | After Applications approve - not a parent-graph node |

### Subgraph detail

One diagram per **compiled subgraph** (not every leaf helper). Enough for judges to see depth without noise.

#### `search_subgraph`

LangGraph nodes are enqueue → wait. While waiting, the cloud **Qwen ReAct** agent + **Search Helper / WebBridge** collect LinkedIn Posts and POST the result.

```mermaid
flowchart LR
  enq["enqueue_browser_task"] --> wait["wait_for_listings"]
  wait --> out["raw_listings"]
```

**Outside those nodes (same task):** ECS Qwen ReAct ↔ Helper WebBridge → `POST /api/worker/tasks/{id}/result`  
**Contract:** one task out, one result back over HTTP. ECS never imports browser SDKs.

#### `application_subgraph` (per job, parallel)

```mermaid
flowchart LR
  e["enrich_job\nQwen score + swap plan"] --> c["classify_fit"]
  c --> p["package_out\njob_packages row"]
```

Code: [`subgraphs/search/`](./backend/app/graph/subgraphs/search/) · [`subgraphs/application/`](./backend/app/graph/subgraphs/application/)

Posts without a public URL receive an internal `linkedin-post://{hash}` identifier for deduplication and storage - used server-side only, not shown as a user-facing link.

---

## Technical depth / Engineering

Scannable map of the autopilot stack (Track 4): what each piece does and why it matters.

### Agents and components

| Piece | What it does | Why it matters |
|-------|----------------|----------------|
| **Parent LangGraph** | Routes `init_run` → search → prefilter → parallel application subgraphs → persist | Deterministic orchestration; code owns control flow |
| **Search subgraph** | Enqueues a worker task and waits for listings | Separates "order" (cloud) from "delivery" (desktop browser) |
| **Cloud browser agent (Qwen ReAct)** | On ECS, decides WebBridge tool calls for LinkedIn Posts | Qwen Cloud drives search; tools run on the user PC |
| **Search Helper (`worker/`)** | Paired desktop app; polls tasks; executes WebBridge actions | Real Chrome + home IP; LinkedIn session never uploaded to ECS |
| **Kimi WebBridge** | Local bridge into the user's Chrome | Browser tools without shipping cookies to the cloud |
| **Prefilter (code)** | Normalize, dedupe, drop already-applied | Cheap gate before LLM scoring |
| **Application subgraph** | Per-job `enrich_job` (score, summary, keep/swap plan) | Parallel Qwen judgment per listing |
| **Suggested CV (`tailor_cv`)** | User-approved slot swaps → layout-preserving `.docx` | HITL; analysis never writes the master CV |
| **Profile / evidence LLMs** | CV skills, GitHub overview, embeddings + rerank | Grounds scoring in the user's real projects |

### Search Helper and session boundary

LinkedIn automation needs the user's logged-in Chrome and residential network. Running that browser on Alibaba ECS would use a datacenter IP and would not see the user's session. JobPilot keeps **orchestration and Qwen keys on ECS**, and keeps **browser execution on the paired Search Helper**.

- Helper code: [`worker/`](./worker/)  
- WebBridge provider notes: [`System Design/kimi-webbridge-provider.md`](./System%20Design/kimi-webbridge-provider.md)  
- Pairing and task queue: [`backend/app/services/worker_store.py`](./backend/app/services/worker_store.py)

The Helper talks to ECS over a device-paired HTTP task API. Review the `worker/` package for how tasks are fetched and how WebBridge is invoked locally.

### Engineering decisions

| Decision | Rationale |
|----------|-----------|
| **LangGraph parent + subgraphs** | Clean separation: search wait loop, per-job scoring, browser ReAct |
| **Worker task queue (HTTP)** | Resilient polling; simple to debug; no WebSocket infra |
| **Kimi WebBridge on user PC** | Real Chrome session and home IP for LinkedIn Posts |
| **Targeted Qwen usage** | Profile, browser agent, `enrich_job`, `tailor_cv`, embeddings - no LLM supervisor router |
| **Code-only prefilter** | Normalize, URL/email dedupe, drop applied before fan-out |
| **Fernet + per-user scope** | Encrypted secrets; every row keyed by `user_id` |
| **Docker + GitHub Actions** | Repeatable Alibaba ECS deploy ([`deploy.yml`](./.github/workflows/deploy.yml)) |

### Key modules

| Path | Role |
|------|------|
| [`backend/app/graph/orchestrator.py`](./backend/app/graph/orchestrator.py) | Parent LangGraph - nodes, edges, `Send` fan-out |
| [`backend/app/graph/subgraphs/search/`](./backend/app/graph/subgraphs/search/) | Enqueue + wait for worker listings |
| [`backend/app/graph/subgraphs/application/`](./backend/app/graph/subgraphs/application/) | Per-job enrich, score gate, package output |
| [`backend/app/services/browser_agent/`](./backend/app/services/browser_agent/) | Cloud Qwen ReAct loop (ECS) |
| [`backend/app/services/listing_prefilter.py`](./backend/app/services/listing_prefilter.py) | Normalize, dedupe, drop applied |
| [`backend/app/services/worker_store.py`](./backend/app/services/worker_store.py) | Device pairing, task queue, result polling |
| [`backend/app/services/tailor_cv_llm.py`](./backend/app/services/tailor_cv_llm.py) | Suggested CV generation after user approve |
| [`worker/`](./worker/) | Search Helper - WebBridge executor + UI |
| [`worker/api_client.py`](./worker/api_client.py) | Search Helper ↔ ECS HTTP client |

---

## Tech stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS, Heroicons |
| **Design** | Stitch UI exports, `design-system/MASTER.md`, responsive AppShell |
| **Backend** | Python 3.11+, FastAPI, Uvicorn, Pydantic v2 |
| **Database** | SQLite on ECS (schema ready for RDS migration) |
| **Agents** | LangGraph - parent graph + compiled subgraphs |
| **LLM** | Qwen Cloud (Dashscope OpenAI-compatible API) |
| **Browser automation** | Kimi WebBridge (HTTP daemon + Chrome extension) |
| **Desktop worker** | PyInstaller `.exe`, PySide6 settings UI |
| **Auth** | Email/password + JWT httpOnly cookie; GitHub OAuth |
| **Deploy** | Docker Compose, Nginx, GitHub Actions → Alibaba ECS |

---

## Quick start

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Qwen Cloud API key](https://home.qwencloud.com) (`DASHSCOPE_API_KEY`)
- Kimi WebBridge extension + daemon
- GitHub OAuth app (for repo import)

### 1. Clone and configure

```bash
git clone <repo-url>
cd JobPilot
cp .env.example .env
# Set DASHSCOPE_API_KEY, JWT_SECRET, DATA_ENCRYPTION_KEY, GITHUB_*
```

### 2. Setup

**Windows:**
```bat
setup.cmd
```

**Manual:**
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cd frontend && npm install
```

### 3. Run locally

**Windows:**
```bat
dev.cmd
```

**Manual:**
```bash
# Terminal 1 - API
uvicorn backend.app.main:app --reload --port 8000

# Terminal 2 - UI
cd frontend && npm run dev

# Terminal 3 - Search Helper (after pairing in UI)
cd worker && python main.py
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| Health | http://localhost:8000/health |

Search Helper: [`worker/README.md`](./worker/README.md) · WebBridge: [`System Design/kimi-webbridge-provider.md`](./System%20Design/kimi-webbridge-provider.md)

---

## Project structure

```text
JobPilot/
├── backend/app/
│ ├── graph/ # LangGraph orchestrator + subgraphs
│ ├── routes/ # FastAPI routers (auth, search, worker, jobs)
│ ├── services/ # worker_store, search_store, listing_prefilter, profile_llm
│ └── models/ # Pydantic contracts (browser, search, worker)
├── frontend/src/ # React SPA (Welcome, Profile, Search)
├── worker/ # JobPilot Search Helper (WebBridge + Qwen agent loop)
├── config/llm.yaml # Model routing defaults
├── design-system/ # Design tokens (Stitch overrides)
├── System Design/ # Architecture specs and ADRs
├── deploy/ # Docker, Nginx, ECS bootstrap
└── tests/ # Backend + worker unit tests
```

---

## API surface

### User & profile

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/signup` | Create account |
| `POST` | `/api/auth/login` | Login (JWT cookie) |
| `GET` | `/api/profile` | Profile + search preferences |
| `PUT` | `/api/profile` | Update roles, projects, search prefs |
| `POST` | `/api/profile/cv` | Upload `.docx`, extract skills (Qwen) |
| `GET` | `/auth/github` | GitHub OAuth start |
| `POST` | `/api/github/import` | Import READMEs → project cards |

### Search & jobs

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/search` | Start search run → background graph |
| `GET` | `/api/runs/latest/status` | Latest run for current user |
| `GET` | `/api/runs/{runId}/status` | Poll run progress |
| `GET` | `/api/jobs?runId=` | List scored `job_packages` for a run |

### Search Helper (worker)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/worker/pair` | Issue `WORKER_TOKEN` |
| `POST` | `/api/worker/heartbeat` | Liveness + browser health |
| `GET` | `/api/worker/tasks/next` | Claim next `browser_search` task |
| `POST` | `/api/worker/tasks/{id}/result` | Post `RawJobListing[]` |
| `POST` | `/api/worker/tasks/{id}/fail` | Report task failure |

---

## Design & UI

- **Stitch** desktop reference screens adapted to responsive web (`frontend/UI Design/`)
- **Design tokens:** [`.stitch/DESIGN.md`](./.stitch/DESIGN.md), [`design-system/MASTER.md`](./design-system/MASTER.md)
- **App shell:** sidebar desktop, drawer mobile, profile gate before search
- **Core screens:** Welcome (`/`), Profile (`/profile`), Search (`/search`), Applications (`/applications`), Settings (`/settings`)

---

## Documentation

| Document | Purpose |
|----------|---------|
| [`System Design/JobPilot-System-Design.md`](./System%20Design/JobPilot-System-Design.md) | System topology and state shapes |
| [`System Design/jobpilot-agent-build-guide.md`](./System%20Design/jobpilot-agent-build-guide.md) | Agent architecture and API contracts |
| [`System Design/kimi-webbridge-provider.md`](./System%20Design/kimi-webbridge-provider.md) | WebBridge integration |
| [`System Design/browser-provider-abstraction.md`](./System%20Design/browser-provider-abstraction.md) | Browser provider protocol |
| [`docs/database-schema.md`](./docs/database-schema.md) | SQLite schema reference |

---

## Principles

1. **Human-in-the-loop** - user approves before any application is sent
2. **Real browser sessions** - LinkedIn automation uses the user's Chrome, not datacenter bots
3. **Server-side secrets** - Qwen keys stay on ECS; never exposed in the frontend bundle
4. **Per-user isolation** - profiles, runs, tokens, and job packages scoped by `user_id`
5. **Production patterns** - deterministic graph routing, typed contracts, tested worker protocol

---

## Hackathon

**Title:** JobPilot 
**Track:** **Track 4 - Autopilot Agent** 
**Event:** [Qwen Cloud Global AI Hackathon](https://qwencloud-hackathon.devpost.com/) 
**License:** [MIT](./LICENSE) 
**Status:** Product build complete - packaging for Devpost submission (July 2026)

JobPilot is an end-to-end autopilot-style agent: cloud LangGraph orchestration, Qwen Cloud judgment calls, and a distributed desktop Search Helper (Kimi WebBridge) that browses LinkedIn Posts in the user's real Chrome session - with human approval before any suggested CV draft is finalized.

### Submission proof links (judges)

| Requirement | Link |
|-------------|------|
| **Track** | Track 4 - Autopilot Agent |
| **Qwen Cloud API** (OpenAI-compatible base URL) | [`backend/app/config.py`](./backend/app/config.py) - `qwen_base_url = https://dashscope-intl.aliyuncs.com/compatible-mode/v1` |
| **Qwen models by call site** | [`config/llm.yaml`](./config/llm.yaml) |
| **Alibaba Cloud deploy proof** | [`alibaba-cloud-trial.md`](./System%20Design/alibaba-cloud-trial.md) · [`deploy/Dockerfile.api`](./deploy/Dockerfile.api) · [`deploy.yml`](./.github/workflows/deploy.yml) · [Actions runs](https://github.com/HamzaFayaz/JobPilot/actions) |
| **Architecture diagram** | [Agentic architecture](#agentic-architecture) (Mermaid: ECS · Qwen Cloud · Search Helper · WebBridge) |
| **Technical depth** | [Technical depth / Engineering](#technical-depth--engineering) |
| **Live demo** | [http://47.237.150.6](http://47.237.150.6) |
| **Open-source license** | [`LICENSE`](./LICENSE) (MIT) |

### What ships for the hackathon

| Requirement / theme | JobPilot delivery |
|---------------------|-------------------|
| Agent on Alibaba Cloud | FastAPI + LangGraph on **Alibaba ECS** (Singapore) |
| Qwen Cloud APIs | DashScope `compatible-mode/v1` - profile skills, listing rewrite, cloud browser ReAct, `enrich_job`, `tailor_cv`, embeddings/rerank |
| Autopilot agent loop | Parent graph → search subgraph → prefilter → parallel application subgraphs |
| Human-in-the-loop | Applications inbox; suggested CV (`tailor_cv`) only after user-approved swaps |
| Live demo | [http://47.237.150.6](http://47.237.150.6) |

**Out of hackathon scope (intentional):** Gmail/send apply, Indeed / LinkedIn Jobs boards, Windows code-signing cert (SmartScreen guidance in Settings).

### Next (packaging)

1. **Demo video** (&lt; 3 min) - title → ECS IP → app → Helper connect → search → analysis → suggested CV 
2. **Blog / social post** - optional Blog Post prize 
3. Devpost: same proof links + architecture image export of the Mermaid above 

Contact: [hamza.fayaz.ai@gmail.com](mailto:hamza.fayaz.ai@gmail.com)

---

<p align="center">
 <strong>JobPilot</strong> - agentic job search with production architecture patterns.
 <br />
 <sub>Qwen Cloud Global AI Hackathon · Track 4 · July 2026</sub>
</p>
