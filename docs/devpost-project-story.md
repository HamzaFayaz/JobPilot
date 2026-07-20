## Inspiration

I’m an AI / software engineer. Job hunting while still learning and shipping felt twice as heavy. The worst part was not finding roles. It was rewriting the same CV for every job: swapping projects and bullets so real work finally “matched” a new description.

I wanted an Autopilot that searches sources I already use, scores fit against my CV + GitHub, proposes project swaps, and only generates a tailored CV **after I approve**. That is why I built **JobPilot** with **Qwen Cloud** for Track 4: Autopilot Agent.

## What it does

1. Upload CV + connect GitHub  
2. Cloud Qwen drives **LinkedIn Posts** search; a desktop Helper runs the clicks in your logged-in Chrome via Kimi WebBridge  
3. Cloud agents score each job and propose keep/swap plans  
4. You approve; JobPilot drafts a **suggested CV** `.docx` (same layout; does **not** overwrite your master CV)

Loop: **search → score → approve → suggested CV**. Agents propose. Humans decide.

## How we built it

Three tiers: **Alibaba ECS** (React, FastAPI, LangGraph, all Qwen calls) · **Search Helper** on Windows · **Chrome** for personal sessions.

Qwen via DashScope compatible-mode:

- `qwen-turbo`: CV skills  
- `qwen3.7-plus`: browser ReAct + evidence  
- `qwen3.7-max`: scoring, swaps, suggested CV  
- embeddings + rerank: GitHub evidence retrieval  

Qwen keys stay on ECS. Helper is browser hands only.

## Challenges we ran into

Separating cloud brain from local browser hands; keeping structured JSON reliable under parallel job analysis; shipping on Alibaba ECS so personal Chrome never had to live in a datacenter.

## Accomplishments that we're proud of

End-to-end Autopilot on Qwen Cloud + Alibaba ECS; HITL before any suggested CV; right model per step; public MIT repo + live demo.

## What we learned

Put Qwen on the backend. Separate reasoning from irreversible actions. Deploy early. Write the trust rule first, then the graph.

## What's next for JobPilot

I plan for JobPilot to work across a developer’s favorite job-hunting sites, not only LinkedIn Posts. Because JobPilot is built for developers, users should be able to customize which sources and surfaces they use, while the same three-tier loop stays: Qwen reasons in the cloud, the Helper acts in their Chrome, and they still approve before any suggested CV.
