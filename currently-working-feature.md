# Currently Working On

**Status:** Suggested CV (`tailor_cv`) **implemented** — layout contract, LLM + repair/merge/word-trim, draft download on Applications. Gmail/send remains cancelled.

**Baseline:** Run 3 (~79/100). Evals off for product work; Logfire on (see `.env.example`).

**Build plan:** [`.agent/plans/jobpilot_suggested_cv_tailor_plan.md`](.agent/plans/jobpilot_suggested_cv_tailor_plan.md)  
**Design:** [`docs/discussion/enrich-job-to-cv-tailoring-handoff.md`](docs/discussion/enrich-job-to-cv-tailoring-handoff.md)

---

## Start here (new chat)

### Done — product path `[x]`

| Area | Status |
|------|--------|
| Search → worker → prefilter → parallel application analysis | ✅ |
| Seed `analyzing` packages; Applications inbox + decisions | ✅ |
| Dual JD: raw `description_text` for analysis; display rewrite for UI | ✅ |
| Cloud browser agent (Qwen ReAct on backend; Helper = WebBridge only) | ✅ |
| Background GitHub import (hide projects until overview/evidence/index ready) | ✅ |
| Per-user search `runNumber` in UI (global `runId` kept for APIs) | ✅ |
| Helper GUI: clear logs on each new search task | ✅ |

### Next — suggested CV `[x]` shipped

| Item | Notes |
|------|--------|
| **`tailor_cv` (user-triggered)** | Applications → approve swaps → Generate suggested CV → download draft |
| Filenames | `{cvName}_1.docx`, `_2`, … (not company-based) |
| Keep / delete | **Applied** keeps draft; **Skipped** deletes drafts for that job |
| Layout | Per-line budgets from swap-out slot; in-place `python-docx` on a **copy** |
| Repair | Call 1 → lock passing fields → Call 2 (failed only) → word-trim → draft |
| Out of scope | Auto-run; **Gmail/send cancelled**; same-project text refresh deferred |


**Do not confuse with:** search-time `enrich_job` (analysis + swap *plans* only). Plans already persist; generation is the missing piece.

### Cancelled / deferred

| Item | Notes |
|------|--------|
| Send application (Gmail) | **Cancelled** — suggested CV download only |
| Real LinkedIn post URLs | Worker often uses `linkedin-post://` |
| Cancel run | Explicitly out of scope for now |
| Accuracy polish | `optimization/system-accuracy-improvements.md` |

**Frozen:** worker search loop unless listing contract changes. WebBridge versions locked (daemon `v1.10.0` + extension `1.11.3`).

---

## Flow (today → next)

```
Search → Start
  → cloud ReAct (backend) + Helper WebBridge tools
  → listings → rewrite display JD → prefilter
  → parallel application_subgraph (scores + keep/swap plans)
  → Applications: I applied / Not applying

NEXT (last product step):
  → user approves swaps on a job
  → tailor_cv → layout-preserving draft DOCX → preview/download
```

---

## Suggested CV — what “done” means

From the handoff doc (send cancelled):

1. Analysis never writes CV text or mutates the master CV.
2. `package_out` already stores multi-slot swap plans in analysis JSON.
3. `tailor_cv` runs **only** on explicit user action.
4. One model call for all approved slots (not one call per slot).
5. Swap keeps the **same slot location**: same # of title + bullets/paragraphs, each within original character budgets; in-place `.docx` replace so fonts/spacing stay.
6. Deterministic layout checks + draft storage; download suggested CV (no Gmail).

Implementation order:

```text
5. CV layout parser/contract (per-slot title + line/paragraph char budgets)
6. User approval API/UI on Applications/job detail
7. tailor_cv model call (text fits budgets)
8. Layout validation + in-place python-docx rewrite
9. Draft storage, preview, download
```
