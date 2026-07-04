# JobPilot Search Helper

**User-facing name** for the local app in `worker/`. Runs on the **user's computer** — not on Alibaba ECS.

Pulls search tasks from JobPilot cloud, runs **Browser-Use** (v1) against a **job-search Chrome profile**, and posts job listings back.

## For users

| Step | How often |
|------|-----------|
| Download & install Search Helper | **Once per computer** |
| Pair with your JobPilot account | **Once** (until you disconnect in Settings) |
| Log into LinkedIn in **Job search** Chrome profile | **Once** |
| **Run** Search Helper (tray icon) | **Each time** you want real LinkedIn/Indeed search |
| Use JobPilot website | Anytime in your browser — no install |

Keep JobPilot open in your main Chrome window. We open a separate **job-search** window when searching.

## For developers

**Full build spec:** [`System Design/jobpilot-agent-build-guide.md`](../System%20Design/jobpilot-agent-build-guide.md)  
**Browser provider protocol:** [`System Design/browser-provider-abstraction.md`](../System%20Design/browser-provider-abstraction.md)

### Prerequisites

- Python 3.11+
- Google Chrome
- JobPilot account
- Chrome profile **Job search** (`Profile 1` by default) with LinkedIn logged in

### Install

```bash
cd worker
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # or copy on Windows
```

Set in `.env`:

- `JOBPILOT_API_BASE` — e.g. `http://43.98.197.132`
- `WORKER_TOKEN` — from JobPilot Settings → Connect this computer (when implemented)
- `BROWSER_PROVIDER=browser-use`
- `BROWSER_CHROME_PROFILE=Profile 1`

### Run

```bash
python main.py
```

Leave running while using Search on JobPilot.

### Chrome setup (one-time)

1. Chrome → Add profile → name it **Job search**
2. In that profile only, log into LinkedIn (and Indeed if needed)
3. Use JobPilot in your **main** profile — do not close it to search

### WebBridge (later)

Set `BROWSER_PROVIDER=webbridge` and install Kimi WebBridge. JobPilot cloud app unchanged — only the provider inside this Helper changes.
