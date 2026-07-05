# JobPilot Search Helper

Local app in `worker/` — runs on the **user's PC**, not on ECS.

Polls JobPilot cloud for search tasks, runs **Kimi WebBridge** + **Qwen (`qwen-plus`)** ReAct loop against the user's **real Chrome** (existing LinkedIn login), and posts raw listings back.

> **Migration:** Browser-Use is deprecated. Setup and architecture: [`System Design/kimi-webbridge-provider.md`](../System%20Design/kimi-webbridge-provider.md)

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

1. Install Kimi WebBridge + Chrome extension — see [kimi-webbridge-provider.md](../System%20Design/kimi-webbridge-provider.md)
2. Start daemon: `kimi-webbridge.exe start`
3. Verify: `kimi-webbridge.exe status` → `running: true`, `extension_connected: true`
4. Log into LinkedIn in your normal Chrome (no separate profile needed)

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
