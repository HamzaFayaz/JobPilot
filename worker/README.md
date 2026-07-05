# JobPilot Search Helper

Local app in `worker/` — runs on the **user's PC**, not on ECS.

Polls JobPilot cloud for search tasks, runs **Browser-Use** with **Qwen (`qwen-plus`)** against a **job-search Chrome profile**, and posts raw listings back.

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
| `WORKER_TOKEN` | From JobPilot after `POST /api/worker/pair` (logged-in user) |
| `DASHSCOPE_API_KEY` | Your Dashscope key (browser LLM on this PC only) |
| `QWEN_MODEL` | `qwen-plus` (default) |
| `BROWSER_CHROME_PROFILE` | `Profile 1` (Chrome profile with LinkedIn login) |

## Run locally (test before .exe)

```powershell
.\.venv\Scripts\python.exe main.py
```

Leave it running. On the website: set search preferences → Start search (with graph wired) or enqueue a task via API tests.

## Chrome one-time setup

1. Chrome → Add profile **Job search** (often shows as `Profile 1`)
2. Log into LinkedIn in that profile only
3. Keep JobPilot open in your main Chrome window

## Pairing WORKER_TOKEN

1. Log into JobPilot in the browser
2. Call `POST /api/worker/pair` (Settings UI coming) — copy `workerToken`
3. Paste into `worker/.env` as `WORKER_TOKEN`

## Model note

Default model is **`qwen-plus`** for trial token budget. Browser-Use officially documents best results with `qwen-vl-max`; if `qwen-plus` misbehaves on action schema, switch to `qwen-vl-max` in `.env`.

## Not in this slice

- PyInstaller `.exe` (after local `python main.py` works)
- PySide6 tray UI (later)

Full spec: [`System Design/jobpilot-agent-build-guide.md`](../System%20Design/jobpilot-agent-build-guide.md)
