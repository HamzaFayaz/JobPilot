# Application Sub-Agent and ATS Compatibility Discussion

**Status:** Locked for implementation (decisions updated 2026-07-16)

**Related docs:**

- Project evidence inputs → [`project-evidence-retrieval-discussion.md`](project-evidence-retrieval-discussion.md)
- Portfolio overview at import → [`project-evidence-portfolio-overview-addendum.md`](project-evidence-portfolio-overview-addendum.md)
- Active build tracker → [`currently-working-feature.md`](../../currently-working-feature.md)

## Purpose

Define how JobPilot should analyse a user's CV against a job listing, make
project-tailoring suggestions, and present an understandable fit estimate.
This is a **JobPilot match score** / **CV fit estimate** — not access to, or a
prediction of, an employer's private ATS score.

## What JobPilot can and cannot claim

Every employer can use a different applicant-tracking system (for example,
Workday, Greenhouse, Lever, Taleo, or a custom system), and each role can have
different private filters and weights. Some systems only store applications;
they do not automatically rank candidates.

JobPilot must therefore use labels such as **JobPilot match score** or **CV fit
score**. It must not claim that a candidate has a particular score in a
specific employer's ATS.

---

## Locked decisions (2026-07-16)

### One LLM call per job (`enrich_job`)

For each prefiltered listing, run **one** structured Qwen call that returns:

- Fit analysis facts (`matched`, `missing`, `unknown`, evidence, confidence)
- **`current_cv_score`** — how well the CV fits **as it is today**
- **`suggested_cv_score`** — estimated fit **after all recommended project
  swaps**, if any swaps would help; otherwise same as `current_cv_score`
- Per-slot project recommendations (`project_swaps[]` — keep or swap for each
  project on the CV)
- `summary` and optional `draft_email` stub

Stages 1 and 2 below are **one call, two output sections** — not two LLM
invocations and not two graph nodes.

### Primary scoring: LLM reasoning

The model scores holistically from job description + CV + retrieved project
evidence. A strong prompt produces better results than a first-version backend
rubric on sparse LinkedIn posts.

Backend does **not** recalculate the score from a weighted rubric. It only:

- Clamps scores to 0–100
- Validates swap fields
- Classifies fit tier and sets user-facing `fit_message`
- Persists the job package

A deterministic rubric engine remains a **deferred alternative** (see below) if
LLM scores prove inconsistent in production.

### Threshold = guidance, not a hard drop

The recommended bar (default **60**) is used to **classify and message**, not to
hide jobs. All enriched jobs are saved to `job_packages`; below-threshold jobs
are shown with a direct low-fit warning so the user can still apply (HITL).

### Per-slot project swaps (up to N, not blind)

The CV project section may be **out of date** compared to the user's imported
GitHub portfolio (e.g. four projects on the CV, eight in portfolio). Newer or
more relevant portfolio projects may fit a target role better than what is
currently printed on the CV.

The agent must:

1. **Detect how many projects are on the CV** (parse the project section — e.g.
   four slots).
2. Return a **per-slot decision** for each CV project: `keep` or `swap`.
3. Suggest swaps only where a portfolio project is **clearly stronger** for this
   job — **not** blind replacement of all slots.
4. **Preserve CV structure:** same number of project entries, same approximate
   length per slot (`chars_per_line` / character budget from CV parse), no extra
   pages, no removed sections. Swap text replaces in-place; it does not grow or
   shrink the CV layout.

Rules:

- **Maximum swaps** = number of projects on the CV (e.g. up to four swaps for
  four slots), but typical output swaps **only weak or outdated slots** (often
  one to three, sometimes zero).
- **Never swap** a CV project that is already a strong match for the job.
- **Never use** the same portfolio project for two slots.
- `suggested_cv_score` reflects fit **after all recommended swaps** in the
  response, not a single swap in isolation.

The agent does **not** run combinatorial “pick best four of eight” optimization.
It makes **judgment calls per slot** with evidence, keeping slots that already
work.

### Project evidence (production path)

Before `enrich_job`, the backend runs **hybrid retrieval** over evidence cards
and README chunks (see project-evidence docs). Inputs per call:

```text
Job: title, company, description_text, platform
Profile: cv_text, skills, target_roles
Projects: all portfolio_overviews + top retrieved evidence cards + chunks
```

Worker listing contract unchanged: `title`, `company`, `url`, `description_text`.

---

## Application sub-agent capabilities

These are product responsibilities, not separate LLM calls (except where noted).

| # | Capability | In `enrich_job`? | When |
| --- | --- | --- | --- |
| 1 | CV-to-job fit analysis | Yes | Every prefiltered job |
| 2 | Project swap suggestion | Yes | Every prefiltered job |
| 3 | CV tailoring draft | No — separate call | User opens job detail (HITL) |
| 4 | Outreach email draft | Stub in enrich; full later | User approves send |

### 1. CV-to-job fit analysis

- **Inputs:** job description, CV text, skills, target roles, light project
  context (portfolio overviews + retrieved evidence).
- **Outputs:** requirements, `matched` / `missing` / `unknown`, evidence,
  `confidence`, **`current_cv_score`**, `summary`.

Scores the CV **as uploaded**, including whatever projects already appear on it.

### 2. Project swap suggestion (per CV slot)

- **Inputs:** same as above, plus retrieved evidence cards/chunks for swap
  grounding; parsed CV project slots (count + `chars_per_line` per slot).
- **Outputs:** `project_swaps[]` (one entry per CV project slot), each with
  `action` (`keep` | `swap`), names, `swap_in_text` when swapping, slot
  character budget, rationale; plus **`suggested_cv_score`**.

Each `swap` replaces one **on-CV** project with one **portfolio** project using
only evidenced facts. `swap_in_text` must fit the **same character budget** as
the original slot so the CV layout and page count do not change.

### 3. CV tailoring draft (deferred from per-job loop)

Full bullet rewrite when the user requests it on the job detail screen. Uses
retrieved README chunks and atomic claims heavily.

### 4. Outreach draft

Optional stub in `enrich_job`. Never sent automatically.

---

## Per-job pipeline

```text
retrieve_project_evidence(job, profile)     ← backend, no LLM
        ↓
enrich_job — ONE Qwen structured JSON call
        ↓
backend guardrails
  · clamp current_cv_score, suggested_cv_score to 0–100
  · validate each slot in project_swaps (exists, grounded, char budget, no dupes)
  · classify_fit_tier + fit_message
        ↓
package_out → INSERT job_packages (all jobs, including below threshold)
```

---

## Scoring approach

### Active: LLM holistic scoring

The prompt must instruct the model to:

- Label scores as **JobPilot match score**, not employer ATS.
- Set **`current_cv_score`** from the CV as-is (projects on CV included).
- Set **`suggested_cv_score`** after evaluating all slot decisions; if every slot
  is `keep`, `suggested_cv_score` equals `current_cv_score`.
- For each CV project slot, choose `keep` or `swap` — swap only when a portfolio
  project is materially better; never swap all slots by default.
- Each `swap_in_text` must respect the slot's character budget (maintain CV
  structure; no layout growth).
- Never penalize unstated requirements (see `matched` / `missing` / `unknown`).
- Cite CV or project evidence for matched items and swap text.
- Return `confidence` (`low` | `medium` | `high`) when the listing is sparse.

Holistic reasoning handles messy LinkedIn posts better than a fixed rubric.

### Deferred alternative: deterministic rubric

If LLM scores drift or violate policy in production, add a backend rubric as a
sanity check or replacement. Illustrative weights (not active):

| Criterion | Weight |
| --- | ---: |
| Explicit required skills evidenced in CV | 45 |
| Explicit preferred skills / stack | 15 |
| Role and seniority alignment | 15 |
| Relevant project or work evidence | 15 |
| Stated location, work-mode, or eligibility constraints | 10 |

```text
fit score = earned points / available stated-criterion points × 100
```

---

## Incomplete job descriptions

LinkedIn posts often omit a full job description, preferred skills, years of
experience, or eligibility constraints. The prompt must enforce three states:

| State | Meaning | Scoring rule (prompt) |
| --- | --- | --- |
| `matched` | Supported by CV/project evidence | Positive signal |
| `missing` | Explicitly required by the job but not evidenced | Negative signal |
| `unknown` | Not stated in the job post | **No penalty** |

Only explicitly stated requirements can be marked `missing`. An unstated skill
such as Docker, AWS, a degree, or years of experience must remain `unknown`.

Role-title implications go in `inferred_requirements`, visibly distinct from
explicit requirements.

Sparse listings example:

> JobPilot fit: 82/100 — low confidence. Limited requirements in the post; estimate
> based on disclosed Python and backend evidence only.

---

## Threshold and user-facing messages

Default recommended bar: **60** (configurable).

| Field | Purpose |
| --- | --- |
| `passes_threshold` | `current_cv_score >= threshold` |
| `fit_tier` | `strong` \| `moderate` \| `weak` \| `not_recommended` |
| `fit_message` | Short, direct advice for the UI (1–2 sentences) |

Illustrative tiers (configurable):

| Tier | Score (example) | `fit_message` tone |
| --- | --- | --- |
| `strong` | 75+ | Strong match — recommended to review |
| `moderate` | 60–74 | Decent match — worth reviewing |
| `weak` | 45–59 | Below recommended bar — apply only if interested |
| `not_recommended` | &lt; 45 | Poor fit — not suggested |

Below-threshold example:

> **Below our recommended fit (52/100).** Weak match for this post. You can still
> apply if the role interests you, but expect lower response odds.

With swap uplift:

> **Current CV: 52** — below recommended bar. **With the suggested swaps (2 of 4
> projects), estimated fit ~68.** Review each swap before applying.

`fit_message` may be templated from tier + scores, or derived from the LLM
`summary`. All jobs are persisted; the UI styles recommended vs caution states.

Rename graph node `score_threshold_gate` → **`classify_fit`** in implementation
(reflects classify + message, not drop).

---

## Backend guardrails (after LLM)

Not a second scoring engine — safety checks only.

### Score clamp

Force integers in range 0–100. Reject or default non-numeric scores.

### Swap validation (per slot)

| Check | Action if fail |
| --- | --- |
| `project_swaps` length matches CV project slot count | Reject or pad with `keep` |
| Each `swap_out_project` exists on the CV in that slot | Force `keep` for that slot |
| Each swap-in project exists in imported portfolio | Force `keep` for that slot |
| No portfolio project used for more than one slot | Deduplicate — keep strongest swap only |
| `swap_in_text` uses only CV + README evidence | Clear or flag that slot |
| `swap_in_text` length ≤ slot `chars_budget` (from CV parse) | Trim or reject that slot |
| Slot `action` is `keep` | `swap_in_text` must be empty |
| All slots `keep` | `suggested_cv_score` equals `current_cv_score` |
| Any slot `swap` | `suggested_cv_score` should be ≥ `current_cv_score` (flag if not) |

### Persist

`package_out` saves **every** enriched job. `match_score` on the package maps to
`current_cv_score`. Store `suggested_cv_score`, `passes_threshold`, `fit_tier`,
and `fit_message` for the UI.

---

## LLM response contract

JSON only. Illustrative full response:

```json
{
  "explicit_requirements": ["Python", "backend engineering", "remote"],
  "inferred_requirements": ["API development"],
  "matched": ["Python", "API development"],
  "missing": [],
  "unknown": ["years of experience", "cloud platform", "database"],
  "evidence": {
    "Python": "Built backend APIs in Project X"
  },
  "confidence": "low",
  "cv_project_slot_count": 4,
  "current_cv_score": 72,
  "suggested_cv_score": 85,
  "project_swaps": [
    {
      "slot_index": 0,
      "action": "keep",
      "cv_project_name": "E-commerce API",
      "rationale": "Already demonstrates backend Python APIs relevant to this post."
    },
    {
      "slot_index": 1,
      "action": "swap",
      "swap_out_project": "Todo App",
      "swap_in_project": "JobPilot",
      "swap_in_text": "JobPilot — FastAPI and LangGraph job-search platform with a desktop browser worker and human-approved application workflow.",
      "chars_budget": 280,
      "rationale": "CV project is outdated; JobPilot has stronger LangGraph and agent evidence for this role."
    },
    {
      "slot_index": 2,
      "action": "keep",
      "cv_project_name": "Data Pipeline",
      "rationale": "Relevant ETL experience; no better portfolio replacement."
    },
    {
      "slot_index": 3,
      "action": "swap",
      "swap_out_project": "Weather Widget",
      "swap_in_project": "Search Helper Worker",
      "swap_in_text": "Search Helper — Desktop worker using Kimi WebBridge for browser-assisted LinkedIn job extraction.",
      "chars_budget": 240,
      "rationale": "Weather Widget is weak for backend roles; worker project shows browser automation aligned with post."
    }
  ],
  "summary": "Good Python fit; 2 of 4 CV projects recommended for swap to reflect newer portfolio work.",
  "draft_email": ""
}
```

Prompt constraints:

- Extract requirements stated in the job post as `explicit_requirements`.
- Put title-based implications in `inferred_requirements` separately.
- Cite CV or project text for every matched item.
- Never mark an unstated requirement as missing.
- Use only user-provided facts for swap text; never invent experience,
  technologies, metrics, or achievements.
- Return one `project_swaps` entry per CV project slot; default to `keep` unless
  a portfolio swap is clearly better.
- Respect `chars_budget` per slot — swap text must not increase CV length or
  page count.

---

## Human-in-the-loop rule

The application sub-agent may create suggestions, but it must never modify the
stored CV automatically. A user opens a job package, reviews the proposed
project swap or rewritten bullets, and explicitly accepts any change. Sending
an email or application is also always a separate user-approved action.

---

## Implementation boundary

- `retrieve_project_evidence()` before each `enrich_job` (production retrieval
  per project-evidence docs).
- One structured Qwen `enrich_job` call per prefiltered job.
- Parse CV project section (slot count + `chars_per_line` per slot) before enrich.
- LLM returns `current_cv_score`, `suggested_cv_score`, fit facts, and
  `project_swaps[]` (per-slot keep/swap).
- Backend: clamp, swap validation, `classify_fit`, `package_out` (save all).
- CV full rewrite on demand after user selection (stage 3).
- Worker listing contract unchanged.

**Graph nodes:** `enrich_job` → `classify_fit` → `package_out`

**Code targets:** [`backend/app/graph/subgraphs/application/graph.py`](../../backend/app/graph/subgraphs/application/graph.py)
