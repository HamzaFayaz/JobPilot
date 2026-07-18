# JobPilot Phase 1–3 System and Accuracy Audit

**Canonical run:** `20260717T134631Z`  
**Logfire trace:** `019f7041b8cc282363bcf648f25c8d19`  
**Review method:** Three independent read-only audits covering evidence/retrieval, application scoring/swaps, and system/evaluation validity.

## Executive verdict

The Phase 1–3 architecture is a credible experimental foundation, but the current baseline should **not** be accepted as production-ready or as proof of accurate CV-fit scoring.

- Phase 1 profile/evidence quality: **82/100 heuristic**
- Phase 2 retrieval quality: **55/100 heuristic**
- Phase 3 mean result accuracy: **64/100 heuristic**
- Production-readiness decision: **reject pending P0 fixes and a new human-reviewed baseline**

The recorded `15 pass / 2 warning / 0 fail` judge headline is not a reliable accuracy measurement. The same Qwen family generated and judged the results, several judge statements credit evidence that was not selected, and the complete-pipeline runner does not exercise package persistence or parent graph finalization.

These percentages are audit heuristics, not statistically calibrated accuracy. The corpus contains one candidate and four jobs.

## What is technically sound

- Strict Pydantic schemas reject coercion and unexpected application fields.
- JSON parsing is strict, with one bounded repair retry.
- Original model output and deterministic corrected output are preserved separately.
- BM25, normalized dense embeddings, reciprocal-rank fusion, and cross-encoder reranking are appropriate retrieval techniques.
- `IndexFlatIP` is correct for normalized vectors.
- User-scoped SQLite/FAISS storage, typed errors, additive fan-out state, and idempotent package upserts are good foundations.
- Pydantic Evals is genuinely used, and the local artifact preserves fixture hashes, canonical cases, model IDs, trace IDs, and judge outputs.
- The Phase 1 checkpoint allows safe test resumption without repeating paid Phase 1 calls.

## Phase 1 audit: CV and project evidence

### CV skill extraction

Precision is very high: no clear unsupported extracted skills were found.

Broader recall is approximately 82%. Clear omissions include:

- PyTorch and CUDA
- YOLOv10 and ByteTrack
- Tkinter
- EasyOCR and PaddleOCR
- LM Studio and Cohere
- WhatsApp Business API and Meta API
- AWS Step Functions

The extraction is useful but incomplete. A section-aware deterministic extractor followed by LLM normalization would improve repeatability and recall.

### Mini-overviews and evidence cards

The mini-overviews are generally accurate and preserve project identity. Agentic RAG, JobPilot, Premcrest, and WhatsApp are the strongest.

Material weaknesses:

- Linnwork converts documentation-index titles into stronger implemented-architecture claims than the README proves.
- Voice Automation describes the `26M to 245M` range as parameter compression.
- YouTube Automation treats progress tracking and filename parsing as metrics.
- WhatsApp overstates limited historical export as no historical retrieval.
- IGI FPS/latency and Voice RTF values are source README assertions, not independently verified measurements.

Evidence should distinguish:

1. directly observed source facts,
2. source-authored performance assertions,
3. independently verified metrics.

### Chunking and index integrity

Observed corpus:

- 116 README chunks
- 44 generated evidence-claim chunks
- 160 vectors at 1024 dimensions
- Mean chunk size: approximately 106.8 tokens
- Observed range: 8–454 approximate tokens

Key defects:

- The configured 120-token minimum is not enforced.
- 73 of 116 README chunks fail source-range containment.
- Fenced-block masking changes offsets without mapping them back to the original README.
- Generated claims are indexed beside their source passages, creating semantic duplication and self-reinforcement.

The vector index itself is technically correct; source traceability and corpus construction are not yet reliable enough.

## Phase 2 audit: retrieval quality

### Job 1 — Azure AI Engineer: 56/100

- Python, React, agent integration, and general Azure evidence are partly useful.
- No Azure AI Foundry, Azure OpenAI, or Azure data-warehousing evidence exists.
- The final bundle includes weak or repeated evidence rather than maximizing explicit requirement coverage.
- The judge correctly issued an overall warning, but still overstates traceability and usefulness.

### Job 2 — AI-assisted Web Developer: 58/100

- JobPilot contributes useful React/FastAPI/web-stack evidence.
- Cursor keyword matching overpromotes WhatsApp MCP evidence.
- IGI troubleshooting and Premcrest documentation are noise.
- HTML/CSS and proof of shipped AI-assisted websites remain unproven.

### Job 3 — Junior AI Engineer: 63/100

- The broad project mix is acceptable for a sparse job description.
- The top result is a hackathon claim.
- The only Agentic RAG passage is prerequisites rather than architecture or implementation evidence.
- The judge credits evidence that was not present in the selected bundle.

### Job 4 — Agentic / GenAI Engineer: 46/100

- JobPilot provides strong LangGraph evidence.
- No Agentic RAG passage is actually selected.
- No selected evidence directly covers Bedrock, PyTorch, NLP, or Git requirements.
- Three JobPilot passages are near-duplicates.
- Debug `selected_project_ids` means projects permitted for packing, not projects actually packed; this misled the judge.

### Retrieval conclusion

The retrieval stack is sound, but final packing is relevance-oriented rather than coverage-aware. It needs requirement-by-requirement retrieval, novelty/deduplication, and explicit coverage accounting.

## Phase 3 audit: scoring and swap accuracy

### Systemic defects

1. **Portfolio leakage into current score**

   Current-CV requirement status and scoring sometimes rely on README/evidence-card facts. Portfolio-only evidence must influence only swap recommendations and suggested fit.

2. **Four CV projects collapse into one slot**

   The source CV visibly contains four projects, but every result evaluates only `slot_index: 0`. The deterministic one-decision-per-slot check passes only because the upstream parser produced one malformed aggregate slot.

3. **Post-correction narrative is stale**

   Job 3 correctly forces an invalid swap to `keep` and resets the suggested score, but the summary and rationale still recommend the rejected swap.

4. **Same-family judge misses direct contradictions**

   Qwen Max gave all Phase 3 cases pass verdicts and often 4/4 criterion scores despite unsupported classifications, irrelevant swaps, and corrected-result contradictions.

### Job 1 — Azure AI Engineer

- Model: `78 → 85`, high confidence
- Independent estimate: `68 → 72`, medium confidence
- Heuristic result accuracy: **68%**

Good:

- Python, agents, React/full-stack, and general Azure evidence are visible.
- JobPilot is a reasonable project for showing React, FastAPI, LangGraph, and deployment.

Problems:

- Azure AI Foundry and Azure OpenAI should be `not_evidenced`, not partial.
- General Azure does not prove those products.
- The +7 uplift does not close Azure-specific gaps.
- The rationale explicitly uses both CV and portfolio to justify current fit.
- Riyadh/location context is omitted.

### Job 2 — AI-assisted Web Developer

- Model: `82 → 88`, high confidence
- Independent estimate: `61 → 64`, medium confidence
- Heuristic result accuracy: **46%**

Good:

- The result recognizes missing proof of AI-assisted website shipping.

Problems:

- One year of web-development experience is unsupported.
- HTML/CSS/JavaScript/frameworks should be partial, not matched.
- Willingness to learn is not directly assessable.
- `Rust-like concurrency patterns` is invented.
- WhatsApp MCP does not prove that Cursor was used to build or ship websites.
- The proposed swap does not resolve its target requirement.

This is the weakest Phase 3 result.

### Job 3 — Devorbis AI Engineer

- Model: `78 → 82`; deterministic final: `78 → 78`
- Independent estimate: `76 → 76`, medium confidence
- Heuristic result accuracy: **69%**

Good:

- Degree, basic AI/ML, location uncertainty, and communication uncertainty are mostly handled correctly.
- Deterministic `invalid_swap_forced_keep` is effective.

Problems:

- The model recommends Agentic RAG even though it already appears in the current CV.
- The backend correctly rejects the swap, but the final narrative still recommends it.
- The claim that 2025–2026 employment dates are future-dated is false on the run date, 2026-07-17.

### Job 4 — Agentic / GenAI Engineer

- Model: `82 → 88`, high confidence
- Independent estimate: `78 → 80`, medium-high confidence
- Heuristic result accuracy: **73%**

Good:

- RAG, Python, PyTorch, Git, and early-career experience are broadly grounded.
- Bedrock remains partial.

Problems:

- The explicit shift requirement is omitted.
- OCR is not NLP evidence.
- JobPilot evidence does not prove the targeted NLP requirement.
- JobPilot is redundant with LangGraph/RAG already visible in the CV.
- Replacing the only AWS/Step Functions project may weaken the most important cloud gap.
- The +6 uplift is excessive.

## Evaluation and observability validity

### What the baseline proves

- The real models can produce schema-valid Phase 1–3 artifacts.
- The retrieval and application calls complete against the real corpus.
- Deterministic correction can prevent at least one invalid swap.
- Logfire and local artifacts provide useful debugging evidence.

### What the baseline does not prove

- Production-ready semantic accuracy
- Calibrated fit-score accuracy
- Correct multi-slot swap planning
- End-to-end package persistence in the real-cost runner
- Robustness across different candidates and job categories
- Independent judge agreement
- Correct behavior under model, retrieval, database, or Logfire failures

### Reproducibility gaps

- The report records commit `c634ff...`, but the Phase 3 implementation was dirty/untracked; the commit does not identify the evaluated code.
- Phase 1 uses moving model aliases.
- Checkpoint validation does not hash implementation source, prompt text, schemas, dependencies, DB, profile, or FAISS files.
- The runner directly calls `analyze_job()` and `classify_fit()` rather than the complete application subgraph and package persistence flow.

### Observability gaps

Logfire captures model calls and the evaluation trace, but Phase 2 domain spans do not contain complete:

- BM25/FAISS result rows
- fusion ordering
- reranker input/output
- final bundle
- fallback reasons
- deterministic corrections
- persistence outcomes

The local canonical artifact is more complete than Logfire, but it still omits several exact raw model/judge messages required by the plan.

## Prioritized remediation

### P0 — required before another acceptance baseline

1. Parse all four CV project slots and test DOCX-derived slot boundaries.
2. Enforce the current-CV/portfolio evidence boundary in code, not only the prompt.
3. Regenerate or deterministically rewrite all dependent narrative after corrections.
4. Fix chunk source offsets and add direct containment tests.
5. Make evaluators inspect actual packed chunks rather than permitted project IDs.
6. Deduplicate generated claims against source passages.
7. Run the real-cost evaluation through application subgraph persistence and parent finalization.
8. Record dirty-tree state and source/config fingerprints in every report.

### P1 — required for trustworthy quality measurement

1. Retrieve per explicit requirement, then pack for coverage, novelty, and diversity.
2. Verify each swap evidence reference directly supports every targeted requirement.
3. Require substring-verifiable CV quotations.
4. Compute tenure and date facts deterministically.
5. Expand deterministic evaluators for ownership, embedding consistency, token budgets, evidence validity, fallback behavior, and correct swap-out mapping.
6. Enforce expected judge criteria and judge-output consistency.
7. Add failed-package, retrieval-failure, transport-failure, Logfire-outage, and redaction tests.

### P2 — calibration and production acceptance

1. Build a larger candidate/job benchmark with negative and adversarial cases.
2. Add blinded human labels and inter-rater agreement.
3. Use an independent judge family or compare multiple judges.
4. Calibrate fit thresholds and score uplift against human ratings.
5. Resolve all warnings and complete a real-search contract smoke test.

## Acceptance criteria for the next baseline

- Four real CV slots produce four ordered decisions for every job.
- No portfolio-only fact changes `current_cv_score`.
- Every selected chunk resolves to the correct original source range.
- Every swap closes at least one explicit requirement with direct evidence.
- Corrected results contain no stale score, summary, limitation, or rationale.
- Real-cost evaluation persists ready/failed packages and finalizes the run.
- The report identifies the exact source tree and checkpoint contents.
- All deterministic checks pass independently against persisted state.
- Human reviewers approve every job result and warning.

## Final conclusion

JobPilot’s Phase 1–3 design should continue, not be discarded. The chosen techniques are appropriate and several safety mechanisms work. However, the current outputs are not accurate enough for user-facing fit scores or project-swap recommendations.

The next engineering milestone should focus on evidence boundaries, CV slot parsing, correction consistency, source traceability, and coverage-aware retrieval before adding more agents or infrastructure.

## Sources reviewed

- Real CV-derived checkpoint text and profile snapshot
- Eight project READMEs
- Four real job descriptions
- SQLite/FAISS Phase 1 checkpoint
- Canonical report `run-20260717T134631Z.json`
- Exported Logfire trace with 188 records
- Phase 1–3 backend implementation and tests
- Phase 3 implementation plan and acceptance criteria

