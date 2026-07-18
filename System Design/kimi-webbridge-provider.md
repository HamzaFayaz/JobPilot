# Kimi WebBridge — Search Helper Browser Provider

**Status:** **Replacing Browser-Use** (2026-07-05)  
**Scope:** Tier 3 only — inside `worker/` on the user's PC. ECS, LangGraph, and worker HTTP protocol stay unchanged.  
**Related:** [`browser-provider-abstraction.md`](./browser-provider-abstraction.md) · [`design-decisions.md`](./design-decisions.md) §4 · [Kimi WebBridge help](https://www.kimi.com/features/webbridge)

---

## 1. Why we are switching

| Browser-Use (deprecated) | Kimi WebBridge (target) |
|--------------------------|-------------------------|
| Copies Chrome profile to a **temp folder** each run | Controls the user's **real Chrome** via extension + daemon |
| LinkedIn sessions often lost / re-login required | Uses **existing login sessions** in the browser you already use |
| Separate job-search Chrome profile required | **No second profile** — JobPilot tab can stay open |
| `browser-use` Python SDK + Qwen inside one package | HTTP tools on `127.0.0.1:10086` + **Qwen ReAct loop** in worker |
| Profile lock errors when Chrome is open | No profile copy — extension attaches to live browser |

**What does not change:** `POST /api/search`, worker task queue, `RawJobListing` JSON, search subgraph on ECS, Settings pairing UI.

---

## 2. Architecture

```text
┌──────────────── ECS (unchanged) ─────────────────┐
│  POST /api/search → graph → wait for worker      │
└────────────────────────┬─────────────────────────┘
                         │ HTTPS task + result
┌────────────────────────┴─────────────────────────┐
│  worker/main.py — poll loop (unchanged)          │
│  worker/browser_client.py → WebBridgeProvider    │
│    └─ agent_loop.py (Qwen + tool calls)          │
└────────────────────────┬─────────────────────────┘
                         │ POST http://127.0.0.1:10086/command
┌────────────────────────┴─────────────────────────┐
│  Kimi WebBridge daemon + Chrome extension        │
│  CDP on user's Chrome (LinkedIn already logged in)│
└──────────────────────────────────────────────────┘
```

**Important:** WebBridge is **not** one-shot “single prompt” automation. The worker runs a **ReAct loop**:

1. `navigate` → LinkedIn Jobs  
2. `snapshot` → read page tree (`@e` refs)  
3. Qwen decides → `click` / `fill` / `navigate`  
4. Repeat until listings collected  
5. Return JSON array (same shape as today)

---

## 3. User setup (one-time per PC)

### 3.0 Locked versions (JobPilot Posts search)

JobPilot LinkedIn **Posts** search was verified against these builds. Prefer this pair; do **not** casually upgrade mid-project without re-testing Posts.

| Component | Locked / verified | Notes |
|-----------|-------------------|--------|
| Daemon (`kimi-webbridge`) | **v1.10.0** | `kimi-webbridge status` → `version` |
| Chrome/Edge extension | **1.11.3** | `status` → `extension_version` |

**Why lock:** the HTTP tool API stays the same, but LinkedIn Posts a11y trees can change between WebBridge builds (`listitem` vs bare list under Primary content). JobPilot’s parser supports both shapes today; a future upgrade could still change trees again and break extraction until we adapt.

**Policy:**

- Install / stay on the locked pair above for demos and production Helper use.
- If `status` shows `update_available`, **do not auto-upgrade** until Posts is re-checked on a test run.
- After any intentional upgrade, run one Posts search and confirm `diagnosis.md` shows `verdict: posts_extracted` (not `filters_only_or_empty_tree`).

Check versions:

```powershell
& "$env:USERPROFILE\.kimi-webbridge\bin\kimi-webbridge.exe" status
```

Expect roughly:

```json
{
  "running": true,
  "extension_connected": true,
  "version": "v1.10.0",
  "extension_version": "1.11.3"
}
```

### 3.1 Install

1. Install **Kimi WebBridge** binary (via [Kimi WebBridge features page](https://www.kimi.com/features/webbridge)) — prefer daemon **v1.10.0**  
2. Install the **Chrome or Edge extension** from the store linked on that page — prefer extension **1.11.3**  
3. (Optional) Kimi Desktop App — helps extension connection  

Binary location (Windows):

```text
%USERPROFILE%\.kimi-webbridge\bin\kimi-webbridge.exe
```

### 3.2 Start daemon

```powershell
& "$env:USERPROFILE\.kimi-webbridge\bin\kimi-webbridge.exe" start
```

`start` is idempotent — safe if already running.

### 3.3 Verify

```powershell
& "$env:USERPROFILE\.kimi-webbridge\bin\kimi-webbridge.exe" status
```

Expect `running: true` and `extension_connected: true`, plus the locked versions in §3.0.

Daemon HTTP: `http://127.0.0.1:10086`

### 3.4 LinkedIn

Log into **LinkedIn in your normal Chrome** (the browser the extension controls). No separate JobPilot profile.

---

## 4. Worker configuration

```env
# worker/.env
BROWSER_PROVIDER=webbridge
WEBBRIDGE_URL=http://127.0.0.1:10086

JOBPILOT_API_BASE=http://43.98.197.132
WORKER_TOKEN=<from Settings>

# Qwen drives the ReAct loop (tool selection)
DASHSCOPE_API_KEY=<your key>
QWEN_MODEL=qwen-plus
```

**Remove / ignore for WebBridge:**

- `BROWSER_CHROME_PROFILE` — not used  
- `BROWSER_USER_DATA_DIR` — not used  
- `browser-use` package — will be removed from `requirements.txt`

---

## 5. WebBridge HTTP API (worker → daemon)

All commands: `POST {WEBBRIDGE_URL}/command` with JSON body:

```json
{
  "action": "navigate",
  "args": { "url": "https://www.linkedin.com/jobs/", "newTab": true, "group_title": "JobPilot search" },
  "session": "jobpilot-run-42"
}
```

| Action | Purpose for JobPilot |
|--------|----------------------|
| `navigate` | Open LinkedIn Jobs, job detail pages |
| `snapshot` | Read accessibility tree + `@e` element refs |
| `click` | Apply filters, open job cards |
| `fill` | Search bar (role + location) |
| `evaluate` | Fallback JS when no `@e` ref |
| `list_tabs` / `find_tab` | Recover focus if needed |
| `close_session` | Optional cleanup after task |

**Session rule:** One `session` string per search run (e.g. `jobpilot-run-{runId}`). All tabs for that task share one Chrome tab group.

**Windows:** Send JSON via `curl.exe --data-binary "@file.json"` (see skill — inline JSON breaks non-ASCII).

**Full tool reference:** `.cursor/skills` or Claude skill `kimi-webbridge` (`SKILL.md` + `references/operations.md`).

---

## 6. LinkedIn search flow (prompt / agent goals)

Same UX as a human — encode in the agent system prompt:

1. `navigate` → `https://www.linkedin.com/jobs/` (single tab group, session = run id)  
2. `fill` search: role + country  
3. Open **All filters**  
4. **Date posted** → map from `jobAge`: `24h` → Past 24 hours, `week` → Past week, `month` → Past month  
5. **Workplace type** → map from `workMode`: remote / on-site / both  
6. Collect up to `maxListings` jobs — title, company, url, description  
7. Return **only** a JSON array (`RawJobListing` shape)

---

## 7. Code layout (target)

```text
worker/
  main.py                    # unchanged poll loop
  browser_client.py          # get_browser_provider() → WebBridgeProvider
  agent_loop.py              # NEW: Qwen + WebBridge tools
  providers/
    webbridge.py             # NEW: HTTP client for :10086
    browser_use.py           # DEPRECATED — remove after WebBridge works
  webbridge_tools.py         # navigate, snapshot, click, fill wrappers
  prompts.py                 # search task + tool-use system prompt
  parse.py                   # unchanged JSON parse
```

```text
backend/app/services/browser/   # optional mirror for BROWSER_EXECUTION=local
  factory.py
  providers/webbridge.py
```

ECS **never** imports WebBridge or Browser-Use.

---

## 8. Health checks

| Check | Worker `health()` | UI (Settings) |
|-------|-------------------|-----------------|
| Daemon up | GET or `kimi-webbridge status` | “Start WebBridge” link |
| Extension connected | `extension_connected: true` | “Install extension” |
| Ready for search | both true | Search enabled |

Map to existing `BrowserHealth`: `ready`, `daemon_down`, `not_installed`, `error`.

---

## 9. Migration checklist

- [ ] User: install WebBridge binary + extension; daemon running  
- [ ] Implement `worker/providers/webbridge.py`  
- [ ] Implement `worker/agent_loop.py` (Qwen tool loop)  
- [ ] Wire `browser_client.py` → `BROWSER_PROVIDER=webbridge`  
- [ ] Update Settings UI: WebBridge setup card (replace Chrome profile card)  
- [ ] Remove `browser-use` from `worker/requirements.txt`  
- [ ] Delete or archive `browser_use` code paths  
- [ ] E2E: ECS search → worker → LinkedIn → listings in UI  

**Do not change:** `POST /api/search`, worker task payload, `RawJobListing`, search subgraph nodes, DB schema.

---

## 10. References

| Resource | URL / path |
|----------|------------|
| Kimi WebBridge product page | https://www.kimi.com/features/webbridge |
| Kimi WebBridge (中文) | https://www.kimi.com/zh-cn/features/webbridge |
| Agent skill (tool API) | `kimi-webbridge/SKILL.md` |
| Daemon operations | `kimi-webbridge/references/operations.md` |
| JobPilot provider protocol | [`browser-provider-abstraction.md`](./browser-provider-abstraction.md) |
| Build phases | [`jobpilot-agent-build-guide.md`](./jobpilot-agent-build-guide.md) |

---

## 11. Decision log

| Date | Decision |
|------|----------|
| 2026-07-02 | Browser-Use shipped as v1 spike |
| 2026-07-05 | **Replace Browser-Use with Kimi WebBridge** — profile copy and session issues block reliable LinkedIn search |
| 2026-07-18 | Posts a11y: newer WebBridge trees expose Feed posts as **bare lists** under `region: Primary content` (not always `listitem`). Parser accepts both shapes. Per-run `diagnosis.md` records shape + DOM probe. |
| 2026-07-18 | **Lock WebBridge for JobPilot:** daemon **v1.10.0** + extension **1.11.3**. Do not auto-upgrade; re-test Posts before changing. |
