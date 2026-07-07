# Job Section (Enrich) Issue — Root Cause & Recommended Fixes

Analysis of **run 56** (`AI Engineer` / `linkedin` / `Pakistan`, `max=6`, `age=week`).
Source data: `logges.md` and `worker/debug_snapshots/run-56/`.

---

## TL;DR

- The agent **correctly opened every job in a new tab** — that part works.
- **Kimi WebBridge's snapshot did not contain the job description.** For every job the
  `/jobs/view/{id}/` page came back with only the **top card + a LinkedIn Premium upsell +
  footer** — the "About the job" section never rendered.
- Result: `0/3 with description` → all 3 jobs dropped → `0 listings` posted.
- **Interim action taken:** Jobs phase disabled; all listings now sourced from the **Posts phase**
  (post body carries the description). See [Interim fix](#interim-fix-applied).

---

## What happened in run 56

The Jobs phase collected 3 valid jobs from the search results list, then the enrich step
(`_enrich_jobs_from_view_pages` in `worker/agent_loop.py`) visited each job page to pull the JD:

| # | Job ID | Title / Company | Enrich result |
|---|--------|-----------------|---------------|
| 1 | 4433930433 | AI Engineer @ Hyphen Connect (APAC, Remote) | `not ready after 8 attempts` |
| 2 | 4437143380 | AI/ML Engineer @ Hire Feed (APAC, Remote) | `not ready after 8 attempts` |
| 3 | 4436786082 | AI Engineer (LInE) @ micro1 (APAC, Remote) | `not ready after 8 attempts` |

Log outcome:

```
Worker job enrich finished: 0/3 with description (run_id=56)
Dropping job missing descriptionText: AI Engineer | Hyphen Connect ...
Dropping job missing descriptionText: AI/ML Engineer (Remote) | Hire Feed ...
Dropping job missing descriptionText: AI Engineer (LInE) | micro1 ...
Phase jobs: 0 listings ... Merged LinkedIn listings: 0 (cap 3)
```

---

## Evidence

### 1. The new-tab navigation succeeded (agent did its job)

Every `.../enrich/job-*/navigate.json` confirms it:

```json
{
  "tool": "navigate",
  "args": { "url": "https://www.linkedin.com/jobs/view/4433930433/", "newTab": true },
  "result": { "ok": true, "data": { "success": true,
              "url": "https://www.linkedin.com/jobs/view/4433930433/", "tabId": 266719833 } }
}
```

- `newTab: true`, `success: true`, distinct `tabId`s (266719833 / 266719837 / 266719841), correct URLs.
- Per the WebBridge skill, `snapshot` acts on the **current tab** (the one just opened), and the
  returned snapshot's `url`/`title` matched the job page — so the snapshot targeted the right tab.

### 2. The snapshot came back WITHOUT the description

From `.../enrich/job-4433930433/snapshot.json` (73 KB, 298 nodes) and its compressed sibling:

- Page `title`: `"AI Engineer | Hyphen Connect | LinkedIn"`; "Hyphen" appears 6× → **right page**.
- Nav chrome present (`Home` / `My Network` / `Jobs` / `Messaging`) → **logged in**, and **no**
  `Sign in` / `Join now` → **not an auth wall**.
- **Only two headings on the whole page:** `"0 notifications"` (nav) and
  `"Use AI to assess how you fit"` (a **Premium upsell** card). Inside the `main` region the only
  heading is the Premium card.
- **No `"About the job"` heading. No description paragraphs.** The longest text anywhere is the
  Premium blurb: *"Premium members are up to 2.6x more likely to get hired…"*.
- Metadata: `"jobDetailReady": false`, `"jobDescriptionChars": 0`.
- **Identical across all 3 jobs** — same 3-node compressed output, same `jobDetailReady: false`.

The captured text jumps straight from the job **top card** (title, company, "Over 100 people
clicked apply", Remote, Full-time, Apply, Save) → **Premium upsell** → **footer**. The entire
"About the job" column is missing.

This is why extraction failed: both `extract_job_description_from_snapshot()` and the
`evaluate_job_description()` DOM fallback key off an `"About the job"` `h2` that never existed in
the returned page — so after 8 retries (~24s+ of waits + scrolls) → `Job view page not ready`.

---

## Root cause

- **Not** an agent bug — the tabs were opened correctly.
- The **"About the job" section never rendered/hydrated** in the opened job tab; LinkedIn served
  only the top card + Premium teaser shell.

**Leading hypothesis (most supported by the data):** the job tab is opened in the **background /
inactive** state. `_enrich_jobs_from_view_pages` navigates with `newTab: true` but **never
activates/focuses that tab** (no `find_tab` with `active: true`, no activation call). LinkedIn
lazy-loads the description (visibility / IntersectionObserver gated), and Chrome throttles
background tabs — so the description fetch/hydration never completes, and the retry scroll+wait
loop can't trigger it because the tab isn't the foreground/visible one. The `"Use AI to assess how
you fit"` card is part of the initial shell, which is why it's the only thing that filled the
description column.

**Secondary factor:** all 3 postings are *"Promoted by hirer / Responses managed off LinkedIn"*
(offsite-apply) jobs, but the empty-column + rendered-Premium-teaser pattern points at hydration,
not content gating.

---

## Interim fix applied

To keep the end-to-end flow working while the Jobs enrich path is fixed, listings are now sourced
entirely from the **Posts phase**, whose post body already carries the description
(`POST_DESCRIPTION_MAX_CHARS = 12000`) and needs no separate tab visit.

Changed in `worker/prompts.py`:

```python
LINKEDIN_JOBS_PHASE_ENABLED = False   # temporary
LINKEDIN_POSTS_PHASE_ENABLED = True

def linkedin_jobs_listing_target(max_listings: int) -> int:
    if not LINKEDIN_JOBS_PHASE_ENABLED:
        return 0                      # skips Jobs phase; full cap routes to Posts
    return max(max_listings // 2, 1)
```

Effect (verified): `listing_targets(4) == (0, 4)`, `listing_targets(6) == (0, 6)` — Jobs phase
skipped, the full `max_listings` cap collected from Posts. Tests in `tests/test_worker_prompts.py`
updated accordingly.

**To restore the Jobs phase:** flip `LINKEDIN_JOBS_PHASE_ENABLED` back to `True` **after** applying
one of the fixes below.

---

## Recommended fixes (for the Jobs enrich path)

Ordered by preference:

1. **Activate/focus the tab before snapshotting.** After `navigate(newTab: true)`, call
   `find_tab` with `active: true` (or navigate in the foreground) so LinkedIn hydrates the
   "About the job" section before the snapshot. Lowest-effort, directly targets the root cause.

2. **Reuse the search-phase detail pane instead of standalone `/jobs/view/` tabs.** The search
   results page already loads job rows successfully; clicking a row loads the description in the
   in-pane detail view (same foreground tab), which is LinkedIn's reliable path. Removes the
   background-tab problem entirely.

3. **Add a readiness gate + failure screenshot.** Only count a retry as "waiting" once the
   `"About the job"` heading is actually present, and capture a `screenshot` on failure so this is
   diagnosable from artifacts instead of guesswork.

## How to verify a fix

- Re-run the worker for a LinkedIn `AI Engineer` task and inspect
  `worker/debug_snapshots/run-<id>/jobs/enrich/job-*/snapshot-compressed.json`.
- Success = `"jobDetailReady": true` and `"jobDescriptionChars" > 0`, and the log shows
  `Worker job enrich finished: N/N with description`.
