# JobPilot — Hackathon submission handoff

**Use this file to continue in a new chat.**  
**Deadline:** Jul 20, 2026, 2:00 pm PT  
**Track:** Track 4 — Autopilot Agent  
**Live demo:** http://47.237.150.6  
**Repo:** https://github.com/HamzaFayaz/JobPilot  
**Contact:** hamza.fayaz.ai@gmail.com

Official rules summary (saved earlier): [`hackathon-official-rules-context.md`](./hackathon-official-rules-context.md)  
Source: [Devpost Official Rules](https://qwencloud-hackathon.devpost.com/rules) · local pack: [`Qwen Cloud Proof of Deployment.docx`](../Qwen%20Cloud%20Proof%20of%20Deployment.docx)

---

## Prizes we target (one submission)

| Prize | Amount | How |
|-------|--------|-----|
| Track 4 Autopilot grand | $7k cash + $3k credits | Main track win |
| Top 10 Honorable Mention | $500 + $500 credits | Same submission |
| Top 10 Blog Post | $500 + $500 credits | Needs public blog/social URL on Devpost |

Cap: one grand + up to one blog prize.

---

## Official Rules — required deliverables

| Requirement | Detail |
|-------------|--------|
| Public repo + OSS license | MIT — GitHub About must show it |
| Text description | Features + functionality |
| Alibaba Cloud proof | **Repo file link** (Official Rules) **and** Workbench/ECS **screenshot** (proof docx) |
| Architecture diagram | Clear system visual (we use PNG) |
| Demo video | **&lt; 3 minutes**; product working; public YouTube / Vimeo / Youku |
| Track | Select **Track 4** on Devpost |
| Testing access | Live site (credentials in Devpost if needed) |
| Optional blog | For Blog prize only |

**Judging (Stage Two):** Innovation 30% · Technical depth 30% · Problem value 25% · Presentation/docs 15%.

**Qwen API we use (correct):**  
`https://dashscope-intl.aliyuncs.com/compatible-mode/v1` + DashScope embeddings/rerank.  
Code: `backend/app/config.py` · models: `config/llm.yaml`.

---

## Complete (done)

- [x] Product build (search → analysis → HITL suggested CV)
- [x] Live on Alibaba ECS (`47.237.150.6`)
- [x] MIT `LICENSE` (GitHub shows MIT)
- [x] README hackathon block + required judge links (Qwen + Alibaba + Actions)
- [x] Technical depth section + Helper/session boundary
- [x] Main architecture PNG: [`docs/architecture.png`](./architecture.png) (in README; use for Devpost + video end)
- [x] Deploy workflow renamed **Deploy to Alibaba ECS** (`.github/workflows/deploy.yml`)
- [x] Alibaba proof docs updated (`System Design/alibaba-cloud-trial.md`)
- [x] Parent/subgraph Mermaid kept for detail (main diagram is the PNG)

---

## Next (do these)

### 1. Demo video (required) — priority

- [x] Recorded &amp; public: **https://youtu.be/68JRJRgvfm8** (2:49)

**Rules:** under **3 minutes** (aim **~2:00–2:45**). Judges need not watch past 3. Public **YouTube / Vimeo / Youku**. Show product **working**. Voice **not required** (English captions / on-screen text OK). No unlicensed music.

**Live demo note (README + Devpost):** Live UI hard-caps at **8 jobs** (cannot select more). Server: `ecs.e-c1m2.xlarge` (4 vCPU · 8 GiB) — capacity for stable judging; **not** a product architecture limit.

**Assets for the video**
| Asset | Use |
|-------|-----|
| Title / project card | Fullscreen slide or image: **JobPilot** · **Track 4 — Autopilot Agent** · **Qwen Cloud · Alibaba ECS** (PowerPoint Slide Show or similar — do **not** open README as the title) |
| End card | [`docs/architecture.png`](./architecture.png) only (~5–8s). Do **not** show parent/subgraph Mermaid diagrams in the video |
| Live site | `http://47.237.150.6` (after copying IP from ECS) |

**Before recording (prep)**
- Helper already installed; WebBridge ready (or use in-app **Watch setup video**: https://youtu.be/gYTl1co9FKQ)
- Prefer profile/CV already uploaded so you do not wait forever on GitHub import
- Can pause recording during long waits; cut dead time in the edit
- Skip Helper `.exe` download / SmartScreen / install in the **demo** video (setup video covers that separately)

**Step-by-step shot list (agreed)**

| # | Time (guide) | What to record | Notes |
|---|--------------|----------------|-------|
| 1 | 0:00–0:08 | **Title / project image** fullscreen | JobPilot · Track 4 Autopilot Agent · Qwen Cloud · Alibaba ECS. Screen-record the slide (~5–8s). |
| 2 | 0:08–0:20 | **Alibaba Cloud ECS** console | Show running instance + public IP. Copy IP. Keep short — one clear frame is enough. ECS is valid Alibaba proof. |
| 3 | 0:20–0:35 | New browser tab → open `http://&lt;IP&gt;` | Live app loads from ECS. |
| 4 | 0:35–0:55 | **Signup / login** | Short. Use a ready account if signup is slow. |
| 5 | 0:55–1:15 | **Profile / current CV** | Show current CV / profile is ready (upload only if quick). Do not linger. |
| 6 | 1:15–1:35 | **Search Helper connect** | Settings (or Search): create/copy pairing token → put in Helper → start Helper → show **connected/paired**. Do **not** show downloading the worker. |
| 7 | 1:35–1:55 | **Start search** (LinkedIn Posts) | Start run. Pause if needed until activity appears. |
| 8 | 1:55–2:05 | **Logs flash** | Helper or run logs for **1–2 seconds** only (optional Qwen/usage flash is OK but product stays primary). |
| 9 | 2:05–2:25 | **Analysis** | When jobs ready: show analysis starting; when **one** job completes, show it; note others running **in parallel**. Do not wait for every job. |
| 10 | 2:25–2:45 | **Suggested CV HITL** | Open job → current vs suggested swaps → **approve** → generate → download `.docx` → quick open so layout/structure looks the same. |
| 11 | 2:45–2:55 | **Architecture end card** | Fullscreen [`docs/architecture.png`](./architecture.png) ~5–8s. Then stop. |

**What NOT to put in the video**
- README as the opening title
- All Mermaid subgraph diagrams (parent / search / application) — only the PNG
- Long Helper download/install
- Long Qwen console/logs (optional 5s max; never show API keys)
- Going over 3:00

**Upload:** public link → paste on Devpost.

### 2. Devpost form (required)

- [ ] Select **Track 4 — Autopilot Agent**
- [ ] Repo URL: https://github.com/HamzaFayaz/JobPilot
- [ ] Written description (features + DashScope `compatible-mode/v1`; can reuse points from Medium draft)
- [ ] Video link
- [ ] Live demo: http://47.237.150.6 (+ test login if useful)
- [ ] Architecture image: upload `docs/architecture.png`
- [ ] Alibaba proof **file link** e.g.  
  `https://github.com/HamzaFayaz/JobPilot/blob/main/System%20Design/alibaba-cloud-trial.md`  
  (also OK: `deploy/Dockerfile.api` or `.github/workflows/deploy.yml`)
- [ ] Gallery screenshots: ECS Workbench/console (instance + IP), optional UI + Helper paired
- [ ] Blog URL (Medium) when published

**Medium blog (only draft file):** [`docs/medium-blog-draft.md`](./medium-blog-draft.md)

### 3. ECS / Workbench screenshot (required by proof docx)

- Alibaba console / Workbench overview showing **running** instance and public IP
- Add to Devpost gallery (and keep a local copy)

### 4. Blog / social (optional — Blog prize) — **targeting Top 10**

- **Platform locked:** Medium (public)
- **Prize criteria:** thoroughness + potential impact only
- **Must:** journey building with Qwen Cloud + relevant to JobPilot + URL on Devpost
- **Draft ready to paste:** [`docs/medium-blog-draft.md`](./medium-blog-draft.md) (**only** Medium draft file — use this)
- **Note:** This hackathon’s Blog winners are not announced yet. Peer posts already live on Dev.to — compete on depth + reusable insight.
- **Title:** *Building JobPilot: an Autopilot Job-Application Agent on Qwen Cloud*

### 5. Optional extras

- Short deck/PPT (marketing site mentions it; Official Rules do not require it)
- Judge test account notes on Devpost

---

## Judge deep-links (after push to main)

| What | Link |
|------|------|
| Qwen API config | `backend/app/config.py` |
| Models | `config/llm.yaml` |
| Alibaba ECS notes | `System Design/alibaba-cloud-trial.md` |
| API Docker image | `deploy/Dockerfile.api` |
| Deploy workflow | `.github/workflows/deploy.yml` |
| Actions runs | https://github.com/HamzaFayaz/JobPilot/actions |
| Architecture image | `docs/architecture.png` |
| Helper code | `worker/` |

---

## Do not reopen unless broken

- Worker search loop / WebBridge version lock
- Gmail send / Indeed / LinkedIn Jobs (out of submit path — do not advertise as gaps on Devpost title)
- Rewriting README architecture Mermaid as main diagram (PNG is source of truth)

---

## Prompt — paste to start a new chat

```text
Continue JobPilot hackathon submission packaging.

Read and follow:
- docs/hackathon-submission-handoff.md  (source of truth for what's done / next)
- docs/hackathon-official-rules-context.md  (Official Rules summary)

Context:
- Track 4 Autopilot Agent · live http://47.237.150.6 · repo https://github.com/HamzaFayaz/JobPilot
- Product + README + MIT LICENSE + docs/architecture.png are done
- Demo video has a full step-by-step shot list in the handoff (title card → ECS IP → app → Helper pair → search → analysis → suggested CV → architecture.png). Follow that; do not invent a new flow.
- Next priorities: (1) record demo video &lt; 3 min (2) Devpost form (3) ECS Workbench screenshot (4) optional blog for Blog prize

Help me with: [recording the demo / Devpost description draft / screenshot checklist / blog outline — pick one]
```
