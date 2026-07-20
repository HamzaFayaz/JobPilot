<!--
MEDIUM PASTE INSTRUCTIONS
1. Medium → Write a story
2. Title = first line below (Building JobPilot…)
3. Select from "## The job-search problem" through the end → Copy → Paste into Medium
4. Fix any broken headings/links once
5. Optional cover: docs/architecture.png
6. Publish Public → paste Medium URL on Devpost Blog field
Delete this comment block before publishing (or just don't copy it).
-->

# Building JobPilot: an Autopilot Job-Application Agent on Qwen Cloud

*Submission story for the [Qwen Cloud Global AI Hackathon](https://qwencloud-hackathon.devpost.com/) — Track 4: Autopilot Agent.*

Job search for developers is broken in two opposite ways.

Do it by hand and you stay accurate — but you drown in LinkedIn posts, tabs, and “I’ll tailor the CV later.” Blast applications with bulk automation and you move fast — but conversion drops, platforms get hostile, and you lose control over what goes out with your name on it.

I wanted the middle path: an **autopilot** that can scout, score, and draft — with a **human checkpoint** before anything becomes a real tailored CV.

That project is **JobPilot**. I built it for Track 4 (Autopilot Agent) on **Qwen Cloud**, deployed the backend on **Alibaba Cloud ECS**, and kept the browser on the user’s own Chrome — because that’s where LinkedIn sessions actually live.

**Demo video:** https://youtu.be/68JRJRgvfm8  
**Repo:** https://github.com/HamzaFayaz/JobPilot  
**Live demo:** http://47.237.150.6

---

## The job-search problem nobody automates well

Hiring posts are messy. A LinkedIn post is not a clean job board row. It might be a recruiter shout-out, a founder hiring note, or a half-complete role description with the real requirements buried in comments.

A useful autopilot has to:

- handle **ambiguous inputs**
- call **external tools** (a real browser, not a fake scrape)
- stop and ask a human at the **critical** moment
- feel **production-ready**, not like a weekend chat demo

That is exactly what Track 4 asks for. JobPilot is my answer for technical job search.

---

## What JobPilot is (Track 4 Autopilot)

JobPilot is a multi-tier agentic system:

1. You build a profile from a CV (and optionally GitHub).
2. You start a search from the web app.
3. A cloud orchestrator (LangGraph on ECS) coordinates a desktop **Search Helper**.
4. The Helper drives **LinkedIn Posts** in your logged-in Chrome via WebBridge.
5. Listings come back, get prefiltered, then **per-job application agents** score the match and propose CV keep/swap plans.
6. You approve swaps → JobPilot generates a **suggested CV** `.docx` — without overwriting your master CV.

It is not “send 500 emails.” It is **search → analyze → human-approved draft**.

---

## The design rule: agents propose, humans decide

The product rule I refused to break:

**Analysis never writes final CV text into your master file. Suggested CV runs only after explicit approval.**

That sounds obvious until you watch agent demos quietly mutate user data. For JobPilot:

- Qwen proposes keep/swap plans per job
- the UI shows current vs suggested clearly
- the user approves
- only then does `tailor_cv` generate a layout-preserving `.docx` draft

That HITL gate is the Autopilot “trust dial.” Agents can be aggressive in search and scoring. Humans stay in control where identity and reputation matter.

---

## Three-tier architecture (ECS · Helper · Chrome)

The architecture is the real product insight.

**Tier 1 — Alibaba ECS (cloud)**  
React UI, FastAPI, LangGraph, SQLite, and all **Qwen Cloud** calls (browser ReAct, scoring, suggested CV). Secrets stay on the server.

**Tier 2 — User PC (Search Helper)**  
A Windows Helper pairs to the account, polls a task queue, and executes browser tools. It is a thin, trusted local worker — not a place to put API keys for the default cloud-agent path.

**Tier 3 — User Chrome**  
Kimi WebBridge in the user’s real LinkedIn session. LinkedIn trusts home IP + cookies. A datacenter browser would fight that battle badly.

So the cloud thinks; the desktop acts; the browser stays human.

Architecture image in the repo: https://github.com/HamzaFayaz/JobPilot/blob/main/docs/architecture.png

---

## Where Qwen Cloud does the thinking

JobPilot is not “a UI with a model sprinkled on.” Qwen Cloud is the reasoning layer on ECS.

We use DashScope’s OpenAI-compatible endpoint:

`https://dashscope-intl.aliyuncs.com/compatible-mode/v1`

Config lives here:

- https://github.com/HamzaFayaz/JobPilot/blob/main/backend/app/config.py  
- https://github.com/HamzaFayaz/JobPilot/blob/main/config/llm.yaml  

In practice Qwen Cloud powers:

- **Cloud browser ReAct** — decide what to click/extract during LinkedIn Posts search (tools execute locally via the Helper)
- **Profile / skill extraction** from uploaded CVs
- **Per-job scoring + match summaries**
- **Keep/swap planning** for CV evidence
- **Suggested CV drafting** after approval
- **Embeddings / rerank** where the retrieval path needs them

The important engineering choice: **Qwen keys never ship in the frontend**. Judges and users pair a Helper; they do not paste DashScope secrets into the browser.

That split made the Autopilot feel like a real product: cloud intelligence + local hands.

---

## The hard engineering: browser on the user’s PC

If you only run agents in the cloud, LinkedIn search becomes a bot story.

If you only run everything on the laptop, you lose a clean multi-user backend, deploy story, and centralized model ops.

JobPilot’s compromise:

- ECS owns orchestration, persistence, and Qwen calls
- the Helper owns WebBridge tool execution
- HTTP task queue + long-poll agent protocol connect them (no fragile “hope the WebSocket survives” demo glue)

Pairing is explicit. The Helper claims a `browser_search` task, attaches to the cloud agent session, runs tools, and posts listings back. The parent graph waits, then continues into prefilter and parallel application subgraphs.

This is the part most “multi-agent dashboards” skip — and the part that makes Track 4 feel real.

---

## Parallel analysis without breaking trust

Once listings return, JobPilot does not ask one giant prompt to “do everything.”

Flow:

1. Normalize / dedupe / drop already-applied (cheap, no LLM)
2. Fan out **per-job application subgraphs** in parallel
3. Each job gets structured scoring + a keep/swap plan
4. The Applications inbox becomes the human workspace
5. Suggested CV is a separate, explicit action

That matters for cost, latency, and clarity. Parallelism is for analysis. Trust is for drafts.

---

## Shipping on Alibaba Cloud ECS

For the hackathon, “it runs on my laptop” was not enough. The backend had to live on Alibaba Cloud.

JobPilot’s live stack:

- Alibaba ECS (Singapore)
- Docker Compose (`web` + `api`)
- Nginx
- GitHub Actions deploy workflow: **Deploy to Alibaba ECS**

Proof and notes:

- https://github.com/HamzaFayaz/JobPilot/blob/main/System%20Design/alibaba-cloud-trial.md  
- https://github.com/HamzaFayaz/JobPilot/blob/main/.github/workflows/deploy.yml  
- https://github.com/HamzaFayaz/JobPilot/actions  

Live demo: http://47.237.150.6

**Live demo note for testers:** the live UI only allows selecting up to **8 jobs** per search. That matches the capacity of the current live server (`ecs.e-c1m2.xlarge` — 4 vCPU · 8 GiB) so the shared demo stays stable through judging. It is **not** a JobPilot architecture limit — on a larger server the same system can run more jobs in parallel.

---

## What almost broke (and what we locked)

A few scars worth sharing:

**1) Cloud brain vs local hands**  
Early designs blur “agent” and “browser.” Separating Qwen ReAct on ECS from WebBridge execution on the PC made failures debuggable: model issues vs extension/daemon issues vs network to ECS.

**2) Production deploy is half the hackathon**  
The agent graph can look “done” while Docker, env vars, and Actions still decide whether judges see a live product. We treated ECS deploy as a first-class feature, not a last-day screenshot.

**3) HITL must be structural**  
If “approve” is just a toast, users will not trust the system. Suggested CV is a real gate: no approve → no draft file.

**4) Scope discipline**  
For submit, we locked LinkedIn Posts + scoring + suggested CV download. Gmail send and other boards can wait. Autopilot credibility comes from a complete thin slice, not a wide incomplete surface.

---

## What I’d tell the next Qwen Cloud builder

If you are building an Autopilot Agent on Qwen Cloud this week:

1. **Put Qwen where the system of record lives** (your backend), not in every client.
2. **Use the compatible-mode endpoint** so your orchestration code stays boring and portable — then spend creativity on tools, state, and HITL.
3. **Separate reasoning from side effects.** Let Qwen plan and score; let deterministic code and humans own irreversible actions.
4. **Deploy early on Alibaba Cloud.** Your architecture diagram should match a URL judges can open.
5. **Write the trust rule first.** Decide what the agent must never do alone — then design the graph around that.

Those lessons are why this post exists: not only to show JobPilot, but to leave something reusable for the next builder on Qwen Cloud.

---

## Try it / links for judges

- **Demo video (2:49):** https://youtu.be/68JRJRgvfm8  
- **GitHub (MIT):** https://github.com/HamzaFayaz/JobPilot  
- **Live demo:** http://47.237.150.6  
- **Architecture:** https://github.com/HamzaFayaz/JobPilot/blob/main/docs/architecture.png  
- **Qwen API config:** https://github.com/HamzaFayaz/JobPilot/blob/main/backend/app/config.py  
- **Hackathon:** https://qwencloud-hackathon.devpost.com/

---

## Closing

JobPilot is my Track 4 bet: an autopilot for technical job search that can operate in the messy real world — ambiguous posts, real browsers, parallel analysis — while keeping a human in the loop before a tailored CV exists.

Built with **Qwen Cloud** for reasoning, **Alibaba ECS** for the live backend, and a local Search Helper for Chrome.

Agents propose. Humans decide. That is the product.

— Hamza Fayaz  
hamza.fayaz.ai@gmail.com

#QwenCloud #Hackathon #AutopilotAgent #LangGraph #AlibabaCloud #AIAgents #JobPilot
