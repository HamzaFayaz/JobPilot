# JobPilot Local Browser Worker

Runs on the **user's computer**. Pulls search tasks from JobPilot (ECS), executes them via the swappable browser provider (default: **Browser-Use**), and posts results back.

The API on ECS never runs Chrome directly.

## Prerequisites

- Python 3.11+
- Google Chrome installed
- JobPilot account (logged in on the website)
- **Job-search Chrome profile** (see below)

## One-time Chrome setup (Browser-Use)

1. In Chrome, add a second profile (e.g. rename **Profile 1** to **Job search**).
2. In that profile only, log into [LinkedIn](https://linkedin.com) (and Indeed if you use it).
3. Keep using JobPilot in your **main** profile — you do not need to close that window.

## Install

```bash
cd worker
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set:

- `JOBPILOT_API_BASE` — e.g. `http://43.98.197.132` or `http://localhost:8000`
- `WORKER_TOKEN` — from JobPilot Settings → Connect this computer (when implemented)
- `BROWSER_PROVIDER` — `browser-use` (default)
- `BROWSER_CHROME_PROFILE` — `Profile 1` (or your job-search profile directory name)

## Run

```bash
python main.py
```

Leave this running while you use JobPilot Search.

## Architecture

See [`System Design/browser-provider-abstraction.md`](../System%20Design/browser-provider-abstraction.md).

Swapping to Kimi WebBridge later: set `BROWSER_PROVIDER=webbridge` and install the WebBridge extension — no JobPilot app changes required.
