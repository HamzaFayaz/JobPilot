# `enrich_job` → `package_out` → CV Tailoring Handoff

**Status:** Design agreed. Analysis + Applications path is **shipped**.  
**Next implementation (last major product step before send):** user-triggered `tailor_cv` — see [`currently-working-feature.md`](../../currently-working-feature.md).

**Related plan:** [`jobpilot_phase3_application_observability_evals_plan.md`](../../.agent/plans/jobpilot_phase3_application_observability_evals_plan.md)

## Purpose

Record the boundary between:

1. search-time job analysis (**done**),
2. persisted project-swap recommendations (**done**), and
3. later user-approved CV generation (**next**).

This prevents `enrich_job` from performing expensive layout-constrained CV
writing for every matched job while preserving everything the later
`tailor_cv` workflow needs.

---

## End-to-end boundary

```text
Search-time Phase 3

retrieve_project_evidence()
        ↓
enrich_job
  - classify disclosed requirements
  - score the current CV
  - select keep/swap per CV project slot
  - identify the replacement project
  - identify requirements the replacement demonstrates
  - return grounded evidence references and rationale
        ↓
classify_fit
  - deterministic score/swap validation
  - fit tier and message
        ↓
package_out
  - persist the job snapshot, validated analysis, and swap plans
        ↓
results UI

Later user-triggered workflow

user selects a job and approved swaps
        ↓
tailor_cv
  - load current CV and verify its version
  - load the persisted job/swap plans
  - reload and validate selected-project evidence
  - generate exact layout-constrained replacement text
        ↓
deterministic layout validation
        ↓
create a new CV draft (never overwrite the original)
        ↓
user preview and final confirmation/download
```

There is no automatic graph edge from `package_out` to `tailor_cv`.
`tailor_cv` runs only after an explicit user action.

---

## `enrich_job` responsibility

`enrich_job` returns an analysis and **swap plan**, not final CV-ready lines.

Per slot, the plan must identify:

```json
{
  "slot_index": 2,
  "action": "swap",
  "swap_out_project": "Computer Vision Aimbot",
  "swap_in_project_id": "jobpilot",
  "swap_in_project_name": "JobPilot",
  "target_requirements": [
    "LangGraph",
    "multi-agent systems",
    "RAG"
  ],
  "evidence_refs": [
    {
      "project_id": "jobpilot",
      "heading_path": "Agentic architecture",
      "chunk_id": "chunk-123"
    }
  ],
  "rationale": "JobPilot provides stronger grounded agentic-AI evidence for this role.",
  "impact": "high"
}
```

The exact schema will be finalized with the Phase 3 application result model.

### `enrich_job` must not

- rewrite the `.docx`,
- generate final per-line CV text,
- modify the stored CV,
- run automatically again after `package_out`,
- treat an imported project absent from the CV as evidence for
  `current_cv_score`,
- claim that a project compensates for unrelated experience, education,
  eligibility, or location gaps.

### Layout awareness at analysis time

`enrich_job` receives enough slot metadata to avoid recommending an obviously
impossible replacement:

- slot index,
- current project identity,
- title/item counts when available,
- approximate character budget.

Precise line generation and rendered layout checking remain the responsibility
of `tailor_cv`.

---

## `package_out` responsibility

`package_out` persists the complete validated handoff required by the future
tailoring workflow.

### Persisted job snapshot

- user ID and run ID,
- job title, company, URL, platform, and description,
- analysis/model/prompt version,
- profile/CV version or stable CV content hash used during analysis.

### Persisted fit analysis

- explicit and inferred requirements,
- requirement statuses and evidence references,
- confidence,
- current and suggested scores,
- fit tier/message,
- summary,
- deterministic validation warnings/corrections.

### Persisted swap plans

For every CV project slot:

- slot index,
- action (`keep` or `swap`),
- current project identity,
- replacement project ID/name when swapping,
- target requirements,
- evidence references,
- rationale,
- qualitative impact (`low`, `medium`, or `high`).

The current `job_packages` table contains only legacy single-swap columns
(`cv_decision`, `swap_out_project`, and `swap_in_text`). Phase 3 needs a
multi-slot structured representation. The storage choice and migration are part
of the application-subagent schema discussion; this document does not choose
between a JSON column and normalized child rows.

`package_out` should store references and validated analysis, not duplicate all
README text into every job package.

---

## User-triggered `tailor_cv` workflow

### Trigger timing

`tailor_cv` runs only when the user:

1. opens a job package,
2. reviews the recommendation,
3. selects or approves one or more swaps, and
4. chooses **Generate tailored CV**.

The generated result is a draft. A second explicit confirmation is required to
accept/download it.

### Inputs

`tailor_cv` receives:

- full job description,
- original/current CV,
- approved slot and swap plans,
- exact CV slot layout contract,
- selected replacement-project overview,
- selected replacement-project evidence card,
- selected relevant README chunks,
- prompt/model/profile/CV versions.

It does not need every portfolio project because project selection has already
occurred. If the user manually chooses a different project, evidence for that
project is loaded before generation.

### Freshness checks

Before generation:

- verify the job package belongs to the current user,
- verify the selected project still exists,
- verify evidence references are still valid,
- compare current CV/profile version with the version used by `enrich_job`,
- regenerate analysis or require user review if the CV/profile changed.

---

## Layout-preserving output contract

The future CV parser should expose each project slot as structured layout
constraints:

```json
{
  "slot_index": 1,
  "title": {
    "text": "Current Project",
    "max_characters": 30
  },
  "description_items": [
    {
      "item_index": 0,
      "type": "bullet",
      "max_characters": 50,
      "style_id": "ProjectBullet"
    },
    {
      "item_index": 1,
      "type": "bullet",
      "max_characters": 60,
      "style_id": "ProjectBullet"
    }
  ]
}
```

`tailor_cv` returns exactly:

- one replacement title,
- the same number of description paragraphs/bullets,
- one generated item per original item,
- text within each configured budget,
- evidence references supporting every factual claim.

Character count is only an approximation of rendered width. Equal character
counts do not guarantee equal Word line lengths because glyph widths, font,
bold runs, indentation, tabs, margins, and paragraph spacing differ.

The future workflow therefore requires:

1. deterministic item-count and character-budget validation,
2. replacement while preserving paragraph/run styles,
3. `.docx` rendering or page/layout validation,
4. shortening/regeneration when the draft overflows,
5. preservation of the original CV.

Same-project bullet refresh belongs to this tailoring workflow. Phase 3
`enrich_job` focuses on keeping the current project or selecting a different
portfolio project.

---

## Model-call and token policy

`enrich_job` runs once per matched job because every result needs analysis.

`tailor_cv` runs only for a user-selected job. One call handles all approved
slots; do not make one model call per slot.

Approximate tailoring budget:

```text
system prompt                    400–700
job description                  500–1,500
CV/context                     1,000–2,000
approved swap plans              100–500
layout constraints               100–500
selected project evidence        500–2,000
─────────────────────────────────────────
total input                   ~2,600–7,200 tokens
output                          ~200–1,000 tokens
```

Actual usage depends on the number of approved swaps and selected evidence.
Logfire records exact model, prompt version, tokens, latency, and output.

---

## Human-in-the-loop guarantees

- Search-time analysis never modifies a CV.
- `package_out` persists recommendations only.
- Generating a draft requires explicit user action.
- The generated draft never overwrites the original CV.
- Final acceptance/download requires another explicit user confirmation.
- Sending an application remains a separate user-approved operation.

---

## Implementation order

```text
Shipped:
1. enrich_job
2. classify_fit
3. package_out and structured handoff persistence
4. real Phase 1–3 evaluation + Applications UI

Next (last product step before send) — implement now:
5. exact CV layout parser/contract
6. user approval API/UI
7. tailor_cv model call
8. deterministic and rendered layout validation
9. draft storage, preview, and download

Later:
10. attach tailored CV + send (separate HITL)
```

