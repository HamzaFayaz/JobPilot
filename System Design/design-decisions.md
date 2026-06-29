# JobPilot — Design Decisions (Lock Before Coding)

**Related:** [JobPilot-System-Design.md](./JobPilot-System-Design.md)

These three items change the API contract or are the most likely demo-breakers. Resolve them before writing the first LangGraph node or FastAPI route.

---

## 1. `run_id` in run state and API correlation

**Issue:** `RunState` in the main design has `role`, `platform`, `profile`, `listings`, `packages`, `errors` — but no `run_id`. Without it you cannot tie a LangGraph execution back to the `/search` response or support multiple concurrent searches.

**Decision (MVP):**

- Every search trigger creates a UUID `run_id` at the API layer before the graph starts.
- Persist `run_id` in LangGraph `RunState` and in the DB (`search_runs` table or equivalent).
- All run-scoped reads filter by `run_id`: `GET /runs/{run_id}/status`, `GET /jobs?run_id=...`.

```python
class RunState(TypedDict):
    run_id: str              # UUID, set at graph start
    role: str
    platform: str
    profile: dict
    listings: list[JobListing]
    packages: list[JobPackage]
    errors: list[str]
    status: str              # "pending" | "running" | "completed" | "failed"
```

**Out of scope for MVP:** `user_id`. Single-user hackathon — add when multi-user auth lands.

---

## 2. Async search contract (do not block `POST /search`)

**Issue:** Search + browser extraction + per-job sub-agent batch can take 30–90 seconds. A synchronous `POST /search` that waits for all sub-agents will hang the HTTP request and timeout in any real deployment.

**Decision (MVP):**

| Endpoint | Behavior |
|----------|----------|
| `POST /search` | Create `run_id`, enqueue/start graph in background, return immediately `{ run_id, status: "pending" }` |
| `GET /runs/{run_id}/status` | Poll: `{ status, progress?, jobs_ready_count?, error? }` |
| `GET /jobs?run_id={run_id}` | List `JobPackage`s as they complete (client polls until `status === "completed"`) |

**Optional later:** WebSocket or SSE push for live job cards — not required for hackathon MVP if the UI polls every 2–3s.

**Updated sequence:**

```
Client                          API                         Orchestrator
  |-- POST /search ------------>| create run_id, start bg   |
  |<-- { run_id, pending } -----|                           |
  |                             |-------- run graph ------->|
  |-- GET /runs/{id}/status --->|                           |
  |<-- { running, 3/8 } --------|                           |
  |-- GET /jobs?run_id=... ---->|                           |
  |<-- [JobPackage, ...] -------|                           |
  |     (repeat poll)           |                           |
  |-- GET /runs/{id}/status --->|                           |
  |<-- { completed } -----------|                           |
```

**Implementation note:** FastAPI `BackgroundTasks`, `asyncio.create_task`, or a small job queue (e.g. in-process for MVP). The graph writes `JobPackage` rows as each sub-agent finishes so partial results appear before the run completes.

---

## 3. Gmail OAuth token lifecycle

**Issue:** The main design lists "Gmail OAuth start + callback" but not where tokens live, how refresh works, or what happens when a token expires mid-run. This is the #1 likely demo failure.

**Decision (MVP):**

### Setup flow

1. `GET /auth/google` — redirect to Google OAuth consent (scopes: `gmail.send`, `userinfo.email`).
2. `GET /auth/google/callback` — exchange code for tokens; store refresh token + access token.
3. `POST /profile` — separate from Gmail; CV + skills/projects only.

### Token storage

| Field | Where |
|-------|--------|
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | `.env` / ECS secrets (never in DB) |
| Refresh token | SQLite `oauth_tokens` table (MVP) or encrypted file at `data/gmail_token.json` |
| Access token | In-memory cache with expiry; refresh on demand |

Single-user MVP: one row in `oauth_tokens`. Multi-user later: keyed by `user_id`.

### Refresh strategy

- Before every `gmail.users.messages.send`, check access token expiry.
- If expired or within 5 minutes of expiry, refresh using stored refresh token.
- Update stored access token + expiry after refresh.

### Failure handling (Dispatch Agent)

| Condition | API response | User-facing message |
|-----------|--------------|---------------------|
| No token on file | `401` + `{ code: "gmail_not_connected" }` | "Connect Gmail before sending" |
| Refresh token revoked / invalid | `401` + `{ code: "gmail_auth_expired" }` | "Gmail access expired — reconnect in Settings" |
| Send API error (quota, etc.) | `502` + `{ code: "gmail_send_failed", detail }` | Show provider error; `JobPackage.status` stays `ready` (allow retry) |
| Send succeeds | `200` + persist `AppliedJob` | "Application sent" |

### Mid-run expiry

- Token refresh happens at send time, not at search start. A 30–90s search run does not require a valid Gmail token.
- If refresh fails when user clicks Send, block send and surface `gmail_auth_expired` — do not partially mark the job as applied.

### Pre-demo checklist

- [ ] OAuth callback URL matches Google Console exactly (`http://localhost:8000/auth/google/callback` for local).
- [ ] Refresh token persisted and survives server restart.
- [ ] Test send after revoking and re-connecting Gmail.

---

## Summary

| # | Decision | Action before first node |
|---|----------|--------------------------|
| 1 | `run_id` in state + DB | Add to `RunState`, `search_runs` table, all run-scoped APIs |
| 2 | Async `/search` + poll | Change API contract; background graph execution |
| 3 | Gmail OAuth lifecycle | Token table, refresh-on-send, explicit error codes |
