# JobPilot — Product Requirements Document (PRD)

**Version:** 1.0
**Date:** June 27, 2026
**Track:** Global AI Hackathon Series with Qwen Cloud — Track 4: Autopilot Agent
**Deadline:** July 9, 2026

---

## 1. Project Name

**JobPilot**

---

## 2. What Is JobPilot?

JobPilot is a browser-controlling multi-agent job search autopilot built for developers. It takes over the entire job application process — from searching listings to sending tailored emails — with the user only stepping in to approve before anything is sent.

The user connects their GitHub, uploads their CV, picks their target role and platforms, and JobPilot does the rest: it opens their browser, searches jobs in real time, scores each one against their skills, rewrites the relevant CV section for that specific job, drafts a personalized application email, and sends it — all with a human approval gate before anything goes out.

---

## 3. The Problem JobPilot Solves

Job searching for developers in 2026 is a full-time job on top of a full-time job.

A serious search means:

- Scanning multiple platforms (LinkedIn, Indeed, Wellfound, RemoteOK) every day
- Reading each JD carefully to decide if it is worth applying
- Checking if your CV is even strong enough for that specific role
- Rewriting your CV or swapping projects for different JD targets
- Drafting a unique, personalized cover email — not a template
- Repeating this 10 to 20 times per day to get any traction

Most developers either apply with the same generic CV to everything (low conversion) or spend hours tailoring each application manually (unsustainable). There is no middle path that is both high-quality and high-volume.

**JobPilot is that middle path.** It brings the intelligence of a careful manual application to the volume of a bulk spray-and-pray campaign — with a human in the loop before anything is sent.

---

## 4. Who Is This For?

- Developers actively job searching who want quality applications at scale
- Engineers targeting remote-first or international roles across multiple platforms
- Anyone who has built projects on GitHub but struggles to translate them into tailored applications quickly

---

## 5. What JobPilot Does — End to End

### Step 1: Onboarding

- User connects GitHub — agent scans repositories and presents a list; user selects which projects to include in their profile
- User uploads their CV (PDF or DOCX)
- User selects target role, platforms (LinkedIn, Indeed, Wellfound, etc.), and regions

### Step 2: Browser Takeover

- Agent takes control of the user's existing Chrome browser via Browser-Use
- Opens tabs, navigates to selected job platforms, searches for the target role in real time
- Operates inside the user's actual logged-in sessions — no separate login required

### Step 3: Job Scoring

- Scoring sub-agent reads each job listing
- Evaluates the JD against the user's skills, experience, and selected GitHub projects
- Returns a match score and flags the strongest fits

### Step 4: CV Optimization Check

- CV optimization sub-agent compares the user's current CV to the JD
- Decides if the CV is strong enough as-is, or if a project swap would improve the match
- If a swap is needed, identifies which project to replace and with which alternative (Variant A / Variant B logic, word-count aware)

### Step 5: Human-in-the-Loop Gate

- Agent surfaces the job listing, match score, and proposed CV change to the user
- User approves or rejects before anything is written or sent

### Step 6: CV Rewrite

- On approval, agent rewrites the relevant CV section for that specific job
- Keeps tone, structure, and word count consistent with the rest of the document

### Step 7: Email Draft and Send

- Agent drafts a personalized application email tied to the specific JD and company
- Email is sent via Gmail API — not through Gmail.com in the browser
- CV is attached programmatically as a base64 attachment
- User gives final approval before send

---

## 6. Technical Architecture

### 6.1 Architecture Overview

```
User's Machine
├── Chrome Browser (user's real logged-in session)
│   └── Browser-Use controls this via local CDP
└── Browser-Use local agent (Python)

Alibaba Cloud ECS (mandatory deployment)
├── JobPilot FastAPI backend
├── LangGraph multi-agent orchestration
├── Qwen model via Dashscope API
└── Gmail API integration

GitHub API
└── Repository scanner at onboarding

Google Console
└── Gmail API (OAuth2) for sending emails
```

### 6.2 Agent Architecture (LangGraph)

| Sub-Agent | Role |
|---|---|
| Orchestrator Agent | Controls the overall flow, routes tasks between sub-agents |
| Browser Agent | Drives Browser-Use to navigate and extract job listings |
| Scoring Agent | Evaluates each JD against user profile and assigns a match score |
| CV Optimization Agent | Checks CV fit, decides project swap if needed |
| Email Drafting Agent | Writes a personalized application email per JD |
| HITL Gate | Surfaces decisions to the user before any action is taken |

### 6.3 Browser Control Layer

**Tool:** Browser-Use (Python, open source, 95k+ GitHub stars)

- Native Python SDK — LangGraph calls it directly, no bridge needed
- CLI 2.0 syncs the user's real Chrome profile including cookies and active sessions
- Built-in CAPTCHA solving: Cloudflare Turnstile, PerimeterX, reCAPTCHA
- Operates inside the user's real logged-in LinkedIn and Indeed sessions
- No headless browser — runs in the user's actual Chrome window on their machine
- Antibot risk is minimal because LinkedIn sees a real Chrome session from a real residential IP

### 6.4 Email Sending Layer

**Tool:** Gmail API via Google Console (OAuth2)

- User completes a one-time OAuth2 consent flow at onboarding
- Refresh token stored securely in backend
- Agent calls `gmail.users.messages.send` with CV attached as base64
- No browser automation of Gmail.com — eliminates the risk of tab conflicts, file upload dialog issues, and Gmail antibot triggers
- CV file is stored in Alibaba OSS after upload at onboarding; agent fetches and attaches per send

### 6.5 LLM Layer

**Model:** Qwen (via Alibaba Dashscope API — required by hackathon)

- API base URL: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
- OpenAI-compatible interface — drop-in with LangChain/LangGraph
- Powers all sub-agents: scoring, CV optimization, email drafting, orchestration

### 6.6 GitHub Integration

**Tool:** GitHub REST API

- Scans user's public repositories at onboarding
- Extracts repo name, description, language, and README summary
- User selects which projects to include in their active profile
- Agent uses this context in both the scoring and CV optimization steps

---

## 7. Technology Stack

| Layer | Technology |
|---|---|
| Agent Orchestration | LangGraph |
| LLM | Qwen (Dashscope, OpenAI-compatible) |
| Backend Framework | FastAPI |
| Browser Control | Browser-Use (Python SDK) |
| Browser Protocol | Chrome DevTools Protocol (CDP) via Browser-Use |
| Email Sending | Gmail API (Google Console, OAuth2) |
| File Storage | Alibaba OSS (CV storage) |
| GitHub Integration | GitHub REST API |
| Deployment | Alibaba Cloud ECS (mandatory) |
| Language | Python |

---

## 8. Human-in-the-Loop (HITL) Design

JobPilot never takes a consequential action without user approval. The HITL gate fires at two points:

1. **Before CV rewrite** — user sees the job listing, match score, and proposed project swap
2. **Before email send** — user sees the final email draft and attached CV

The user can approve, reject, or edit at each gate. If rejected, the agent moves to the next job in the queue.

This design means the user stays in control of their reputation. Nothing goes out that they have not read.

---

## 9. Key Constraints and Decisions

| Decision | Rationale |
|---|---|
| Browser-Use over Kimi WebBridge | Browser-Use has a native Python SDK, MCP server, and built-in CAPTCHA solving. WebBridge requires a custom bridge layer to connect to a Python backend — too much build time for a 12-day sprint. |
| Gmail API over browser-based Gmail | Automating Gmail.com creates tab conflicts, file upload dialog issues, and antibot risk. Gmail API is direct, reliable, and keeps the browser layer focused on job platforms only. |
| Real Chrome session (not headless) | LinkedIn blocked 23.5M automated sessions in Q1 2026. Headless browsers expose TLS fingerprint mismatches and missing browser attributes. Running inside the user's real Chrome session avoids all detection layers. |
| Agent logic on Alibaba ECS, browser on local machine | Agent decisions run in the cloud as required by the hackathon. Browser actions run locally so LinkedIn sees a real residential IP and a real Chrome environment. |
| Qwen via Dashscope | Mandatory for the hackathon. OpenAI-compatible interface means zero friction with LangGraph. |

---

## 10. Hackathon Scope (MVP)

For the July 9 deadline, the MVP covers:

- Onboarding: GitHub connect, CV upload, role and platform selection
- Browser control: LinkedIn and Indeed job search via Browser-Use
- Scoring sub-agent: match score per JD
- CV optimization sub-agent: project swap recommendation
- HITL gate: approval before rewrite and before send
- CV rewrite: targeted section rewrite per JD
- Email drafting and sending: personalized email via Gmail API with CV attached

Out of scope for MVP (post-hackathon):

- Multi-user support and authentication
- Dashboard / application tracking UI
- Support for platforms beyond LinkedIn and Indeed
- Resume version history
- ATS score integration

---

## 11. Blog Post Award (Parallel Target)

A dev.to blog post is being written in parallel with the build for the Blog Post Award ($500 cash + $500 credits, 10 winners across all tracks).

The post covers:

- Why browser-controlling agents are the next frontier for job search automation
- How the multi-agent architecture is designed and why each sub-agent is separate
- The Browser-Use vs Kimi WebBridge decision and what we learned
- Why Gmail API beats browser automation for email sending
- The antibot problem and how running inside a real Chrome session solves it

The post is written as the project is built — not after — so it captures real decisions, real tradeoffs, and real code.

---

*Document prepared for internal use during the Global AI Hackathon Series with Qwen Cloud, Track 4: Autopilot Agent.*
