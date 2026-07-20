# Building JobPilot: an Autopilot Job-Application Agent on Qwen Cloud

*Three-tier Autopilot: Qwen Cloud reasons on ECS while your Chrome stays personal*

*Submission story for the [Qwen Cloud Global AI Hackathon](https://qwencloud-hackathon.devpost.com/), Track 4: Autopilot Agent.*

## Inspiration

I’m an AI / software engineer. Like a lot of people who code, I wasn’t only looking for a job. I still had to keep learning, studying, and shipping skills while I searched. That made the job hunt feel twice as heavy.

I was spending hours finding roles, then more hours reshaping my CV for each one: dropping projects, swapping projects, rewriting bullets so the same work suddenly “matched” a new job description. The frustrating part was not that my projects were wrong. Often the project *did* fit. The pain was that the written description did not surface the techniques I actually used, or map cleanly to what that job asked for. So I edited again. And again. Every role became another round of manual surgery on the same evidence.

I got tired of that loop, and angry at tools that either left me alone with the grind or automated past my judgment. I wanted something that could search the kinds of sources I was already using, take my CV and GitHub projects, score the fit, suggest project swaps for that role, and only then generate a tailored CV after I checked and approved it.

That is why I built JobPilot with **Qwen Cloud**: an Autopilot Agent for developers, software engineers, and AI engineers that takes on the heavy work, but keeps the human gate where your story gets rewritten.

JobPilot is built for the Qwen Cloud Global AI Hackathon, **Track 4: Autopilot Agent**. Reasoning runs on **Qwen Cloud**, the backend is live on **Alibaba Cloud ECS**, and browsing stays in the user’s own Chrome so personal account sessions never have to live in a datacenter.

**Demo video:** https://youtu.be/68JRJRgvfm8  
**Repo:** https://github.com/HamzaFayaz/JobPilot  
**Live demo:** http://47.237.150.6

## What JobPilot is

JobPilot is a multi-tier agentic system:

1. You upload your CV and connect **GitHub** so JobPilot can import the projects that prove you can code.
2. You start a search from the web app.
3. A cloud orchestrator (LangGraph on ECS) coordinates a desktop **Search Helper**.
4. The Helper drives **LinkedIn Posts** in your logged-in Chrome via **Kimi WebBridge**.
5. Listings come back, get prefiltered, then **per-job application agents** score the match and propose CV keep/swap plans.
6. You approve swaps, then JobPilot generates a **suggested CV** `.docx` that **follows your uploaded CV’s structure** and **does not overwrite or alter your master CV**.

It is not “send 500 emails.”

## Track 4 fit

Track 4 asks for an Autopilot that can handle ambiguous inputs, call external tools, stop for a human at critical decisions, and finish a real workflow. JobPilot does that as **search → score → approve → suggested CV**. Messy hiring posts are the first beachhead, not a claim that the product ends there.

## The design rule: agents propose, humans decide

The product rule I refused to break:

**Analysis never writes final CV text into your master file. Suggested CV runs only after explicit approval.**

That sounds obvious until you see tools quietly rewrite a user’s CV without a clear approval step. For JobPilot:

- Qwen proposes keep/swap plans per job
- the UI shows current vs suggested clearly
- the user approves
- only then does `tailor_cv` generate a layout-preserving `.docx` draft

That HITL gate is the Autopilot “trust dial.” Agents can be aggressive in search and scoring. Humans stay in control where identity and reputation matter.

## Where Qwen Cloud does the thinking

JobPilot is not “a UI with a model sprinkled on.” **Qwen Cloud** is the reasoning layer on ECS, reached through DashScope’s OpenAI-compatible API:

`https://dashscope-intl.aliyuncs.com/compatible-mode/v1`

That compatibility mattered: orchestration could stay clean while every serious reasoning step still ran on Qwen.

In JobPilot, Qwen’s abilities show up in different jobs:

- **Tool-using search:** as a cloud ReAct agent, Qwen decides what to click and extract on LinkedIn Posts; **Kimi WebBridge** (via the Helper) only executes those actions in Chrome
- **Understanding a developer:** skill extraction from the uploaded CV, so the profile is structured for matching
- **Judging fit:** per-job scoring and match summaries against CV + GitHub evidence
- **Rewriting with evidence:** keep/swap plans that pull the right project proof for *this* role, not generic fluff
- **Drafting under control:** suggested CV text after human approval (`tailor_cv`)
- **Retrieval support:** embeddings and rerank so we fetch relevant chunks instead of pasting whole repos into the prompt

The important product choice: **Qwen keys never leave ECS**. The Helper is for browser hands, not for holding the model secret.

**Right Qwen model for the job.** JobPilot does not send every step to the same model. We match model strength to risk and difficulty:

- **`qwen-turbo`** for CV skill extraction: frequent setup work where speed and cost matter
- **`qwen3.7-plus`** for the cloud browser ReAct agent and project/evidence understanding: needs stronger tool reasoning without paying Max prices on every browser step
- **`qwen3.7-max`** for job scoring, keep/swap plans, requirement extraction, and suggested CV drafting: highest-stakes structured outputs that affect what the user may approve into a real `.docx`
- **`text-embedding-v4` + `qwen3-rerank`** for retrieval: find the right GitHub evidence first so Max sees relevant chunks, not whole repositories

Pattern: cheaper models for repeatable setup, stronger models for tools, **Max** when the answer can change a CV decision.

**What surprised me about Qwen.** The compatible-mode API made wiring boring in the best way, but the quality jump showed up in the hard parts: structured JSON scoring that stayed schema-valid often enough to trust in parallel jobs, and swap rewrites that actually pulled techniques from GitHub evidence instead of inventing fluffy bullets. When a response did break the contract, a single repair pass was usually enough. That combination (clean endpoint + strong structured output + recoverable failures) is what made Qwen Cloud feel like a real Autopilot brain, not just another chat API glued to a form.

That is the Qwen journey in JobPilot: one cloud brain, many structured roles, always behind clear contracts and a human gate where it counts.

## Feeding Qwen only what matters

Calling Qwen on every raw string would be expensive and noisy. JobPilot builds a focused profile, then sends the model only the evidence it needs.

**Profile first.** You upload a CV and connect GitHub. Qwen helps extract skills from the CV. GitHub projects become the proof layer: READMEs and evidence cards are chunked, embedded, and indexed so later matching can retrieve relevant pieces instead of stuffing whole repositories into a prompt.

**Cheap work before expensive work.** After search, a code-only prefilter normalizes listings, dedupes, and drops already-applied jobs with **no LLM cost**. Only the remaining jobs enter parallel application analysis.

**Per job, grounded in evidence.** Each application agent scores the fit, summarizes the match, and proposes keep/swap plans using retrieved GitHub project evidence. The same project can get a **completely different swap rewrite for different jobs**, because the rewrite follows that job’s requirements plus the relevant GitHub evidence, not a one-size-fits-all blurb. For example, one repo might stress multi-agent orchestration for an Autopilot-style role, then stress evaluation, retrieval, and evidence quality for an Applied ML role: same project, different story, because **Qwen Max** is rewriting from that job’s needs. Suggested CV generation runs later, and only after you approve swaps.

That is how we use Qwen Cloud as a sharp tool: retrieve what matters, skip what does not, and keep irreversible CV changes behind a human gate.

## Three-tier architecture (ECS, Helper, Chrome)

The architecture is the real product insight.

![JobPilot three-tier architecture: Qwen Cloud on Alibaba ECS, Search Helper on the user PC, and Kimi WebBridge in Chrome](https://raw.githubusercontent.com/HamzaFayaz/JobPilot/main/docs/architecture.png)

**Tier 1: Alibaba ECS (cloud)**  
React UI, FastAPI, LangGraph, SQLite, and all **Qwen Cloud** calls (browser ReAct, scoring, suggested CV). Secrets stay on the server.

**Tier 2: User PC (Search Helper)**  
A Windows Helper pairs to the account, polls a task queue, and executes browser tools. It is a thin, trusted local worker, not a place to put API keys for the default cloud-agent path.

**Tier 3: User Chrome**  
Kimi WebBridge in the user’s real logged-in session (home IP + cookies). A datacenter browser would fight that battle badly.

So the cloud thinks; the desktop acts; the browser stays human.

## The hard engineering: browser on the user’s PC

If you only run agents in the cloud, anything that needs a **personal account** becomes a bot story. Job search runs on the user’s identity: their LinkedIn session today, and later the same pattern can cover other personal surfaces (more job boards, personalized feeds, or outreach) without putting cookies or mailboxes inside a datacenter agent.

So JobPilot keeps the hands on the user’s PC.

**Qwen Cloud** runs the browser ReAct brain on ECS. The **Search Helper** claims the task and drives **Kimi WebBridge** in the user’s logged-in Chrome. Listings return to the cloud for prefilter, scoring, and the human-approved CV path.

For this hackathon submit, that personal-session loop is live for **LinkedIn Posts**. The same three-tier idea is how you safely grow into more personal surfaces later without putting the user’s cookies and mailbox inside a datacenter agent.

JobPilot’s compromise:

- ECS owns orchestration, persistence, and Qwen calls
- the Helper owns Kimi WebBridge tool execution
- HTTP task queue + long-poll agent protocol connect them (no fragile WebSocket-only glue)

Pairing is explicit. The Helper claims a `browser_search` task, attaches to the cloud agent session, runs tools, and posts listings back. The parent graph waits, then continues into prefilter and parallel application subgraphs. The Helper is intentionally thin and scoped: it acts for the paired user only and executes browser tools, while Qwen keys and orchestration stay on ECS.

That split is the hard engineering: cloud intelligence, local hands, one Autopilot loop built around the user’s own accounts.

## Parallel analysis without breaking trust

Once listings return, JobPilot does not ask one giant prompt to “do everything.” Matched jobs fan out into **per-job application subgraphs in parallel**, so scoring and keep/swap plans can finish side by side.

Parallelism is for analysis. Trust is for drafts: the Applications inbox is where you review, and suggested CV stays a separate action after you approve swaps.

## Shipping on Alibaba Cloud ECS

For the hackathon, the backend also had to live on Alibaba Cloud, not only on a laptop. JobPilot’s live stack runs on Alibaba ECS with Docker Compose and Nginx. The Search Helper still runs on the user’s PC, because personal Chrome sessions cannot move to the datacenter.

## What almost broke (and what we locked)

A few scars worth sharing:

**1) Cloud brain vs local hands**  
Early designs blur “agent” and “browser.” Separating Qwen ReAct on ECS from WebBridge execution on the PC made failures debuggable: model issues vs extension/daemon issues vs network to ECS.

**2) Structured output is part of the product**  
Scoring and swaps only help if they arrive as valid JSON the graph can trust. We treat schema failures as expected: repair once, then fail that job cleanly instead of poisoning the whole run. That kept parallel analysis usable when one listing got a bad model response.

**3) Deploy is part of the Autopilot story**  
An agent graph that only runs locally is incomplete for this hackathon. Getting JobPilot onto Alibaba ECS forced the real split: Qwen and orchestration in the cloud, browser hands on the PC.

**4) Scope discipline**  
For this hackathon submit, the live search path is **LinkedIn Posts** plus scoring and suggested CV download. That is the first complete vertical slice. The three-tier design is built so more personal surfaces can plug into the same autopilot loop later.

## What I’d tell the next Qwen Cloud builder

If you are building an Autopilot Agent on Qwen Cloud this week:

1. **Put Qwen where the system of record lives** (your backend), not in every client.
2. **Use the compatible-mode endpoint** so your orchestration code stays boring and portable, then spend creativity on tools, state, and HITL.
3. **Separate reasoning from side effects.** Let Qwen plan and score; let deterministic code and humans own irreversible actions.
4. **Deploy early on Alibaba Cloud.** Your architecture diagram should match a URL judges can open.
5. **Write the trust rule first.** Decide what the agent must never do alone, then design the graph around that.

Those lessons are why this post exists: not only to show JobPilot, but to leave something reusable for the next builder on Qwen Cloud.

## Try it / links for judges

- **Demo video (2:49):** https://youtu.be/68JRJRgvfm8  
- **GitHub (MIT):** https://github.com/HamzaFayaz/JobPilot  
- **Live demo:** http://47.237.150.6  
- **Hackathon:** https://qwencloud-hackathon.devpost.com/

## Closing

I started this because I was burning hours on the same painful loop: find a role, then surgically rewrite project bullets so my real work finally matched the job. JobPilot is my Track 4 answer to that loop: Qwen Cloud does the reasoning, the Search Helper keeps personal browsing on my machine, and I still approve before a tailored CV exists.

Built with **Qwen Cloud** for reasoning, **Alibaba ECS** for the live backend, and a local Search Helper for Chrome.

Agents propose. Humans decide. That is the product.

Hamza Fayaz  
hamza.fayaz.ai@gmail.com
