# Phase A — Step 1: Contracts First

**Purpose:** Lock the shared inputs/outputs before building graph logic.

---

## Scope

Step 1 is split into three small parts:

1. **Step 1A — Database**
2. **Step 1B — Models and states**
3. **Step 1C — Stub APIs**

---

## Step 1A — Database `[x]`

Completed:

- expanded `search_runs`
- expanded `job_packages`
- expanded `job_applications`
- updated [`docs/database-schema.md`](docs/database-schema.md)

Deferred for later:

- `worker_devices`
- `worker_tasks`

---

## Step 1B — Models and states `[x]`

Completed:

- `backend/app/models/browser.py`
  - `Platform`
  - `BrowserHealth`
  - `RawJobListing`
  - `SearchListingsRequest`
  - `SearchListingsResult`

- `backend/app/models/search.py`
  - `RunStatus`
  - `JobPackageStatus`
  - `CvDecision`
  - `SearchStartResponse`
  - `SearchRunStatusResponse`
  - `JobListingResponse`
  - `JobPackageResponse`

- `backend/app/graph/state.py`
  - `RunState`
  - `ProfileState`
  - `JobListing`
  - `JobPackageState`

- `backend/app/graph/subgraphs/search/state.py`
  - `SearchState`

- `backend/app/graph/subgraphs/application/state.py`
  - `ApplicationState`

---

## Step 1C — Stub APIs `[x]`

Completed:

- `backend/app/routes/search.py`
  - `POST /api/search`
  - reads saved `searchRole` / `searchPlatform` from profile DB
  - creates a `search_runs` row and returns `{ runId, status }`

- `backend/app/routes/runs.py`
  - `GET /api/runs/{runId}/status`
  - returns `status`, `jobsReadyCount`, and `error`

- `backend/app/routes/jobs.py`
  - `GET /api/jobs?runId=`
  - returns the current `job_packages` list for one run

- `backend/app/main.py`
  - registers the new search, runs, and jobs routers

### Frontend ↔ backend connections added

1. **Start search**
   - frontend → `POST /api/search`
   - backend reads saved profile search preferences from DB, creates a run row, and returns `runId`

2. **Poll run status**
   - frontend → `GET /api/runs/{runId}/status`
   - backend reads `search_runs`

3. **Fetch jobs**
   - frontend → `GET /api/jobs?runId=`
   - backend reads `job_packages`

---

## Why this step exists

- everyone agrees on the data contracts first
- graph nodes can be built on top of stable state shapes
- APIs can be wired without guessing field names later

---

## Done when

- DB schema is ready
- models and graph states exist
- stub polling/search APIs exist
- no real subgraph logic is required yet
