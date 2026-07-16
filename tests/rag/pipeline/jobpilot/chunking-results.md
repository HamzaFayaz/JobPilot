# Chunking results — jobpilot

## Summary
- Parents: 23
- Boundary units: 59
- Child chunks: 23
- README chars: 13603

## Parents
- `JobPilot` — 145 tokens
- `JobPilot > Overview` — 251 tokens
- `JobPilot > The problem` — 92 tokens
- `JobPilot > Features` — 239 tokens
- `JobPilot > Agentic architecture` — 53 tokens
- `JobPilot > Agentic architecture > Three-tier deployment` — 184 tokens
- `JobPilot > Agentic architecture > Parent graph pipeline` — 187 tokens
- `JobPilot > Agentic architecture > End-to-end search flow` — 174 tokens
- `JobPilot > Agentic architecture > Data flow` — 127 tokens
- `JobPilot > Engineering highlights` — 391 tokens
- `JobPilot > Tech stack` — 182 tokens
- `JobPilot > Quick start > Prerequisites` — 43 tokens
- `JobPilot > Quick start > 1. Clone and configure` — 33 tokens
- `JobPilot > Quick start > 2. Setup` — 40 tokens
- `JobPilot > Quick start > 3. Run locally` — 141 tokens
- `JobPilot > Project structure` — 197 tokens
- `JobPilot > API surface > User & profile` — 118 tokens
- `JobPilot > API surface > Search & jobs` — 81 tokens
- `JobPilot > API surface > Search Helper (worker)` — 98 tokens
- `JobPilot > Design & UI` — 91 tokens
- `JobPilot > Documentation` — 163 tokens
- `JobPilot > Principles` — 111 tokens
- `JobPilot > Hackathon` — 118 tokens

## Child chunks
### JobPilot (chunk 0, 145 tokens, readme_section)
**AI job application copilot — LangGraph orchestration, distributed browser automation, and human-in-the-loop control.**  [![Live Demo](https://img.shields.io/badge/demo-Alibaba%20ECS-43.98.197.132-blue?style=flat-square)](http://43.98.197.132) [![Stack](https://img.shields.io/badge/stack-React%20%7C%20FastAPI%20%7C%20LangGraph-blue?style=flat-square)](#tech-stack) [![LLM](https://img.shields.io/b...

### JobPilot > Overview (chunk 1, 251 tokens, readme_section)
JobPilot is a **multi-tier agentic system** built for developers who want high-quality job applications without manual grind on every listing. Users build a profile from their CV and GitHub, start a search from the web app, and a **cloud orchestrator** coordinates a **desktop Search Helper** that browses LinkedIn Posts in the user's real Chrome session. Listings return to the server, pass through ...

### JobPilot > The problem (chunk 2, 92 tokens, readme_section)
Technical job search at scale breaks down in two directions:  - **Manual:** reading every post, tailoring every CV, writing every email — accurate but exhausting - **Bulk automation:** fast but low conversion, platform risk, no user control  JobPilot delivers the middle path: **agentic search, scoring, and drafting with human approval before anything is sent.**  ---

### JobPilot > Features (chunk 3, 239 tokens, readme_section)
- **Multi-user accounts** — signup, login, JWT httpOnly sessions, per-user data isolation - **Profile intelligence** — CV upload (`.docx`), Qwen skill extraction, target roles, GitHub OAuth repo import - **LinkedIn Posts search** — Search Helper captures hiring posts via Kimi WebBridge in real Chrome - **LangGraph orchestration** — parent graph with search subgraph, prefilter, and parallel applica...

### JobPilot > Agentic architecture (chunk 4, 53 tokens, readme_section)
JobPilot uses a **deterministic LangGraph pipeline** — code routes between subgraphs. Qwen is invoked where structured judgment is required: the browser ReAct agent on the user's PC and `enrich_job` on the server.

### JobPilot > Agentic architecture > Three-tier deployment (chunk 5, 184 tokens, readme_section)
```mermaid flowchart TB   subgraph T1 ["Tier 1 — Alibaba ECS (cloud)"]     UI["React SPA"]     API["FastAPI"]     LG["LangGraph orchestrator"]     DB[("SQLite")]     UI --> API --> LG --> DB   end    subgraph T2 ["Tier 2 — Search Helper (user PC)"]     WH["worker/main.py poll loop"]     BC["browser_client + agent_loop"]     WH --> BC   end    subgraph T3 ["Tier 3 — Kimi WebBridge"]     WB["HTTP :1...

### JobPilot > Agentic architecture > Parent graph pipeline (chunk 6, 187 tokens, readme_section)
```mermaid flowchart LR   A["init_run"] --> B["search_subgraph"]   B --> C["prefilter"]   C --> D{"matched_jobs?"}   D -->|yes| E["Send × N\napplication_subgraph"]   D -->|no| F["persist"]   E --> F ```  | Node | Layer | Responsibility | |------|-------|----------------| | `init_run` | Parent | Load profile snapshot, validate gates, set `search_runs.status` | | `search_subgraph` | Subgraph | Enque...

### JobPilot > Agentic architecture > End-to-end search flow (chunk 7, 174 tokens, readme_section)
```mermaid sequenceDiagram   participant U as User browser   participant ECS as FastAPI + LangGraph   participant H as Search Helper   participant C as Chrome (WebBridge)    U->>ECS: POST /api/search   ECS->>ECS: enqueue worker_tasks row   ECS-->>U: { runId, pending }   H->>ECS: GET /api/worker/tasks/next   ECS-->>H: browser_search task   H->>C: Kimi WebBridge + Qwen ReAct   C-->>H: RawJobListing[...

### JobPilot > Agentic architecture > Data flow (chunk 8, 127 tokens, readme_section)
```text Search Helper   POST /api/worker/tasks/{taskId}/result   { listings: RawJobListing[], warnings: string[] }        ↓ worker_tasks.result_json        ↓ search_subgraph.wait_for_listings()        ↓ prefilter → matched_jobs        ↓ application_subgraph (per job) → job_packages        ↓ search_runs (jobs_ready_count, status) ```  Posts without a public URL receive an internal `linkedin-post://...

### JobPilot > Engineering highlights (chunk 9, 391 tokens, readme_section)
| Decision | Rationale | |----------|-----------| | **LangGraph parent + subgraphs** | Clean separation: search wait loop, per-job scoring, browser ReAct | | **Worker task queue (HTTP)** | Resilient polling; simple to debug; no WebSocket infra | | **Kimi WebBridge** | Real Chrome session, residential IP, existing LinkedIn login | | **Targeted Qwen usage** | Profile extraction, browser agent, `enri...

### JobPilot > Tech stack (chunk 10, 182 tokens, readme_section)
| Layer | Technology | |-------|------------| | **Frontend** | React 19, TypeScript, Vite, Tailwind CSS, Heroicons | | **Design** | Stitch UI exports, `design-system/MASTER.md`, responsive AppShell | | **Backend** | Python 3.11+, FastAPI, Uvicorn, Pydantic v2 | | **Database** | SQLite on ECS (schema ready for RDS migration) | | **Agents** | LangGraph — parent graph + compiled subgraphs | | **LLM**...

### JobPilot > Quick start > Prerequisites (chunk 11, 43 tokens, readme_section)
- Python 3.11+ - Node.js 18+ - [Qwen Cloud API key](https://home.qwencloud.com) (`DASHSCOPE_API_KEY`) - Kimi WebBridge extension + daemon - GitHub OAuth app (for repo import)

### JobPilot > Quick start > 1. Clone and configure (chunk 12, 33 tokens, readme_section)
```bash git clone <repo-url> cd JobPilot cp .env.example .env # Set DASHSCOPE_API_KEY, JWT_SECRET, DATA_ENCRYPTION_KEY, GITHUB_* ```

### JobPilot > Quick start > 2. Setup (chunk 13, 40 tokens, readme_section)
**Windows:**  ```bat setup.cmd ```  **Manual:**  ```bash python -m venv .venv .venv\Scripts\activate pip install -r requirements.txt cd frontend && npm install ```

### JobPilot > Quick start > 3. Run locally (chunk 14, 141 tokens, readme_section)
**Windows:**  ```bat dev.cmd ```  **Manual:**  ```bash # Terminal 1 — API uvicorn backend.app.main:app --reload --port 8000  # Terminal 2 — UI cd frontend && npm run dev  # Terminal 3 — Search Helper (after pairing in UI) cd worker && python main.py ```  | Service | URL | |---------|-----| | Frontend | http://localhost:5173 | | API | http://localhost:8000 | | Health | http://localhost:8000/health ...

### JobPilot > Project structure (chunk 15, 197 tokens, readme_section)
```text JobPilot/ ├── backend/app/ │   ├── graph/              # LangGraph orchestrator + subgraphs │   ├── routes/             # FastAPI routers (auth, search, worker, jobs) │   ├── services/           # worker_store, search_store, listing_prefilter, profile_llm │   └── models/             # Pydantic contracts (browser, search, worker) ├── frontend/src/           # React SPA (Welcome, Profile, Se...

### JobPilot > API surface > User & profile (chunk 16, 118 tokens, readme_section)
| Method | Path | Description | |--------|------|-------------| | `POST` | `/api/auth/signup` | Create account | | `POST` | `/api/auth/login` | Login (JWT cookie) | | `GET` | `/api/profile` | Profile + search preferences | | `PUT` | `/api/profile` | Update roles, projects, search prefs | | `POST` | `/api/profile/cv` | Upload `.docx`, extract skills (Qwen) | | `GET` | `/auth/github` | GitHub OAuth ...

### JobPilot > API surface > Search & jobs (chunk 17, 81 tokens, readme_section)
| Method | Path | Description | |--------|------|-------------| | `POST` | `/api/search` | Start search run → background graph | | `GET` | `/api/runs/latest/status` | Latest run for current user | | `GET` | `/api/runs/{runId}/status` | Poll run progress | | `GET` | `/api/jobs?runId=` | List scored `job_packages` for a run |

### JobPilot > API surface > Search Helper (worker) (chunk 18, 98 tokens, readme_section)
| Method | Path | Description | |--------|------|-------------| | `POST` | `/api/worker/pair` | Issue `WORKER_TOKEN` | | `POST` | `/api/worker/heartbeat` | Liveness + browser health | | `GET` | `/api/worker/tasks/next` | Claim next `browser_search` task | | `POST` | `/api/worker/tasks/{id}/result` | Post `RawJobListing[]` | | `POST` | `/api/worker/tasks/{id}/fail` | Report task failure |  ---

### JobPilot > Design & UI (chunk 19, 91 tokens, readme_section)
- **Stitch** desktop reference screens adapted to responsive web (`frontend/UI Design/`) - **Design tokens:** [`.stitch/DESIGN.md`](./.stitch/DESIGN.md), [`design-system/MASTER.md`](./design-system/MASTER.md) - **App shell:** sidebar desktop, drawer mobile, profile gate before search - **Core screens:** Welcome (`/`), Profile (`/profile`), Search (`/search`)  ---

### JobPilot > Documentation (chunk 20, 163 tokens, readme_section)
| Document | Purpose | |----------|---------| | [`System Design/JobPilot-System-Design.md`](./System%20Design/JobPilot-System-Design.md) | System topology and state shapes | | [`System Design/jobpilot-agent-build-guide.md`](./System%20Design/jobpilot-agent-build-guide.md) | Agent architecture and API contracts | | [`System Design/kimi-webbridge-provider.md`](./System%20Design/kimi-webbridge-provid...

### JobPilot > Principles (chunk 21, 111 tokens, readme_section)
1. **Human-in-the-loop** — user approves before any application is sent 2. **Real browser sessions** — LinkedIn automation uses the user's Chrome, not datacenter bots 3. **Server-side secrets** — Qwen keys stay on ECS; never exposed in the frontend bundle 4. **Per-user isolation** — profiles, runs, tokens, and job packages scoped by `user_id` 5. **Production patterns** — deterministic graph routin...

### JobPilot > Hackathon (chunk 22, 118 tokens, readme_section)
Submitted to the **Qwen Cloud Global AI Hackathon** (Track 4: Autopilot Agent).  - **Alibaba Cloud deployment** — ECS, Docker, public URL - **Qwen Cloud APIs** — CV skills, README summarization, browser ReAct agent, per-job scoring - **Agentic system** — LangGraph multi-subgraph orchestration with distributed Search Helper  ---  <p align="center">   <strong>JobPilot</strong> — agentic job search w...
