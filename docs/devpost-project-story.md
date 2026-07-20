## Inspiration

I’m an AI / software engineer. While job hunting I still had to keep learning and shipping, so the search felt twice as heavy. The worst loop was not finding roles. It was surgically rewriting the same CV for each one: dropping projects, swapping projects, rewriting bullets so real work finally “matched” a new job description.

Often the project *did* fit. The written description just did not surface the techniques I used. Tools either left me alone with that grind or automated past my judgment. I wanted an Autopilot that could search sources I already use, score fit against my CV + GitHub, propose project swaps, and only then generate a tailored CV **after I approve**.

That is why I built **JobPilot** with **Qwen Cloud** for Track 4: Autopilot Agent.

**Demo:** https://youtu.be/68JRJRgvfm8  
**Live:** http://47.237.150.6  
**Repo:** https://github.com/HamzaFayaz/JobPilot  
**Blog:** paste your Medium URL here

## What it does

JobPilot is a three-tier Autopilot for developers / SWE / AI engineers:

1. Upload CV + connect **GitHub** (project proof)
2. Start search from the web app
3. Cloud **LangGraph** on **Alibaba ECS** coordinates a desktop **Search Helper**
4. Helper drives **LinkedIn Posts** in your logged-in Chrome via **Kimi WebBridge**
5. Listings are prefiltered; **per-job agents** score fit and propose keep/swap plans
6. You approve swaps; JobPilot generates a **suggested CV** `.docx` that follows your CV layout and **does not overwrite your master CV**

Track 4 loop: **search → score → approve → suggested CV**. Agents propose. Humans decide.

## How we built it

**Qwen Cloud** is the reasoning layer on ECS via DashScope compatible-mode:

`https://dashscope-intl.aliyuncs.com/compatible-mode/v1`

We match model strength to risk:

- `qwen-turbo` — CV skill extraction
- `qwen3.7-plus` — cloud browser ReAct + evidence understanding
- `qwen3.7-max` — scoring, keep/swap plans, suggested CV drafting
- `text-embedding-v4` + `qwen3-rerank` — retrieve GitHub evidence instead of stuffing whole repos

**Architecture**

![JobPilot three-tier architecture](https://raw.githubusercontent.com/HamzaFayaz/JobPilot/main/docs/architecture.png)

- **Tier 1 — Alibaba ECS:** React, FastAPI, LangGraph, SQLite, all Qwen calls (keys stay on server)
- **Tier 2 — Search Helper (Windows):** pairs to the account, polls tasks, runs browser tools
- **Tier 3 — User Chrome:** Kimi WebBridge in the real logged-in session

Stack: React + TypeScript frontend, FastAPI backend, LangGraph parent + parallel application subgraphs, SQLite, Docker Compose + Nginx on ECS, local Helper for WebBridge.

## Challenges we ran into

1. **Cloud brain vs local hands** — Early designs blurred “agent” and “browser.” Separating Qwen ReAct on ECS from WebBridge on the PC made failures debuggable.
2. **Structured output under parallel load** — Scoring/swaps only help as valid JSON. We repair once, then fail that job cleanly so one bad listing does not poison the run.
3. **Personal sessions cannot live in a datacenter** — LinkedIn (and later other personal surfaces) need the user’s Chrome. That forced the Helper + task-queue design.
4. **Deploy is part of Autopilot** — A laptop-only graph is incomplete for this hackathon. Shipping on Alibaba ECS locked the real three-tier split.

## Accomplishments that we're proud of

- End-to-end Autopilot: search → parallel analysis → HITL → suggested CV
- Qwen keys never leave ECS; Helper is hands only
- Right Qwen model for each job (turbo / plus / max / embeddings+rerank)
- Live demo on Alibaba ECS with public repo (MIT)
- Hard rule: suggested CV only after explicit approval

## What we learned

- Put Qwen where the system of record lives (backend), not in every client
- Use compatible-mode so orchestration stays boring; spend creativity on tools, state, and HITL
- Separate reasoning from irreversible side effects
- Deploy early on Alibaba Cloud so the architecture diagram matches a URL judges can open
- Write the trust rule first, then design the graph around it

## What's next for JobPilot

Keep the same three-tier loop and grow personal surfaces carefully (more job boards / feeds / outreach) without putting cookies or mailboxes inside a datacenter agent. Sharpen retrieval and swap quality with more GitHub evidence. Keep the HITL gate where identity and reputation matter.
