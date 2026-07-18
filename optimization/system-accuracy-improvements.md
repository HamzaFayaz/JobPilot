# JobPilot system optimization suggestions

Suggestions to improve **complete system accuracy** (Phase 1 → retrieval → application), not one-off fixes for the four Deerbiation jobs.

**Baseline this builds on:** Run 3 (`20260717T184341Z`) — Qwen Max + `enrich_job_v4` — human system accuracy **~79/100**. Keep that baseline; optimize on top of it.

---

## Priority order (highest impact first)

### 1. Phase 2 retrieve / rerank noise (high)

**Problem:** Irrelevant portfolio chunks still get packed (e.g. van-sales / YouTube install notes for an agentic/Bedrock-style JD). That wastes context and can confuse swap evidence.

**Directions:**
- Stronger requirement-conditioned packing (prefer chunks whose content actually supports the requirement tokens).
- Soft demote projects that never match any high-importance requirement.
- Cap low-relevance projects per job (noise budget).
- Keep the rule: retrieval supplies **candidates**, not proof.

**Why it matters system-wide:** Every new job type benefits from cleaner evidence.

---

### 2. Application swap discipline (high)

**Problem:** Suggested score can rise when a swap only reinforces an already-`matched` skill, or when swap-out loss is ignored.

**Directions (prompt + light structural checks — do not recompute LLM scores):**
- Do not recommend a swap whose only targets are already fully matched on the current CV.
- Prefer swaps that turn `partial` / `not_evidenced` into stronger coverage.
- When swapping out a strong project, state what coverage is lost; keep uplift modest if net gain is small.
- Keep ownership rules: swap evidence must be replacement-owned packed `source_id`s only.

**Why it matters system-wide:** Fairer `suggested_cv_score` on all roles, not just Job 2/4.

---

### 3. Semantic status conservatism (medium)

**Problem:** Borderline adjacent skills (e.g. voice/RAG counted as full NLP) can be marked `matched` instead of `partial`.

**Directions:**
- Prompt: use `matched` only for explicit, direct evidence; use `partial` for related-but-incomplete.
- Keep product distinctions (Azure ≠ Azure AI Foundry / Azure OpenAI; Bedrock listed ≠ Bedrock deployed).

**Why it matters system-wide:** Reduces over-claiming across JDs.

---

### 4. Exact CV quote hygiene (medium / small)

**Problem:** Valid `cv_span_id` with abbreviated display quotes (`…`) weakens human and judge trust even when IDs are correct.

**Directions:**
- Prefer quotes that are exact substrings of the cited span (or short contiguous excerpts).
- Do not invent or mash span IDs; copy supplied IDs only.
- Keep metadata validation strict (do not auto-map hashes → UUIDs).

**Why it matters system-wide:** Grounding integrity without changing score authority.

---

### 5. Phase 1 skill / span completeness (lower for fit scores)

**Problem:** Judge warned that skill extraction omitted skills implied by projects (PyTorch, CUDA, pgvector, etc.).

**Directions:**
- Only chase this if Phase 1 outputs feed later stages poorly.
- Prefer improving CV evidence spans and date facts over bloating the skills list for its own sake.
- Fit scoring should stay CV-text grounded, not skill-list inflated.

**Why it matters less for “fit accuracy”:** Application already reads CV spans; missing skill tags rarely change grounded scores.

---

### 6. Measurement and evaluation hygiene (process)

**Directions:**
- Re-score on **new** jobs after changes; do not optimize only to the four Deerbiation cases.
- Keep durable checkpoints (Phase 1, per-job, prejudge) so retries do not re-bill.
- Treat same-family Max judging Max as supporting signal, not ground truth; human review stays required.
- Store system accuracy reviews under `evals/system/`; keep this file under `optimization/` for upcoming work.

---

## What not to do (premature / harmful)

- Do not enable application **thinking mode** while depending on `json_object` without a redesigned stream→JSON path.
- Do not loosen source identity, CV-vs-portfolio boundaries, or score invariants.
- Do not replace LLM semantic scores with fixed weight formulas (Run 2 failure mode).
- Do not auto-accept cross-project evidence or content hashes as `source_id`.
- Do not change the application model again until retrieve/swap discipline is measured on Plus/Max with the same prompt family.

---

## Expected impact (honest)

| Workstream | Likely effect on complete-system accuracy |
| --- | --- |
| Retrieve/rerank noise | Largest remaining Phase 2 gain |
| Swap discipline | Clear Phase 3 calibration gain |
| Status conservatism + exact quotes | Smaller but real grounding/claim gains |
| Phase 1 skill list polish | Small for fit scores unless spans are wrong |

Together, these are more likely to move the system from **~79 toward the mid-80s** than to **90+** in one step. Reach for 90+ only after a second measured run on held-out jobs.

---

## Suggested next implementation slice

1. Prompt updates for swap discipline + matched-status conservatism (no paid full re-run until approved).
2. Deterministic non-paid tests for: redundant-swap rejection hints, keep-shape, ID rules.
3. Targeted retrieve/rerank packing tweak + unit tests with noisy vs relevant chunks.
4. One paid pipeline run with checkpoints; human review; update `evals/system/`.

---

## Related artifacts

- Accuracy review: `evals/system/run-20260717T184341Z-accuracy.md`
- Canvas copy: `evals/system/run3-system-accuracy.canvas.tsx`
- Run report: `tests/complete-pipeline-test/results/run-20260717T184341Z.json`
- Plan: `.agent/plans/jobpilot_phase2_recall_phase3_llm_authority_plan.md`
