# JobPilot — Product Requirements Document (PRD)

**Status:** Full product vision (problem + architecture + roadmap).  
**Shipped hackathon path only:** [`jobpilot_prd_mimimum.md`](./jobpilot_prd_mimimum.md)  
**Live product snapshot:** [`README.md`](./README.md)

**Version:** 2.0  
**Updated:** July 20, 2026  
**Track:** Global AI Hackathon Series with Qwen Cloud — Track 4: Autopilot Agent  
**Live demo:** http://47.237.150.6  
**Repo:** https://github.com/HamzaFayaz/JobPilot

---

## 1. Project name

**JobPilot**

---

## 2. What is JobPilot?

JobPilot is a multi-tier Autopilot Agent for people who code (developers, software engineers, AI engineers). It scouts hiring signals using the user’s real browser session, scores fit against their CV and GitHub projects, proposes per-job project keep/swap plans, and generates a tailored CV draft only after human approval.

It is **not** bulk spam and **not** a chat box with an API key. Cloud **Qwen** reasons on Alibaba ECS; a desktop **Search Helper** drives **Kimi WebBridge** in the user’s Chrome (or Edge) so personal accounts stay on the user’s machine.

**Beachhead vs destination:** The first complete vertical slice is **LinkedIn Posts → score → HITL suggested CV**. The product goal is broader: any hiring surface that needs the user’s personal account (more boards, later Gmail-assisted outreach, Indeed-style personalized feeds), using the same three-tier loop.

---

## 3. The problem JobPilot solves

Job search for people who code is a bad tradeoff on top of learning and shipping work.

A serious search means:

- Finding roles across messy sources (posts, boards, referrals), not only clean job-board rows  
- Reading each JD carefully  
- Checking whether CV + projects are strong enough for that specific role  
- Rewriting project bullets so real techniques map to the JD (often the project fits, but the write-up does not)  
- Repeating that surgery for every role  

Most people either apply with one generic CV (low conversion) or spend hours tailoring by hand (unsustainable).

**JobPilot is the middle path:** agentic scout + score + draft, with a human gate before any tailored CV becomes a real document.

---

## 4. Who is this for?

- Developers, software engineers, and AI engineers actively searching  
- People with GitHub work who struggle to turn projects into per-role CV stories quickly  
- Users who want quality applications with control, not unsupervised send bots  

---

## 5. Product principles

1. **Human-in-the-loop** — user approves swaps before suggested CV generation  
2. **Personal browser sessions** — LinkedIn (and later other accounts) use the user’s Chrome, not datacenter bots  
3. **Server-side secrets** — Qwen keys stay on ECS  
4. **Scoped Search Helper** — paired user only; browser tools only; no model keys on the default cloud path  
5. **Evidence over fluff** — GitHub projects are chunked/retrieved so swaps are grounded  
6. **Right Qwen model for the job** — turbo / plus / max / embeddings+rerank by risk (see `config/llm.yaml`)  

---

## 6. End-to-end product (vision)

### 6.1 Shipped now (see minimum PRD)

- Multi-user accounts  
- CV upload + GitHub import + evidence index  
- Search Helper + Kimi WebBridge  
- LinkedIn Posts search (cloud Qwen ReAct)  
- Prefilter + parallel application analysis  
- HITL Applications inbox  
- Suggested CV download (layout-preserving `.docx`, master CV unchanged)  
- Deploy on Alibaba ECS  

### 6.2 Next surfaces (same architecture)

| Surface | Intent | Status |
|---------|--------|--------|
| LinkedIn Posts | Ambiguous hiring posts | **Shipped** |
| LinkedIn Jobs / Indeed / other boards | Broader inventory + personalized feeds | Deferred |
| Gmail draft / send | Outreach with user’s mailbox | Cancelled for hackathon submit; future optional |
| More HITL gates | e.g. before any outbound send | Future when send returns |

Design rule for expansion: anything that needs a **personal account** stays on the user’s PC via Helper + WebBridge; Qwen and orchestration stay on ECS.

---

## 7. Technical architecture (current)

### 7.1 Three tiers

```
Tier 1 — Alibaba ECS
  React · FastAPI · LangGraph · SQLite · Qwen Cloud (DashScope)

Tier 2 — User PC
  Search Helper: pair, poll tasks, execute WebBridge tools

Tier 3 — User browser
  Kimi WebBridge daemon + extension · real LinkedIn session
```

### 7.2 LangGraph (code-routed)

Parent: `init_run` → `search_subgraph` → `prefilter` → parallel `application_subgraph` → persist.  
Suggested CV is **outside** the parent graph: explicit user approve → `tailor_cv`.

### 7.3 Browser control

**Tool:** Kimi WebBridge (not Browser-Use).  
Cloud Qwen ReAct decides tools; Helper executes them locally.

### 7.4 LLM layer

**Qwen Cloud** via `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`  
Tiered models in [`config/llm.yaml`](./config/llm.yaml): turbo (profile), plus (browser agent / evidence), max (scoring, swaps, tailor_cv), embeddings + rerank (retrieval).

### 7.5 GitHub integration

OAuth + import: projects, evidence cards, chunking, FAISS index for per-job retrieval.

---

## 8. HITL design

Consequential CV mutation never happens silently.

1. Analysis proposes keep/swap plans (Qwen)  
2. User reviews in Applications UI  
3. User approves selected swaps  
4. Only then `tailor_cv` builds a suggested `.docx`  
5. Master CV remains unchanged; user downloads a draft  

Future outbound send (if reintroduced) must add another explicit gate before anything leaves the user’s name.

---

## 9. Key decisions (current)

| Decision | Rationale |
|----------|-----------|
| Kimi WebBridge over Browser-Use | Real Chrome/Edge session; no profile-copy pain; Helper stays thin |
| Qwen ReAct on ECS, tools on PC | Hackathon/cloud brain + personal IP/session |
| LinkedIn Posts first | Hardest ambiguous inputs; proves Track 4 |
| No Gmail in submit path | Complete thin slice: search → score → suggested CV |
| Tiered Qwen models | Cost/latency vs quality by risk |
| Layout-preserving suggested CV | Trust: structure matches uploaded CV |

---

## 10. Hackathon submit checklist (pointer)

Use [`jobpilot_prd_mimimum.md`](./jobpilot_prd_mimimum.md) and [`docs/hackathon-submission-handoff.md`](./docs/hackathon-submission-handoff.md) for the exact shipped scope, live demo notes, and Devpost packaging.

Blog prize: Medium journey building with Qwen Cloud (see [`docs/medium-blog-draft.md`](./docs/medium-blog-draft.md)).

---

*PRD v2.0 replaces earlier drafts that listed Browser-Use, Gmail send as MVP, and Indeed as current submit scope.*
