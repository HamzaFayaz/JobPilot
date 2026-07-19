# Qwen Cloud Hackathon  -  Official Rules (main context)

**Source:** Global AI Hackathon Series with Qwen Cloud Official Rules (Devpost).  
**JobPilot track:** Track 4  -  Autopilot Agent.  
**Deadline:** Jul 20, 2026, 2:00 pm PT (Submission Period ends).  
**Judging:** Jul 28 - Aug 11, 2026 PT · Winners ~Aug 17, 2026.

If marketing pages conflict with these rules, **Official Rules win**.

---

## What we must build

- Project uses **Qwen models on Qwen Cloud**.
- Fits **at least one track**  -  JobPilot: **Track 4 Autopilot Agent**
  - End-to-end real-world workflow
  - Ambiguous inputs
  - External tools
  - Human-in-the-loop at critical decisions
  - Production-ready (not a toy demo)

---

## Required Devpost submission fields

| Requirement | Detail |
|-------------|--------|
| **Public repo** | All source + run instructions; **OSS license file** detectable in GitHub About |
| **Text description** | Features + functionality |
| **Alibaba Cloud proof** | Backend on Alibaba Cloud; proof = **link to a code file in the repo** that shows Alibaba Cloud services/APIs |
| **Architecture diagram** | Clear system visual (Qwen Cloud ↔ backend ↔ DB ↔ frontend) |
| **Demo video** | **&lt; 3 minutes** (judges need not watch past 3); show product working; public on **YouTube / Vimeo / Youku**; no unlicensed music/trademarks |
| **Track** | Identify track on the form → **Track 4** |
| **Testing access** | Working demo (website / build). Private site → include login. Free access until judging ends. Judges may score from text/images/video only |

**Optional (Blog prize):** Public blog or social post about building with QwenCloud; link must be in the Submission.

**Language:** English (or English translation of video, description, testing instructions).

**After deadline:** Submission frozen (no edits). Drafts OK before deadline.

---

## Stage One pass/fail (must clear)

Project must **reasonably fit the theme** and **reasonably apply the required APIs/SDKs** (Qwen Cloud).

JobPilot: DashScope OpenAI-compatible  
`https://dashscope-intl.aliyuncs.com/compatible-mode/v1`  
+ DashScope embeddings/rerank. State this clearly in description + diagram (not a separate “API proof file” rule).

---

## Stage Two scoring (equal weights as listed)

| Weight | Criterion | Judges look for |
|--------|-----------|-----------------|
| 30% | Innovation & AI Creativity | Sophisticated Qwen Cloud API use; engineering novelty |
| 30% | Technical Depth & Engineering | Architecture, clean non-trivial code, stack sophistication |
| 25% | Problem Value & Impact | Real pain point; productization / OSS potential |
| 15% | Presentation & Documentation | Clear demo; architecture docs |

**Blog prize:** judged on thoroughness + impact of the blog/social post (separate criteria).

---

## Prizes JobPilot can target (one submission)

| Prize | Amount | Notes |
|-------|--------|-------|
| Track 4 Autopilot grand | $7k cash + $3k credits (+ swag / feature) | One winner per track |
| Top 10 Honorable Mention | $500 + $500 credits | All eligible submissions |
| Top 10 Blog Post | $500 + $500 credits | Needs Blog Submission link |

**Cap:** one grand prize + up to one blog prize per project.

---

## Not required by Official Rules

- Voiceover in the demo video (show functioning product; English captions OK)
- Separate “Qwen API proof file” link (unlike Alibaba proof)
- Presentation deck (marketing site mentions it; Official Rules do not list PPT as required)

---

## JobPilot packaging checklist

- [x] GitHub **LICENSE** (MIT)  -  push so About detects it
- [x] README: Track 4 + Qwen + Alibaba proof links ([README Hackathon](../README.md#hackathon))
- [ ] Devpost: Track 4 selected
- [ ] Description: features + **Qwen Cloud / DashScope compatible-mode** stated
- [ ] Architecture diagram uploaded (export Mermaid from README to PNG)
- [ ] Alibaba proof on form: link [`System Design/alibaba-cloud-trial.md`](../System%20Design/alibaba-cloud-trial.md) or [`deploy/Dockerfile.api`](../deploy/Dockerfile.api)
- [ ] Demo video &lt; 3 min, public link
- [ ] Testing: live demo URL (+ credentials if needed)
- [ ] Optional: blog/social URL for Blog prize

**Live demo:** http://47.237.150.6  
**Repo:** https://github.com/HamzaFayaz/JobPilot  

**Judge deep-links (after push):**
- Qwen API: `backend/app/config.py` · models: `config/llm.yaml`
- Alibaba: `System Design/alibaba-cloud-trial.md` · `deploy/Dockerfile.api` · `.github/workflows/deploy.yml` · https://github.com/HamzaFayaz/JobPilot/actions
- Technical depth: README `#technical-depth--engineering` · worker: `worker/`
