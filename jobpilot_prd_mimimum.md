# JobPilot — Minimum PRD (hackathon / shipped path)

**Status:** Source of truth for what is **shipped now** for the Qwen Cloud hackathon submit.  
**Full product vision:** [`jobpilot_prd.md`](./jobpilot_prd.md)  
**Product snapshot:** [`README.md`](./README.md) · [`currently-working-feature.md`](./currently-working-feature.md)

**Version:** 2.0 (aligned to live product)  
**Updated:** July 20, 2026  
**Track:** Qwen Cloud Global AI Hackathon — Track 4: Autopilot Agent  
**Live demo:** http://47.237.150.6  
**Repo:** https://github.com/HamzaFayaz/JobPilot

---

## Purpose of this document

This minimum PRD describes the **current end-to-end path judges can run**, not the long-term roadmap. LinkedIn Posts is the first beachhead because hiring posts are ambiguous and need a real browser session. It is not a claim that JobPilot is “LinkedIn-only forever.”

---

## Problem (developer-focused)

Developers, software engineers, and AI engineers must find roles while still learning and shipping. The painful loop is:

1. Search hiring signals for hours  
2. For each role, reshape the CV: drop/swap projects, rewrite bullets so real work maps to the JD  
3. Often the project *fits*, but the written description does not show the techniques or requirements — so they edit again by hand  

JobPilot’s shipped answer: scout → score against CV + GitHub evidence → suggest per-job swaps → generate a suggested CV **only after human approval**.

---

## Who it is for (now)

- Developers / software engineers / AI engineers who can code  
- Users with a CV (`.docx`) and GitHub projects as evidence  

---

## Shipped end-to-end flow

1. **Account** — signup / login (multi-user, JWT)  
2. **Profile** — upload CV (`.docx`); Qwen extracts skills; connect GitHub; import projects (overview, evidence, chunk index)  
3. **Search Helper** — pair desktop Helper; Kimi WebBridge in logged-in Chrome; Qwen keys stay on ECS  
4. **Search** — start LinkedIn **Posts** search from the web app (cloud Qwen ReAct + local WebBridge tools)  
5. **Prefilter** — normalize, dedupe, drop already-applied (no LLM)  
6. **Parallel analysis** — per-job application subgraphs: score, match summary, keep/swap plans grounded in GitHub evidence  
7. **HITL** — Applications inbox; user reviews; approves swaps  
8. **Suggested CV** — `tailor_cv` generates layout-preserving `.docx`; does **not** overwrite master CV; user downloads draft  

Live UI caps selectable jobs at **8** on the current ECS size (`ecs.e-c1m2.xlarge`, 4 vCPU · 8 GiB) for shared-demo stability — not an architecture limit.

---

## In scope (keep)

| Capability | Notes |
|------------|--------|
| Kimi WebBridge + Chrome (or Edge) | Real session / home IP |
| LinkedIn **Posts** search | Ambiguous hiring posts |
| Cloud Qwen ReAct on ECS | Helper executes tools only |
| GitHub project import + evidence index | Required evidence base |
| Code prefilter | No LLM cost |
| Parallel per-job scoring + keep/swap | Qwen Max for high-stakes steps |
| HITL before suggested CV | Approve swaps → generate → download |
| Layout-preserving suggested `.docx` | Master CV unchanged |
| Alibaba ECS deploy | Docker + GitHub Actions |
| Multi-user isolation | Per-user data |

---

## Out of scope for this minimum (deferred / cancelled)

| Capability | Status |
|------------|--------|
| Gmail draft/send | Cancelled for submit (suggested CV download only) |
| Indeed / LinkedIn Jobs boards | Deferred |
| Windows code-signing for Helper `.exe` | Deferred (SmartScreen note in UI) |
| Claiming “all platforms live” | Do not advertise as shipped |

---

## Architecture (shipped)

```
Tier 1 — Alibaba ECS
  React · FastAPI · LangGraph · SQLite · Qwen Cloud (DashScope)

Tier 2 — User PC
  JobPilot Search Helper (pair, poll tasks, WebBridge executor)

Tier 3 — User browser
  Kimi WebBridge + LinkedIn session (home IP)
```

Qwen API: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`  
Models by call site: [`config/llm.yaml`](./config/llm.yaml)

---

## HITL rule (non-negotiable)

Analysis never writes final CV text into the master file. Suggested CV runs only after explicit user approval of swaps.

---

## Success for hackathon submit

- Public MIT repo + live ECS demo + demo video &lt; 3 min  
- Track 4 selected on Devpost  
- Alibaba proof via code file (prefer `.github/workflows/deploy.yml`)  
- Optional Medium blog for Blog prize  

*This file supersedes older “lean” tables that listed Gmail as in-scope and GitHub as cut.*
