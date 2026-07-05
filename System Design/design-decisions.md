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

**Out of scope for MVP:** `user_id` was deferred for hackathon single-user demo.

**Update (2026-07-02):** Multi-user auth is now **in progress** — add `user_id` to `RunState`, `JobPackage`, `AppliedJob`, `profiles`, and `oauth_tokens` when login/signup ships. See [`currently-working-feature.md`](../currently-working-feature.md).

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

> **Status (2026-07-02): CANCELLED for MVP.** LinkedIn and Indeed use in-platform apply flows, not email send. Gmail UI removed from onboarding; backend routes may remain but are unused. Skip HTTPS/Google OAuth for deploy.

**Issue:** The main design lists "Gmail OAuth start + callback" but not where tokens live, how refresh works, or what happens when a token expires mid-run. This was the #1 likely demo failure when email send was in scope.

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

## 4. Browser provider abstraction (swappable layer)

**Issue:** Search must use the user's real Chrome and IP. **Browser-Use was shipped as a spike** but caused profile-copy and session issues. **Kimi WebBridge** is now the v1 provider (real Chrome via extension + daemon).

**Decision (2026-07-05):**

| Layer | Responsibility | Changes when swapping provider |
|-------|----------------|-------------------------------|
| Tier 1 — ECS | `POST /search`, poll, DB, LangGraph | **Never** |
| Tier 2 — Local worker | Pull tasks, post results | Worker env only |
| Tier 3 — `BrowserProvider` | `search_listings()`, `health()` | New file under `providers/` + factory branch |

- **v1:** `BROWSER_PROVIDER=webbridge` — HTTP to `127.0.0.1:10086`, Kimi extension + daemon, Qwen ReAct loop in worker.
- **Deprecated:** `BROWSER_PROVIDER=browser-use` — separate Chrome profile; remove after WebBridge E2E passes.
- LangGraph and routes call **`get_browser_provider()` only** — never import `browser_use` or WebBridge directly on ECS.

**Primary guide:** [`kimi-webbridge-provider.md`](./kimi-webbridge-provider.md)  
**Full spec:** [`browser-provider-abstraction.md`](./browser-provider-abstraction.md)

**Chrome UX (WebBridge):** User keeps JobPilot and LinkedIn in their **normal Chrome**. Install Kimi WebBridge extension + daemon once; no second profile required.

**Deployment (locked):** Alibaba ECS for API + LangGraph; **JobPilot Search Helper** on user PC for browser automation. Rejected: full client-side SPA, full local backend. See [`jobpilot-agent-build-guide.md`](./jobpilot-agent-build-guide.md).

---

## Summary

| # | Decision | Action before first node |
|---|----------|--------------------------|
| 1 | `run_id` in state + DB | Add to `RunState`, `search_runs` table, all run-scoped APIs |
| 2 | Async `/search` + poll | Change API contract; background graph execution |
| 3 | Gmail OAuth lifecycle | Token table, refresh-on-send, explicit error codes |
| 4 | Browser provider abstraction | `BrowserProvider` protocol + worker; **Kimi WebBridge v1** (replaces Browser-Use) |
| 5 | Deployment + Search Helper | ECS + Helper install once; mock search for judges — [build guide](./jobpilot-agent-build-guide.md) |
