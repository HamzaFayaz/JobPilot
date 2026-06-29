# JobPilot UI Design (Stitch export)

> **Reference only — desktop mockups (1440px).**  
> Do not copy layouts pixel-for-pixel. Build a **responsive website** per `frontend/progress.md` (Web UI rules).

Desktop UI screens exported from the **JobPilot** Stitch project for visual reference (colors, hierarchy, copy).

**Stitch project ID:** `15608968145801711863`  
**Design system:** `.stitch/DESIGN.md`

## Screens

| Folder | Route | Description |
|--------|-------|-------------|
| `01-welcome/` | `/` | Setup gate — profile incomplete |
| `02-profile/` | `/profile` | CV, skills, projects, Gmail |
| `03-search/` | `/search` | Start new job search |
| `04-run-progress/` | `/runs/:runId` | Agent run in progress |
| `05-job-list/` | `/runs/:runId/jobs` | Search results list |
| `06-job-detail/` | `/jobs/:id` | HITL review (Overview tab) |
| `07-applications/` | `/applications` | Applied jobs + past searches |
| `08-settings/` | `/settings` | Gmail, preferences, about |

Each folder contains:

- `screenshot.png` — visual reference
- `screen.html` — Stitch-generated HTML/Tailwind (starting point for React components)
- `meta.json` — title, route, slug

## Re-download

If Stitch designs are updated, re-run:

```powershell
powershell -ExecutionPolicy Bypass -File "frontend/UI Design/download-screens.ps1"
```

## Implementation notes

- Refactor shared shell (sidebar + layout) into a single `AppShell` component.
- Do not copy HTML verbatim — extract reusable pieces: `ScoreBadge`, `JobCard`, `HitlBanner`, etc.
- See `.agent/plans/jobpilot_stitch_ui_plan.md` for full flow and API mapping.
