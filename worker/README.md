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

Expect `running: true` and `extension_connected: true` (open Chrome if extension is false).

## Run locally (test before .exe)

```powershell
.\.venv\Scripts\python.exe main.py
```

Leave it running. On the website: Settings → pair Search Helper → Start search.

## Pairing WORKER_TOKEN

1. Log into JobPilot in the browser
2. Settings → **Connect this computer** — copy pairing code
3. Paste into `worker/.env` as `WORKER_TOKEN`

## Model note

Default model is **`qwen-plus`** for trial token budget. If navigation misbehaves, try `qwen-vl-max` in `.env`.

## Not in this slice

- PyInstaller `.exe` (after local `python main.py` works)
- PySide6 tray UI (later)

Full spec: [`System Design/jobpilot-agent-build-guide.md`](../System%20Design/jobpilot-agent-build-guide.md) · [`kimi-webbridge-provider.md`](../System%20Design/kimi-webbridge-provider.md)
