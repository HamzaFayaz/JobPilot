# Currently Working On

**Status:** Applications inbox UI wired. Search starts a run → early `analyzing` job rows → WhatsApp-style Applications list + detail panel. Applied / Not applying stored on packages. No cancel. No tailored CV yet.

**Baseline:** Run 3 (~79/100). Evals off for product work; Logfire on (see `.env.example`).

---

## Start here (new chat)

### Done this slice `[x]`

| Area | Status |
|------|--------|
| Seed `analyzing` packages after prefilter | ✅ |
| `PATCH /api/jobs/{id}/decision` → applied / skipped | ✅ |
| Block second search while run active | ✅ |
| Applications page (list + detail) | ✅ |
| Progressive detail: JD while analyzing; scores/swaps when ready | ✅ |
| Search: disable Start during run; link to Applications | ✅ |
| Nav unlock + complete profile → Applications | ✅ |
| No post URL in UI | ✅ |
| No cancel | ✅ (deferred) |

### Still later

| Item | Notes |
|------|--------|
| Suggested CV text generation | Analysis plans only today |
| Real LinkedIn post URLs | Worker often uses `linkedin-post://` |
| Cancel run | Explicitly out of scope for now |
| Accuracy polish | `optimization/system-accuracy-improvements.md` |

**Frozen:** worker search loop unless listing contract changes.

---

## Flow

```
Search → Start (disabled while active)
  → worker listings → prefilter → seed analyzing packages
  → parallel application_subgraph per job
  → package ready/failed (UI polls Applications)
  → I applied / Not applying
```
