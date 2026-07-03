# Phase A — Step 1: Contracts and Scaffolding

**Status:** Current working step  
**Goal:** Define the search/application data contracts, persistence layer, and stub API surface before building graph logic or browser execution.

---

## What we will code in Step 1

### 1. Search domain models

- `backend/app/models/search.py`
  - `RunStatus`
  - `SearchRequest`
  - `SearchRunStatusResponse`
  - `JobPackageResponse`

### 2. Database schema updates

- Update `backend/app/db.py`
  - extend `search_runs` for real run tracking
  - extend `job_packages` for scored job output
  - extend `job_applications` so it can act as the dedupe source later

### 3. Search persistence layer

- `backend/app/services/search_store.py`
  - create search run
  - update run status
  - insert job package
  - read run status / jobs for polling

### 4. Stub search APIs

- `backend/app/routes/search.py`
  - `POST /api/search`
  - create run row
  - return `{ runId, status }`

- `backend/app/routes/runs.py`
  - `GET /api/runs/{runId}/status`
  - return stub progress from DB

- `backend/app/routes/jobs.py`
  - `GET /api/jobs?runId=`
  - return stored packages, even if currently empty

### 5. Route registration

- Update `backend/app/main.py`
  - register the new search, runs, and jobs routers

---

## What Step 1 does not include

- No LangGraph files yet
- No `search_subgraph` yet
- No `application_subgraph` yet
- No worker tables yet
- No worker pairing flow yet
- No Browser-Use integration yet
- No Qwen `enrich_job` yet

---

## Expected output after Step 1

- Repo has stable search models
- DB can store search runs, job packages, and applied job records cleanly
- Frontend or manual API calls can start a search run and poll status
- The graph can be added on top of these contracts in the next step

---

## Done when

- Models import cleanly
- DB initializes with the new tables/columns
- `POST /api/search` returns a real `runId`
- `GET /api/runs/{runId}/status` works
- `GET /api/jobs?runId=` works
- No real browser or LangGraph dependency is required yet
