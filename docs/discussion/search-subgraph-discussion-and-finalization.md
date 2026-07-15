# Search Subgraph — Discussion and Finalization

> **Browser provider update (2026-07-05):** **Kimi WebBridge** replaces Browser-Use for the Search Helper. ECS subgraph and worker HTTP protocol are unchanged. See [`System Design/kimi-webbridge-provider.md`](../../System%20Design/kimi-webbridge-provider.md). Historical Browser-Use references below are kept for context.

## Question

if you check we plan to use someting like Your intuition is right (user view)
When you click Start search, you want:

"Find jobs on LinkedIn for this role."

That is one job. You should not think of it as two products.

Why the design splits it (engineer view)

```text
┌─────────────────────────────────────┐
│  ECS (cloud)                        │
│  search_subgraph                    │
│  • create task                      │
│  • wait for results                 │
│  • clean URLs, remove applied jobs  │
└──────────────┬──────────────────────┘
               │  task queue / API
               ▼
┌─────────────────────────────────────┐
│  Your PC (Search Helper)            │
│  browser agent                      │
│  • open Chrome                      │
│  • click, scroll, read LinkedIn     │
│  • return raw job list              │
└─────────────────────────────────────┘
```

| Piece | Where | Job |
|-------|-------|-----|
| search_subgraph | Cloud | Orchestration: "run search", wait, clean data |
| browser agent | Your PC | Actually control Chrome on LinkedIn |
They are not the same because Chrome cannot run on ECS. LinkedIn needs your logged-in session and your home IP. So the "hands on keyboard" part must live on your machine.

Analogy  for the seach subagnet 

---

## Answer

Your intuition is **exactly right**.

From the user’s perspective it is **one action**: “Start search on LinkedIn for this role.”

From the system’s perspective it is **two jobs in two places**, because LinkedIn cannot be driven from the cloud server.

---

### User view (what you feel)

> “JobPilot, find Python jobs on LinkedIn.”

One button. One wait. One results list.

---

### Engineer view (why it’s split)

| Piece | Where | What it does |
|-------|--------|----------------|
| **`search_subgraph`** | ECS (cloud) | Boss / coordinator |
| **Browser agent** | Your PC (Search Helper) | Worker with hands on Chrome |

**`search_subgraph` does not open LinkedIn.** It:

1. Creates a task (“search LinkedIn for Python Developer”)
2. Waits for your PC to finish
3. Cleans the raw list (normalize URLs, drop already-applied jobs)
4. Passes clean `listings` back to the main graph

**Browser agent on your PC** does the messy part:

- Open Chrome (your logged-in session)
- Search, scroll, click, read listings
- Return raw JSON to the cloud

---

### Analogy

Think of **ordering food delivery**:

| Role | JobPilot equivalent |
|------|---------------------|
| **You** | User clicks “Start search” |
| **Restaurant app (cloud)** | `search_subgraph` on ECS — takes order, tracks status, cleans up the bill |
| **Delivery driver (your street)** | Search Helper + browser agent — actually goes to the store and brings food back |

The app doesn’t drive to the store. It **coordinates**. The driver **executes**.

LinkedIn is the “store” — it only trusts **your** Chrome, **your** cookies, **your** home IP. ECS is in Singapore/datacenter; LinkedIn would block or distrust that. So the driver (Search Helper) **must** run on your PC.

---

### One search, two layers

```text
User: "Start search"
        │
        ▼
┌─────────────────────────────────────┐
│  search_subgraph (cloud)            │
│  "I need listings for role X"       │
│  enqueue → wait → clean             │
└──────────────┬──────────────────────┘
               │ worker task
               ▼
┌─────────────────────────────────────┐
│  browser agent (your PC)            │
│  Opens Chrome, searches, raw jobs   │
└──────────────┬──────────────────────┘
               │ raw listings JSON
               ▼
┌─────────────────────────────────────┐
│  search_subgraph (cloud)            │
│  normalize, drop applied            │
│  → listings in RunState             │
└─────────────────────────────────────┘
```

---

### Why this matches our build order

When we **build search subgraph next**, we implement the **cloud half**:

- `enqueue_browser_task`
- `wait_for_listings`
- `normalize_listings`
- `drop_applied`

The **browser agent** comes with **Search Helper** (`worker/`) — separate piece, talks to ECS via task queue API.

So: **one product for the user, two components for engineers** — and that split is intentional, not over-engineering.

---

## Stopping conditions — Question

What should be the possible **stop conditions** for the job search step?

When the user clicks Start search, the browser agent scrolls LinkedIn and collects listings. **When should it stop?** What conditions should end the search — success, failure, timeout, empty results, user cancel, etc.?

We need to lock this before implementing `wait_for_listings` and the browser agent task prompt.

---

## Stopping conditions — Answer

Stopping conditions split into **two layers**. Do not mix them up.

| Layer | Where | Question it answers |
|-------|--------|---------------------|
| **Browser search stop** | Search Helper (your PC) | “When do I stop scrolling LinkedIn and send results?” |
| **Search subgraph stop** | ECS (`wait_for_listings`) | “When do I stop waiting for the Helper and move on?” |

The user sees one search. Engineers need both stop rules.

---

### Layer 1 — Browser agent stop conditions (Search Helper)

These are set in the **task payload** (`SearchListingsRequest`) and the **browser agent prompt**. Locked defaults from our contracts:

| Stop condition | Type | Default / rule | Result |
|----------------|------|----------------|--------|
| **`max_listings` reached** | Success | `8` (`SearchListingsRequest.max_listings`) | Stop scrolling; return list (may be &lt; 8 if page runs out) |
| **`max_pages` reached** | Success | `3` (`BROWSER_SEARCH_MAX_PAGES`) | Stop after N result pages even if listings &lt; max |
| **No more results on page** | Success | Agent detects end of list / empty next page | Stop early with whatever was collected (0 to N listings) |
| **Agent task finished normally** | Success | Browser-Use returns structured JSON | POST result to ECS |
| **CAPTCHA / login wall / blocked** | Partial / fail | Warning in `SearchListingsResult.warnings` | Return what we have + warning, or fail task if zero listings |
| **Chrome crash / provider error** | Fail | Helper catches exception | POST `tasks/{id}/fail` with error code |
| **User closes Helper or revokes pairing** | Fail | Heartbeat stops / task cancelled | Fail or timeout on ECS side |

**MVP rule:** browser agent stops on **whichever comes first**:

1. collected `max_listings` jobs  
2. scanned `max_pages` pages  
3. no more jobs visible on the platform  

That is the primary **success stop**. Early stop with fewer jobs is still success.

---

### Layer 2 — Search subgraph stop conditions (`wait_for_listings`)

The cloud side does **not** control scrolling. It waits for the worker task to finish. Stop when:

| Stop condition | Type | Default / rule | Run outcome |
|----------------|------|----------------|-------------|
| **Worker posts result** | Success | `POST /api/worker/tasks/{id}/result` with `RawJobListing[]` | Continue to `normalize_listings` → `drop_applied` |
| **Worker posts fail** | Fail | `POST /api/worker/tasks/{id}/fail` | Run → `failed`; error on `search_runs` |
| **Wait timeout** | Fail | `120s` (`wait_for_worker_listings` in browser-provider spec) | Run → `failed`; code `search_timeout` (504) |
| **Helper offline at enqueue** | Fail | No paired device / heartbeat stale | Fail before or at wait; “Search Helper not connected” |
| **Zero listings after normalize** | Success (empty) | Valid result, list is `[]` | Graph continues; prefilter gets nothing; user sees “no jobs found” — **not** a crash |
| **Parse error on result JSON** | Fail | Invalid `RawJobListing[]` | Run → `failed`; code `search_parse_failed` |

**MVP rule:** `wait_for_listings` stops waiting on **result**, **fail**, or **timeout** — nothing else.

---

### Layer 3 — Not browser stop (downstream caps)

These stop **how many jobs get scored**, not how many get scraped:

| Condition | Where | Default |
|-----------|--------|---------|
| Skill prefilter drops non-matches | `prefilter` node | Free keyword overlap |
| **Cap N jobs into application subgraph** | `prefilter` | **N = 8** (same as scrape cap for MVP) |
| Score below threshold | `application_subgraph` | Skip packaging if score &lt; 60 |

Scrape cap and score cap can both be 8 for hackathon — simple and predictable cost.

---

### Recommended locked defaults (MVP)

**Superseded — see [Locked — stopping conditions (MVP)](#locked--stopping-conditions-mvp) below.**

---

### Out of scope for first search subgraph slice

| Condition | Defer? | Why |
|-----------|--------|-----|
| User clicks “Cancel search” mid-run | Later | Needs cancel API + task revocation |
| Per-run cost cap beyond N jobs | Later | N=8 is enough for hackathon |
| Retry same task automatically | Later | User starts a new search |
| Stop on duplicate URL mid-scrape | No — handled in `normalize_listings` / `drop_applied`, not stop scroll |

---

### Open decision (discuss before coding)

1. **Empty list:** treat as success or soft-fail? **Recommend success** — platform may genuinely have no matches.  
2. **Partial with warning (CAPTCHA):** return partial listings + warning, or fail entire run? **Recommend partial** if ≥1 listing; fail if 0.  
3. **Timeout 120s:** enough for LinkedIn scroll with age filter? **Start with 120s**; tune after first real Helper test.

---

## Locked — stopping conditions (MVP)

**Status:** Locked (2026-07-04). Implement these four for the first search subgraph + browser agent slice.

Two layers — do not mix them:

| Layer | Locked stops |
|-------|----------------|
| **Browser agent (Search Helper)** | What to collect while scrolling |
| **ECS (`wait_for_listings`)** | When the cloud task finishes or fails |

---

### The four locked stops

| # | Stop | Layer | Rule | Why |
|---|------|--------|------|-----|
| **1** | **Max jobs** | Browser agent | Stop when **`max_listings = 8`** fresh jobs collected | Primary success cap — bounds scrape time and downstream LLM cost |
| **2** | **Job age (~1 week)** | Browser agent | Only collect jobs **posted within the last 7 days**; stop scrolling when no newer jobs remain | Fresh listings only; natural end when results are too old |
| **3** | **Worker result OR fail** | ECS `wait_for_listings` | Stop waiting when Helper **`POST …/result`** or **`POST …/fail`** | Cloud must know the PC task finished — not optional |
| **4** | **Wait timeout** | ECS `wait_for_listings` | Stop waiting after **`120s`** → run `failed`, code `search_timeout` | Prevents hung run if Helper crashes or disconnects |

---

### Browser agent — locked stop rule (wording for prompt)

```text
Stop scrolling and return results when EITHER:
  • you have collected 8 jobs posted within the last 7 days, OR
  • there are no more jobs within the last 7 days to collect
```

Fewer than 8 jobs is still **success** if nothing fresh remains.

---

### ECS — locked stop rule (wording for `wait_for_listings`)

```text
Stop waiting when:
  • worker posts result (RawJobListing[]), OR
  • worker posts fail, OR
  • 120 seconds elapse (timeout)
```

---

### Deferred — `max_pages` (not MVP)

| Item | Status | When to add |
|------|--------|-------------|
| **`max_pages` (e.g. 3)** | **Not in MVP** | Add **only if** real Helper / LinkedIn testing shows the agent **misbehaves** — e.g. keeps scrolling forever without respecting max jobs or the 1-week filter |

Reason to skip for now: redundant with max jobs + age filter; adds prompt complexity; extra pages can increase Browser-Use agent steps and token cost. Revisit after first end-to-end test if runaway scrolling appears.

If added later: treat as a **safety cap**, not a primary stop — still keep max jobs + 1-week filter as the main rules.

---

### Also locked (supporting, not extra “stops”)

| Case | Treatment |
|------|-----------|
| Empty list `[]` after normalize | **Success** — user sees “no jobs found”, run continues |
| Helper offline at enqueue | **Fail** before wait — “Search Helper not connected” |
| Invalid result JSON | **Fail** — `search_parse_failed` |

---

### Summary

**Stop scrolling (Helper):** max 8 jobs within 1 week, or no fresher jobs left.  
**Stop waiting (ECS):** result, fail, or 120s timeout.  
**Stop scoring (later nodes):** prefilter + N cap + score threshold — separate from search stop.

**`max_pages`:** deferred — add only if testing shows agent misbehaviour.

---

## Search subgraph — two parts, connection, LLM

**Status:** Locked summary (2026-07-05).

### Two parts

| Part | Where | Job |
|------|--------|-----|
| **Search subgraph** | ECS (cloud) | Send task → wait → normalize → drop applied |
| **Browser agent** | User PC (Search Helper) | Open Chrome, scroll LinkedIn, return **raw** listings JSON |

User sees one “Start search”. Engineers split it because Chrome must run on the user’s machine (logged-in session + home IP).

---

### How they connect (not page-by-page)

**One task out → worker browses everything on the PC → one result back.**

- ECS does **not** tell the worker “go to page 2” after each page.
- Scrolling, age filter (1 week), and max jobs (8) happen **inside** Browser-Use on the PC.
- Worker **`POST`s one batch** of `RawJobListing[]` when done.
- ECS **`wait_for_listings`** waits for that single result, fail, or 120s timeout.

Worker job = **fetch raw data only**. Real pipeline work (normalize, filter applied, score, package) = **ECS after** raw data arrives.

---

### LLM — who has it

| Part | LLM? | Purpose |
|------|------|---------|
| **Search subgraph (ECS)** | **No** | Code, DB, task queue, URL cleanup |
| **Browser agent (Helper / PC)** | **Yes** | Browser-Use ReAct loop (scroll, click, extract) |
| **Application subgraph (ECS, later)** | **Yes** | `enrich_job` — score, CV hint, package (after search) |

- ECS search steps: **no Qwen**.
- Worker: **Qwen (or configured model) in worker `.env`** — separate from ECS `config/llm.yaml`.
- Browser LLM = many steps per search; application LLM = once per surviving job (capped).

---

### One-line summary

**ECS search subgraph** = no LLM, orchestrates and cleans data.  
**PC browser agent** = has LLM, returns raw listings once.  
**ECS application subgraph** = has LLM, runs after search.

---

## Locked — Browser-Use ReAct, tools, and task prompt

**Status:** Locked (2026-07-05).

Browser-Use ships its **own ReAct loop** and **built-in browser tools** (navigate, click, scroll, read page, finish). JobPilot does **not** implement per-click LangGraph nodes or custom LinkedIn tools for v1.

Our worker code passes:

```text
Agent(
  task="Search {platform} for '{role}'. Up to 8 jobs from last 7 days. Return JSON array …",
  browser=Chrome(job-search profile),
  llm=Qwen(...),
)
```

Browser-Use internally: **observe → LLM decides → act → repeat** until stop conditions met → return structured output.

We control **what** to search and **when to stop** via task prompt + locked caps. We do **not** wire each browser action ourselves.

---

## Locked — API keys: ECS vs worker (Option B)

**Status:** Locked (2026-07-05).

Two secrets, two jobs:

| Secret | Where | Purpose |
|--------|--------|---------|
| **`DASHSCOPE_API_KEY` (ECS)** | Server `.env` only | Profile LLM, `enrich_job` — never exposed to website |
| **User `DASHSCOPE_API_KEY` (Helper)** | User’s PC — **user must provide** | Browser-Use ReAct loop on local Chrome |

**Locked choice: Option B** — each user enters **their own** Dashscope API key in Search Helper setup (store in OS keychain / encrypted local config — not in git, not in frontend, not baked into a public `.exe` with our key).

ECS key stays server-side for cloud LLM. Worker key is **only** for browser agent steps on that user’s machine.

**Not MVP:** ECS proxy for every browser LLM step (key never on client) — stronger but more latency and build cost; defer.

---

## Locked — API key and `.exe` (honest rule)

**Status:** Locked (2026-07-05).

If the Helper is a **`.exe` on the user’s PC** and calls Qwen **directly**, the key **cannot be fully hidden** from someone who owns that machine (`.env`, bundled config, and PyInstaller bundles are all recoverable).

**Mitigations we accept:**

- Do **not** ship one public `.exe` with **our** Dashscope key inside.
- **Option B:** user supplies their own key — leak affects **their** quota, not ours.
- Never commit keys; never put keys in frontend JS.
- **Hackathon demo:** presenter’s `.exe` on presenter’s laptop with presenter’s key only.

**`WORKER_TOKEN`** protects JobPilot API access (revocable). It does **not** replace user-owned Dashscope for browser LLM.

---

## Locked — `WORKER_TOKEN`

**Status:** Locked (2026-07-05).

**What it is:** A long-lived secret issued when a user **pairs** one computer in Settings. It proves: *this Search Helper is allowed to act for this JobPilot account* — poll tasks, post results, heartbeat.

**Not the same as:**

| | `WORKER_TOKEN` | User Dashscope API key |
|--|----------------|------------------------|
| Issued by | JobPilot ECS | User (Alibaba) |
| Used for | Helper ↔ JobPilot API | Browser-Use → Qwen |
| Revoke | Settings → disconnect computer | User rotates in Dashscope |

**Pairing flow (once per PC):**

```text
User logs into JobPilot website
  → Settings: "Connect this computer for job search"
  → ECS issues token (or pairing code → confirm)
  → Helper saves WORKER_TOKEN locally
  → Helper shows "Connected"
```

**Helper loop (each search session):**

```text
Authorization: Bearer <WORKER_TOKEN>

GET  /api/worker/tasks/next
POST /api/worker/heartbeat
POST /api/worker/tasks/{id}/result   (raw listings)
POST /api/worker/tasks/{id}/fail
```

ECS maps token → `user_id` → only that user’s tasks. Revoke via `DELETE /api/worker/pair` — old token stops working.

**Three credentials (product model):**

```text
Website login (JWT cookie)  →  who you are in the browser
WORKER_TOKEN                →  which PC may run searches for you
User Dashscope key          →  who pays for browser-agent LLM on that PC
```

Helper needs **WORKER_TOKEN + user Dashscope key** to run real search (Option B).

---

## Locked — ECS ↔ worker data contract

**Status:** Locked (2026-07-05).

One **search task** out → worker browses on PC → one **result** or **fail** back. Not page-by-page. Types from `backend/app/models/browser.py` and worker API spec.

---

### ECS → Worker (`GET /api/worker/tasks/next`)

**What ECS sends:** search **instructions** only — not CV, not full profile, not LangGraph state, not ECS `DASHSCOPE_API_KEY`.

| Field | Type | Example | Purpose |
|-------|------|---------|---------|
| `taskId` | string | `"uuid"` | Id for result/fail POST |
| `runId` | int | `42` | Links to `search_runs` |
| `role` | string | `"Python Developer"` | Search query |
| `platform` | `"linkedin"` \| `"indeed"` | `"linkedin"` | Job site |
| `maxListings` | int | `8` | Locked scrape cap |
| `skillsSummary` | string | `"Python, FastAPI, SQLite"` | Optional agent prompt hint |
| `chromeProfileDirectory` | string | `"Profile 1"` | Chrome job-search profile |

```json
{
  "taskId": "a1b2c3d4-...",
  "runId": 42,
  "role": "Python Developer",
  "platform": "linkedin",
  "maxListings": 8,
  "skillsSummary": "Python, FastAPI, SQLite",
  "chromeProfileDirectory": "Profile 1"
}
```

**Add when implementing (from locked stops):** `maxJobAgeDays: 7` for 1-week filter — include in task payload + Browser-Use prompt.

---

### Worker → ECS — success (`POST /api/worker/tasks/{taskId}/result`)

| Field | Type | Purpose |
|-------|------|---------|
| `listings` | `RawJobListing[]` | Raw browser output |
| `warnings` | `string[]` (optional) | e.g. CAPTCHA, partial scrape |

**Each `RawJobListing`:**

| Field | Type | Example |
|-------|------|---------|
| `title` | string | `"Senior Python Developer"` |
| `company` | string | `"Acme Corp"` |
| `url` | string | `"https://linkedin.com/jobs/view/..."` |
| `descriptionText` | string | JD snippet from listing |
| `sourcePlatform` | `"linkedin"` \| `"indeed"` | Source site |

```json
{
  "listings": [
    {
      "title": "Python Developer",
      "company": "Acme",
      "url": "https://www.linkedin.com/jobs/view/123",
      "descriptionText": "Build APIs with FastAPI...",
      "sourcePlatform": "linkedin"
    }
  ],
  "warnings": []
}
```

ECS runs **`normalize_listings`** → **`drop_applied`** after this. Worker does **not** normalize, score, or filter applied jobs.

---

### Worker → ECS — failure (`POST /api/worker/tasks/{taskId}/fail`)

| Field | Type | Example |
|-------|------|---------|
| `error` | string | Human-readable message |
| `code` | string | `browser_not_ready`, `worker_offline`, etc. |

---

### Worker → ECS — heartbeat (`POST /api/worker/heartbeat`)

Separate from search result. Used for “Helper connected / Chrome ready” UI.

| Field | Type | Purpose |
|-------|------|---------|
| `browserHealth` | enum | `ready`, `profile_setup`, `busy`, `error`, … |

---

### Flow summary

```text
ECS  ──task──►  Worker
     { runId, role, platform, maxListings, skillsSummary, chromeProfileDirectory }

Worker  ──result──►  ECS
        { listings: RawJobListing[], warnings? }

Worker  ──fail──►  ECS
        { error, code }
```

**One line:** ECS sends **what to search**; worker sends **raw job rows** (or fail). Smarter work stays on ECS.

---

## Locked — Search Helper minimal UI (PySide6)

**Status:** Locked (2026-07-05).

Terminal-only Helper is **not** acceptable for users (API key entry, pairing, trust). Dev may use `python main.py` in terminal during build; **users get a minimal desktop UI**.

**Framework:** **PySide6** (Qt, LGPL — preferred over PyQt6 for open repo).

**Hackathon packaging:** PyInstaller `.exe` bundling Python + PySide6 + worker code. **Later:** optional Tauri/Electron — not MVP.

### Minimal UI scope

| Screen / state | What user sees |
|----------------|----------------|
| **First launch** | Enter **Dashscope API key** (Option B) + save locally |
| **Pairing** | Enter pairing code from JobPilot Settings |
| **Connected** | Connected · Job browser ready |
| **Idle** | Waiting for search… |
| **Searching** | Searching LinkedIn for {role}… (Chrome opens separately) |
| **Done** | Found N jobs — sent to JobPilot |
| **Error** | Plain message (not paired / Chrome not ready / invalid API key) |

**Also:** system **tray icon** (`QSystemTrayIcon`) — Helper runs in background without a terminal.

**Not in Helper UI:** job list, scoring, CV edit (those stay on JobPilot website). Optional “Advanced → logs” for dev only.

**Website:** `SearchHelperStatus.tsx` on Search page shows connected / not connected (second surface alongside Helper UI).

---

## Locked — User trust: installing Search Helper

**Status:** Locked (2026-07-05).

Installing a local app is a **justified trust step** — same class as Zoom/Slack desktop agents. Defensible because **LinkedIn search cannot run on ECS** (real Chrome session + residential IP required).

**Mitigations (enough for user + judge trust):**

- Open-source `worker/` in public repo — users can read what it runs  
- **Separate Chrome profile** (“Job search”) — not user’s main browsing profile  
- **Option B:** user’s own Dashscope key — our key not baked into public `.exe`  
- **`WORKER_TOKEN`:** revocable in Settings; scoped to one account; HTTPS only  
- Clear download copy: what Helper does and does **not** do  
- **Hackathon:** judges use **ECS website** without installing Helper; **presenter** runs Helper on **presenter laptop** for real LinkedIn demo clip  

**Not claimed:** zero risk or hidden keys on client — honest rule in [Locked — API key and `.exe`](#locked--api-key-and-exe-honest-rule).

---

## Agreed way to build the search agent

**Status:** Locked build agreement (2026-07-05).  
**Use this section** when implementing search subgraph + Search Helper. Supersedes scattered notes above where they conflict.

---

### 1. Architecture (agreed)

| Decision | Agreement |
|----------|-----------|
| **User view** | One “Start search” action |
| **Engineer view** | Two parts: **ECS search subgraph** + **PC browser agent** |
| **ECS search subgraph** | LangGraph subgraph: `enqueue_browser_task` → `wait_for_listings` → `normalize_listings` → `drop_applied` — **no LLM** |
| **PC browser agent** | Browser-Use ReAct inside **JobPilot Search Helper** — **has LLM**, returns **raw** listings once |
| **Connection** | **One task out, one result back** — not page-by-page realtime between ECS and PC |
| **Parent graph** | `init_run` → `search_subgraph` → `prefilter` → … (search slice builds subgraph first) |
| **After search** | Normalize + drop applied on ECS; scoring in **application subgraph** (separate, later) |
| **No mock/demo path** | Build real worker queue + Helper path (per project system-focus rule) |
| **Frontend ↔ graph** | **Not wired yet** — `POST /api/search` creates DB row only; graph invoke wired later |

---

### 2. Stopping conditions (agreed)

**Browser (Helper) — stop scrolling when:**

- **8 jobs** collected (`max_listings`), **and** only jobs **posted within last 7 days**, **OR**
- No more jobs within the last 7 days to collect  

**ECS (`wait_for_listings`) — stop waiting when:**

- Worker **result**, worker **fail**, or **120s timeout**

**Deferred:** `max_pages` — add only if testing shows runaway scrolling.

**Supporting:** empty `[]` = success; Helper offline at enqueue = fail.

---

### 3. Data contract (agreed)

**ECS → worker:** `taskId`, `runId`, `role`, `platform`, `maxListings`, `skillsSummary`, `chromeProfileDirectory` (+ `maxJobAgeDays: 7` when implementing).

**Worker → ECS success:** `listings: RawJobListing[]`, optional `warnings`.

**Worker → ECS fail:** `error`, `code`.

**Heartbeat:** `browserHealth` for UI status.

**Not sent to worker:** CV, full profile, ECS Dashscope key, LangGraph state.

---

### 4. Credentials & security (agreed)

| Credential | Where | Purpose |
|------------|--------|---------|
| JWT cookie | Website | User login |
| **`WORKER_TOKEN`** | Helper (paired once per PC) | Helper ↔ JobPilot API — revocable |
| **User Dashscope key** | Helper (Option B) | WebBridge + Qwen ReAct loop on PC |
| **ECS Dashscope key** | Server `.env` | Profile LLM + `enrich_job` |

Do **not** ship public `.exe` with our Dashscope key inside.

---

### 5. Technologies (agreed stack)

| Layer | Technology |
|-------|------------|
| **Orchestration (ECS)** | LangGraph **≥1.2.6, &lt;2** · Python · `RunState` / `SearchState` |
| **API (ECS)** | FastAPI · SQLite · `search_runs` · `worker_tasks` (to add) |
| **Search subgraph (ECS)** | Python nodes — no `browser_use` import on ECS in production |
| **Browser agent (PC)** | **Kimi WebBridge** (v1) · `BrowserProvider` · real Chrome via extension |
| **Browser LLM (PC)** | **Qwen via Dashscope** — user-provided key (Option B) |
| **Cloud LLM (ECS)** | **Qwen via Dashscope** — profile tasks + `enrich_job` (later) |
| **Helper UI (PC)** | **PySide6** minimal window + system tray |
| **Helper packaging** | **PyInstaller** `.exe` (hackathon demo); dev: `python main.py` |
| **Worker ↔ ECS** | HTTPS · `WORKER_TOKEN` · poll `GET /tasks/next` every ~3s |
| **Website status** | React · `SearchHelperStatus.tsx` (to build) |
| **Provider** | Kimi WebBridge v1 (replaces Browser-Use) — [`kimi-webbridge-provider.md`](../../System%20Design/kimi-webbridge-provider.md) |

---

### 6. Techniques & patterns (agreed)

- **LangGraph parent graph** = code routing, not LLM supervisor  
- **Browser ReAct** = opaque inside Kimi WebBridge + Qwen loop — not LangGraph click nodes  
- **Task prompt** controls role, platform, max jobs, 1-week filter, JSON output shape  
- **Deterministic cleanup** on ECS: URL normalize, dedupe, `drop_applied(user_id)`  
- **Async search:** user polls `/runs/{id}/status` — graph runs in background (when wired)  
- **Import rule:** ECS graph/routes never import `browser_use` in `BROWSER_EXECUTION=worker` mode  
- **Three-tier model:** Tier 1 ECS · Tier 2 Search Helper · Tier 3 BrowserProvider  

---

### 7. Build order (agreed sequence)

| Step | What | Status |
|------|------|--------|
| 1 | Parent graph skeleton + edges | Done |
| 2 | `init_run` node | Done |
| 3 | **Search subgraph (ECS)** — `enqueue`, `wait`, `normalize`, `drop_applied` | **Next** |
| 4 | `search_store` + `worker_tasks` table + worker API routes | With step 3 |
| 5 | **Search Helper** — poll loop + Kimi WebBridge provider | After ECS queue |
| 6 | **PySide6 minimal UI** — API key, pair, status, tray | With Helper |
| 7 | Wire `POST /api/search` → background graph | When subgraph + queue ready |
| 8 | `prefilter` + application subgraph | After search works end-to-end |

---

### 8. Hackathon demo (agreed)

- **Judges:** ECS website — signup, profile, search (requires paired Search Helper)  
- **Presenter:** Search Helper on presenter PC — real LinkedIn search in video  
- **Proof:** Alibaba ECS deploy + Qwen on server; browser proof from local Helper  

---

### 9. Explicitly deferred (not in search agent MVP)

- `max_pages` safety cap (unless misbehaviour in testing)  
- ECS proxy for browser LLM calls  
- User cancel mid-search  
- Page-by-page ECS ↔ worker coordination  
- Gmail send  
- Tauri/Electron Helper (post-hackathon)  
- WebBridge provider (v2)  

---

### 10. Reference docs

- [`System Design/jobpilot-agent-build-guide.md`](../../System%20Design/jobpilot-agent-build-guide.md)  
- [`System Design/browser-provider-abstraction.md`](../../System%20Design/browser-provider-abstraction.md)  
- [`backend/app/models/browser.py`](../../backend/app/models/browser.py)  
- [`docs/phase-a-step-1-contracts.md`](../phase-a-step-1-contracts.md)  

**When implementing:** follow §7 build order; do not add deferred items unless a locked decision is updated here first.

---

## Locked — After worker returns data (search subgraph → prefilter)

**Status:** Locked (2026-07-05).

When the worker **`POST`s raw listings**, handling is **not** handed straight to `prefilter`. The **search subgraph** finishes first; **`prefilter` is the next parent graph node** after the subgraph exits.

```text
Worker POSTs raw listings
        ↓
┌─ search_subgraph (ECS) ──────────────────────────────┐
│  wait_for_listings    ← receive RawJobListing[]     │
│  normalize_listings   ← clean URLs, dedupe          │
│  drop_applied         ← remove already-applied URLs │
└────────────────────────── listings → SearchState ──┘
        ↓
Parent RunState.listings updated (map from subgraph)
        ↓
prefilter               ← NEXT parent node (outside search subgraph)
        ↓
fanout → application_subgraph → persist
```

| Step | Node | Graph | Responsibility |
|------|------|-------|----------------|
| Receive raw data | `wait_for_listings` | Search subgraph | Worker result → `raw_listings` / `listings` |
| Clean | `normalize_listings` | Search subgraph | URL normalize, dedupe keys |
| Applied filter | `drop_applied` | Search subgraph | Drop URLs in `job_applications` for this user |
| Skill filter + cap | `prefilter` | **Parent** | Cheap overlap vs profile skills; cap N → `matched_jobs` |

Worker talks **only** to ECS task APIs. Worker does **not** call `prefilter`. Search subgraph does **not** run Qwen or score jobs.

