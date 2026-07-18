# Currently Working On

**Status:** Product path through Applications is live. **Next (last major product step before send):** user-triggered **tailored CV** (`tailor_cv`) from persisted swap plans.

**Baseline:** Run 3 (~79/100). Evals off for product work; Logfire on (see `.env.example`).

**Canonical design for next work:**  
[`docs/discussion/enrich-job-to-cv-tailoring-handoff.md`](docs/discussion/enrich-job-to-cv-tailoring-handoff.md)

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

### Next — tailored CV `[o]` **last step**

| Item | Notes |
|------|--------|
| **`tailor_cv` (user-triggered)** | Not in the search graph. User opens a job → reviews keep/swap plans → **Generate tailored CV** |
| Inputs | Job package + approved swaps + CV layout contract + selected project evidence/chunks |
| Output | New **draft** `.docx` (never overwrite master CV); preview → confirm/download |
| Layout | Same slot/bullet counts + character budgets; validate after generation |
| Out of scope for this step | Auto-run on every job; Gmail send (separate later HITL) |

**Do not confuse with:** search-time `enrich_job` (analysis + swap *plans* only). Plans already persist; generation is the missing piece.

### Still later / deferred

| Item | Notes |
|------|--------|
| Send application (Gmail) | Separate HITL after tailored CV exists |
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

NEXT (last product step before send):
  → user approves swaps on a job
  → tailor_cv → draft DOCX preview → confirm/download
```

---

## Tailored CV — what “done” means

From the handoff doc:

1. Analysis never writes CV text or mutates the master CV.
2. `package_out` already stores multi-slot swap plans in analysis JSON.
3. `tailor_cv` runs **only** on explicit user action.
4. One model call for all approved slots (not one call per slot).
5. Deterministic layout checks + draft storage; second confirm for download.
6. Sending remains a **separate** later action.

Implementation order (handoff § Implementation order, steps 5–9):

```text
5. CV layout parser/contract
6. User approval API/UI on Applications/job detail
7. tailor_cv model call
8. Layout validation
9. Draft storage, preview, download
```
