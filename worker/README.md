# JobPilot Search Helper

Local app in `worker/` — runs on the **user's PC**, not on ECS.

Polls JobPilot cloud for search tasks, runs **Kimi WebBridge** + **Qwen (`qwen-plus`)** ReAct loop against the user's **real Chrome** (existing LinkedIn login), and posts raw listings back.

> **Migration:** Browser-Use removed. Setup: [`System Design/kimi-webbridge-provider.md`](../System%20Design/kimi-webbridge-provider.md)

## Dev setup (use `worker/.venv` — not global Python)

```powershell
cd worker
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `worker/.env`:

| Variable | Example |
|----------|---------|
| `JOBPILOT_API_BASE` | `http://43.98.197.132` or `http://localhost:8000` |
| `WORKER_TOKEN` | From JobPilot Settings → pairing code |
| `DASHSCOPE_API_KEY` | Your Dashscope key (browser LLM on this PC only) |
| `QWEN_MODEL` | `qwen-plus` (default) |
| `BROWSER_PROVIDER` | `webbridge` (default) |
| `WEBBRIDGE_URL` | `http://127.0.0.1:10086` |

## Kimi WebBridge one-time setup

**Locked versions (do not casually upgrade):** daemon **v1.10.0** + extension **1.11.3**. Details: [kimi-webbridge-provider.md §3.0](../System%20Design/kimi-webbridge-provider.md).

1. Install Kimi WebBridge + Chrome extension — [kimi-webbridge-provider.md](../System%20Design/kimi-webbridge-provider.md)
2. Log into LinkedIn in your normal Chrome (no separate profile)
3. Pair below in JobPilot Settings → paste `WORKER_TOKEN` into `worker/.env`
4. Run the helper — it auto-starts the daemon and reports WebBridge health

```powershell
.\.venv\Scripts\pip.exe install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Daemon status (manual check):

```powershell
& "$env:USERPROFILE\.kimi-webbridge\bin\kimi-webbridge.exe" status
```

Expect `running: true`, `extension_connected: true`, `version: "v1.10.0"`, `extension_version: "1.11.3"`. If `update_available` appears, ignore it until Posts is re-tested.
## Run locally (test before .exe)

```powershell
.\.venv\Scripts\python.exe main.py
```

Or test the GUI launcher in dev:

```powershell
cd ..
.\worker\.venv\Scripts\python.exe -m worker.app_entry
```

Leave it running. On the website: Settings → pair Search Helper → Start search.

## Build Search Helper `.exe` (Windows)

```powershell
cd worker
.\build.cmd
```

Output: `worker\dist\JobPilot-SearchHelper.exe` (~70 MB).

1. Double-click the exe
2. Enter **pairing code**, **Dashscope API key**, and **model** (default `qwen-plus`)
3. Click **Start** — settings save to `%LOCALAPPDATA%\JobPilot\SearchHelper\.env`
4. Close the window to keep running in the system tray

Worker/agent code is unchanged; the exe wraps the same `main.py` loop in a subprocess.

## Debug snapshots (Posts / Jobs)

When `SAVE_SNAPSHOTS` is true (default), each run writes under `worker/debug_snapshots/run-{id}/`:

| Path | Contents |
|------|----------|
| `{phase}/full/step-NN-*.json` | Raw WebBridge tool results |
| `{phase}/compressed/step-NN-snapshot.json` | Compressed a11y + extracted posts/jobs |
| `{phase}/diagnosis/step-NN-snapshot.json` | Tree shape, Feed post counts, verdict |
| `{phase}/diagnosis/step-NN-activity-urls.json` | `evaluate` activity URL probe |
| `{phase}/scrolls.jsonl` | Scroll before/after counts + errors |
| `diagnosis.md` / `diagnosis.json` | Run-level summary |
| `run-summary.json` | Steps, tokens, listings |

Use `diagnosis.md` first when Posts returns 0 listings — it says whether the a11y tree had `Feed post` headings (`bare_list` vs `listitem` vs `none`) and whether the DOM probe saw activity nodes.

## Pairing WORKER_TOKEN

1. Log into JobPilot in the browser
2. Settings → **Connect this computer** — copy pairing code (optional: [Watch setup video](https://youtu.be/gYTl1co9FKQ))
3. Paste into `worker/.env` as `WORKER_TOKEN` (or Helper Settings if using the `.exe`)

## Model note

Default model is **`qwen-plus`** for trial token budget. If navigation misbehaves, try `qwen-vl-max` in `.env`.

## Not in this slice

- PySide6 tray UI (later)

Full spec: [`System Design/jobpilot-agent-build-guide.md`](../System%20Design/jobpilot-agent-build-guide.md) · [`kimi-webbridge-provider.md`](../System%20Design/kimi-webbridge-provider.md)
