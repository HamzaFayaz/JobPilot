# Evidence Card — Mini Overview

Frozen Phase 1 test snapshot for **JobPilot** using root `README.md` and `build_project_evidence()`.

| Item | Value |
| --- | --- |
| Repository | `JobPilot/JobPilot` |
| Model | `qwen3.7-plus` |
| Temperature | `0.1` |
| README chars | 13603 |
| Evidence claims | 8 |

## Portfolio mini overview

```text
JobPilot is an AI-driven job application copilot featuring a multi-tier agentic architecture. It combines a FastAPI and LangGraph cloud orchestrator with a distributed desktop browser automation client to search LinkedIn, score roles, and draft applications with human-in-the-loop approval.
```

## Project summary

**Name:** JobPilot

**Description:**

```text
JobPilot is a multi-tier agentic system designed to automate and streamline technical job applications.
It utilizes a cloud orchestrator built with FastAPI and LangGraph to coordinate a distributed desktop Search Helper.
The desktop client executes browser automation in the user's real Chrome session via Kimi WebBridge to capture LinkedIn job posts.
Retrieved listings are processed through a deterministic pipeline that normalizes, deduplicates, and routes them to per-job application sub-agents.
These sub-agents leverage Qwen Cloud to score, summarize, and draft application materials for human approval.
```

**Repo skills:** Python, FastAPI, LangGraph, React, TypeScript, SQLite, Docker, Qwen Cloud, Browser Automation, Agentic Systems, Pydantic, JWT, GitHub Actions

## Evidence card

### Purpose

To automate technical job search and application drafting using agentic systems, balancing bulk automation speed with manual accuracy through human-in-the-loop approval before sending applications.

### Tech stack

- React 19
- TypeScript
- Vite
- Tailwind CSS
- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic v2
- SQLite
- LangGraph
- Qwen Cloud
- Kimi WebBridge
- PyInstaller
- PySide6
- Docker Compose
- Nginx
- GitHub Actions
- Alibaba ECS

### Architecture

- Three-tier distributed architecture: Tier 1 is the Alibaba ECS cloud hosting React UI, FastAPI, LangGraph orchestrator, and SQLite. Tier 2 is the desktop Search Helper (Windows .exe) running a worker poll loop and agent loop. Tier 3 is the browser layer using Kimi WebBridge to interact with the user's logged-in Chrome session. The backend uses a deterministic LangGraph parent graph with search, prefilter, and parallel application subgraphs.

### Key features

- Multi-user accounts with JWT httpOnly sessions
- Profile intelligence via CV upload and GitHub OAuth
- LinkedIn Posts search via real Chrome session
- LangGraph orchestration with parallel application subgraphs
- Code-only listing prefilter for normalization and deduplication
- Per-job application agents for scoring and drafting
- Worker task queue with device pairing and heartbeat
- Fernet encrypted storage for CV text and tokens

### Role relevance

- Demonstrates extensive experience in Python, FastAPI, and agent systems, specifically in building distributed LangGraph orchestrations, integrating LLMs (Qwen) for structured judgment, and designing resilient HTTP-based worker task queues for browser automation.

### Grounded evidence

| # | README section | Claim |
| ---: | --- | --- |
| 1 | Overview | JobPilot is a multi-tier agentic system using LangGraph orchestration and distributed browser automation. |
| 2 | Overview | The cloud orchestrator coordinates a desktop Search Helper that browses LinkedIn Posts in the user's real Chrome session. |
| 3 | Overview | Listings pass through normalization and deduplication before flowing into per-job application sub-agents that score, summarize, and package opportunities. |
| 4 | Agentic architecture | The system uses a deterministic LangGraph pipeline with a parent graph, search subgraph, prefilter, and parallel application subgraphs. |
| 5 | Tech stack | The backend is built with Python 3.11+, FastAPI, and Pydantic v2, utilizing SQLite for the database. |
| 6 | Tech stack | The frontend is built with React 19, TypeScript, Vite, and Tailwind CSS. |
| 7 | Overview | Browser automation is handled by Kimi WebBridge and a Qwen ReAct loop in the user's logged-in Chrome. |
| 8 | Hackathon | The project was submitted to the Qwen Cloud Global AI Hackathon (Track 4: Autopilot Agent). |

### Supported metrics

- _(none stated in README)_

### Limitations / unknowns

- Candidate's specific individual role or team size is not specified
- Exact scale, user base, or conversion metrics are not provided
- Specific hackathon placement or awards are not mentioned
- Production traffic or load handling metrics are unknown

## Input files (verbatim)

| File | Contents |
| --- | --- |
| [`input-system-prompt.txt`](./input-system-prompt.txt) | LLM system prompt |
| [`input-cv-summary.txt`](./input-cv-summary.txt) | CV context passed to the model |
| [`input-user-message.txt`](./input-user-message.txt) | Full user message sent to the model |
| [`input-readme.md`](./input-readme.md) | Exact README used as evidence source |

## Output file (verbatim JSON)

See [`output.json`](./output.json) for the complete structured `build_project_evidence()` result.

## Manifest

See [`manifest.json`](./manifest.json) for file index and model config.
