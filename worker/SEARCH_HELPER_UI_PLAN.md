# Search Helper Desktop UI — Improvement Plan

**Status:** `.exe` build works end-to-end. **Only the UI needs polish.**  
**Start here in a new chat** — do not re-read the full packaging history unless blocked.

---

## Hard rule (do not break)

**Do NOT change worker/agent logic.** The search loop is frozen and working.

| Do not edit | Why |
|-------------|-----|
| `agent_loop.py`, `prompts.py`, `webbridge_scroll.py`, `parse.py`, `browser_client.py`, `api_client.py`, `providers/webbridge.py`, etc. | Agent + browser behavior — fixed after many iterations |
| `main.py` worker loop | Poll / task / heartbeat logic |

| OK to edit (UI + packaging shell only) | Why |
|----------------------------------------|-----|
| `worker/launcher.py` | PySide6 window — primary UI work |
| `worker/app_entry.py` | Entry point only |
| `worker/local_config.py` | UI → `.env` mapping (no agent logic) |
| `worker/runtime_paths.py` | Data dir for frozen exe |
| `worker/build.spec`, `build.cmd` | Rebuild after UI changes |
| New files under `worker/ui/` | Styles, assets, widgets (recommended split) |

Worker still runs as a **subprocess** (`--worker-internal`). UI must keep calling `save_config()` + `apply_config_to_environ()` + `QProcess` start — same contract as today.

---

## What works today

- **Build:** `worker\build.cmd` → `worker\dist\JobPilot-SearchHelper.exe` (~70 MB)
- **Config saved to:** `%LOCALAPPDATA%\JobPilot\SearchHelper\.env`
- **Fields:** pairing code, Dashscope API key, Qwen model name
- **Tray:** minimize to tray; close ≠ quit
- **Logs:** Advanced logs panel streams subprocess stdout
- **Verified:** user confirmed exe runs searches successfully

**Current UI file:** [`launcher.py`](launcher.py) — functional but plain (default Qt widgets, grey status bar, no branding).

---

## Locked UI requirements

Source: [`docs/discussion/search-subgraph-discussion-and-finalization.md`](../docs/discussion/search-subgraph-discussion-and-finalization.md) (Search Helper minimal UI section).

### User-facing fields (setup)

| Field | Env var | Notes |
|-------|---------|-------|
| Pairing code | `WORKER_TOKEN` | From JobPilot website → Settings → Connect this computer |
| Dashscope API key | `DASHSCOPE_API_KEY` | User's own key (Option B) — password field |
| Qwen model | `QWEN_MODEL` | Free text, default `qwen-plus` (e.g. `qwen-max`, `qwen-vl-max`) |

**Hidden / not in UI** (baked in `local_config.py`):

- `JOBPILOT_API_BASE` = `http://43.98.197.132`
- `BROWSER_PROVIDER`, `WEBBRIDGE_URL`, poll/agent step defaults

### Status states (main window — plain language)

| State | User sees |
|-------|-----------|
| First launch / not started | Prompt to enter settings + Start |
| Starting | Starting Search Helper… |
| Connected + WebBridge ready | Connected · Ready to search |
| Idle (worker running) | Waiting for search… |
| Task received | Searching LinkedIn for {role}… |
| Task done | Found N jobs — sent to JobPilot |
| WebBridge not ready | Open Chrome — extension not connected |
| Daemon down | Starting WebBridge… (worker auto-starts) |
| Error | Plain message (not paired / invalid key / worker crashed) |

Derive status from subprocess log lines (already partially in `_update_status_from_log`) — **no new worker API needed**.

### System tray

- Icon + tooltip with current status
- Menu: **Show window**, **Quit**
- Close window → hide to tray (already implemented)

### Advanced (collapsed by default)

- **View logs** — mirror terminal output (monospace, scrollable)
- Do not expose Jobs vs Posts phases, Indeed, or internal agent flags

### Must NOT show in UI

- Jobs / Posts phase toggle (Jobs disabled in `prompts.py` — internal only)
- Job list, scoring, CV editing (website only)
- Our Dashscope key baked into exe

### WebBridge setup help (copy from website)

Reference: [`frontend/src/components/settings/SearchHelperSettings.tsx`](../frontend/src/components/settings/SearchHelperSettings.tsx)

- Link: https://www.kimi.com/features/webbridge
- Short checklist: install WebBridge + Chrome extension → log into LinkedIn → paste pairing code → Start
- Show install card when WebBridge not ready (infer from log: `extension not connected`, `daemon down`)

---

## Design direction (match JobPilot web app)

Use existing JobPilot design tokens — **not a new brand**.

| Token | Value | Usage |
|-------|-------|-------|
| Primary | `#0D9488` | Primary buttons, accents |
| Background | `#F8FAFC` | Window background |
| Surface | `#FFFFFF` | Cards |
| Text primary | `#0F172A` | Headings |
| Text secondary | `#64748B` | Helper text |
| Border | `#E2E8F0` | Card borders |
| Success | `#16A34A` | Ready status |
| Warning | `#D97706` | WebBridge waiting |
| Error | `#DC2626` | Errors |
| Font | Inter (or system sans fallback) | Match web |

**Reference screens:**

- Web Settings (Search Helper section): `frontend/UI Design/08-settings/`
- Design system: [`.stitch/DESIGN.md`](../.stitch/DESIGN.md)
- Live component patterns: `SearchHelperSettings.tsx`

**Window size:** compact desktop utility — suggest **480×640** min, not full 1440px web layout. Single column card, no sidebar.

---

## Stitch MCP workflow (design first, then implement in PySide6)

MCP server: `project-0-JobPilot-stitch`

### Project context (existing)

```json
{
  "projectId": "15608968145801711863",
  "title": "JobPilot",
  "designSystem": "assets/03714a654855452089a6eff03cc905e7"
}
```

From [`.stitch/project.json`](../.stitch/project.json).

### Step 1 — Generate desktop screen(s)

Tool: `generate_screen_from_text`

```
projectId: 15608968145801711863
designSystem: assets/03714a654855452089a6eff03cc905e7
deviceType: DESKTOP
modelId: GEMINI_3_1_PRO
```

**Suggested prompt (screen 09 — Search Helper desktop app):**

```
Design a compact Windows desktop utility window for "JobPilot Search Helper" (not a browser tab).
Single window ~480px wide, JobPilot teal brand (#0D9488), Inter font, calm professional tone.

Include:
- Header with JobPilot name + subtitle "Runs on this PC"
- Status card with colored state (ready=green, waiting=amber, error=red)
- Settings card: Pairing code input, Dashscope API key (masked), Qwen model input (default qwen-plus)
- Primary "Start" button and secondary "Save" / "Stop"
- Collapsed "Advanced logs" section
- Small footer link area: "Install Kimi WebBridge" external link
- Optional: system tray hint text "Runs in background when closed"

States to show as separate variants OR one screen with annotated states:
1) First launch (empty fields)
2) Connected · Waiting for search
3) Searching LinkedIn
4) WebBridge not ready (warning + install CTA)

Do NOT include: job lists, sidebar nav, Jobs/Posts toggles, Indeed, or website chrome.
Match JobPilot web settings Search Helper section visual language.
```

If Stitch suggests variants ("Also generate searching state"), accept and generate 2–3 state screens.

### Step 2 — Download assets

Tools: `get_screen`, `download_assets`

- Export HTML + screenshot per screen
- Save under: `worker/UI Design/search-helper/` (mirror `frontend/UI Design/` pattern)
  - `screen.html`, `screenshot.png`, `meta.json`

### Step 3 — Implement in PySide6

Map Stitch layout to Qt widgets in `launcher.py` (or split):

| Stitch element | PySide6 |
|----------------|---------|
| Status card | `QFrame` + dynamic stylesheet |
| Settings card | `QGroupBox` / `QFrame` with `QFormLayout` |
| Primary button | `QPushButton` objectName `primary` |
| Logs | `QPlainTextEdit` inside `QGroupBox` setCheckable / `QToolBox` |
| Link | `QLabel` with rich text + `openExternalLink` |

Apply global stylesheet from design tokens (QSS file: `worker/ui/styles.qss`).

**Keep existing logic methods** — only replace `_build_ui`, styling, and status presentation.

### Step 4 — Rebuild exe

```powershell
cd worker
.\build.cmd
```

Test: `dist\JobPilot-SearchHelper.exe` — same functional test as before, better visuals.

---

## Current UI gaps (what to fix)

| Gap | Target |
|-----|--------|
| No JobPilot branding / colors | Teal primary, white cards, Inter |
| Generic Qt grey status bar | Colored status card (success/warning/error) |
| No app icon / tray icon | Add `worker/ui/icon.ico` (JobPilot logo) — bundle in `build.spec` `datas` |
| No WebBridge install help in desktop UI | Card + link (like website) when not ready |
| Logs always visible | Collapse "Advanced logs" by default |
| Status doesn't show role during search | Parse `Received task` log for role name |
| No "show/hide API key" toggle | Add reveal button on password field |
| Pairing instructions weak | Short step list: get code from JobPilot Settings |

---

## Suggested file structure (optional refactor)

```
worker/
  launcher.py          # window + tray + process control (thin)
  ui/
    styles.qss         # JobPilot tokens → Qt stylesheet
    widgets.py         # StatusCard, SettingsCard (optional)
    assets/
      icon.ico
  UI Design/
    search-helper/
      meta.json
      screen.html
      screenshot.png
```

---

## Acceptance criteria

- [ ] Visual match to JobPilot brand (teal, cards, typography) per Stitch export
- [ ] All three settings fields work; config still saves to `%LOCALAPPDATA%\JobPilot\SearchHelper\.env`
- [ ] Start/Stop/Save/tray behavior unchanged
- [ ] Status states readable without reading raw logs
- [ ] Advanced logs collapsed by default
- [ ] No Jobs/Posts/Indeed exposed in UI
- [ ] `agent_loop.py` and other frozen files **unchanged**
- [ ] Rebuilt exe passes: pair → start → run search on website → listings returned

---

## Quick test checklist

1. Stop any running `main.py` / old exe (only one worker per machine)
2. Run `worker\dist\JobPilot-SearchHelper.exe`
3. Enter pairing code + API key + model → **Start**
4. JobPilot Settings shows worker connected
5. Start search on website → desktop shows "Searching LinkedIn…"
6. Listings appear on website when done

---

## Related files

| File | Role |
|------|------|
| [`launcher.py`](launcher.py) | Current UI — edit this |
| [`local_config.py`](local_config.py) | Settings persistence |
| [`app_entry.py`](app_entry.py) | Exe entry |
| [`build.spec`](build.spec) | PyInstaller |
| [`README.md`](README.md) | Build/run docs |
| [`currently-working-feature.md`](../currently-working-feature.md) | Project focus pointer |
