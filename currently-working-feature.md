# Currently Working On

**Status:** Hackathon product build **complete** (Track 4 — Autopilot Agent). Live on Alibaba ECS.

**Baseline:** Run 3 (~79/100). Evals off for product work.

**Live demo:** [http://47.237.150.6](http://47.237.150.6)  
**Contact:** [hamza.fayaz.ai@gmail.com](mailto:hamza.fayaz.ai@gmail.com)

---

## Start here (new chat)

### Done — hackathon product path `[x]`

| Area | Status |
|------|--------|
| Search → worker → prefilter → parallel application analysis | ✅ |
| Applications inbox + decisions | ✅ |
| Dual JD: raw `description_text` for analysis; display rewrite for UI | ✅ |
| Cloud browser agent (Qwen ReAct on backend; Helper = WebBridge only) | ✅ |
| Background GitHub import (projects until overview/evidence/index ready) | ✅ |
| Suggested CV (`tailor_cv`) — approve swaps → generate → download draft | ✅ |
| Search Helper `.exe` + CV template downloads; Windows SmartScreen note | ✅ |
| Alibaba ECS deploy (EIP `47.237.150.6`) | ✅ |

### Next — submission packaging `[ ]`

| Item | Notes |
|------|--------|
| **Demo video** | End-to-end walkthrough for judges |
| **Blog post** | Architecture + Qwen usage + three-tier design |
| Optional | Judge feedback polish |

### Cancelled / deferred

| Item | Notes |
|------|--------|
| Send application (Gmail) | **Cancelled** — suggested CV download only |
| Indeed / LinkedIn Jobs | Deferred — LinkedIn Posts only for hackathon |
| Windows code-signing cert | Deferred — Settings explains SmartScreen |

**Frozen:** worker search loop unless listing contract changes. WebBridge versions locked (daemon `v1.10.0` + extension `1.11.3`).

---

## Flow (shipped)

```
Search → Start
  → cloud ReAct (backend) + Helper WebBridge tools
  → listings → rewrite display JD → prefilter
  → parallel application_subgraph (scores + keep/swap plans)
  → Applications: I applied / Not applying
  → approve swaps → tailor_cv → download suggested .docx
```

---

## Principles (unchanged)

1. Analysis never writes CV text or mutates the master CV.
2. `tailor_cv` runs only on explicit user action.
3. Human-in-the-loop before drafts are kept (Applied keeps; Skipped deletes).
