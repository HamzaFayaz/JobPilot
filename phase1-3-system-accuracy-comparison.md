# JobPilot Phase 1–3 accuracy comparison

## Deterministic evidence
- Contract pass rate: 100.0% → 100.0% (+0.00 points).
- Packed chunks: 35 → 7. Changes reflect requirement-aware packing.
- Duplicate packed content: 0 → 0.
- Uncovered requirements: 0 → 0.
- Mean current-fit score: 80.0 → 53.5 (target: at least 75).
- Semantic judge: 6 pass, 3 warning, 3 fail; five cases failed the hardened judge contract.

## Per-job scoring
- job1_deerbiation: current 78 → 55; suggested 85 → 55; validated swaps 0.
- job2_deerbiation: current 82 → 64; suggested 88 → 64; validated swaps 0.
- job3_deerbiation: current 78 → 80; suggested 78 → 80; validated swaps 0.
- job4_deerbiation: current 82 → 15; suggested 88 → 15; validated swaps 0.

## Acceptance
- Deterministic hard contracts: pass.
- Improvement target: fail; Job 4 is 15/100 and the mean is 53.5/100.
- Human review: 0/4 jobs accepted.
- Job 1 fails because valid CV-visible agent evidence is discarded and stale rationale conflates current and portfolio evidence.
- Job 2 fails because web tenure and HTML/CSS coverage are overstated and portfolio details remain in rationale text.
- Job 3 fails because onsite/location and 1–2-year conditions are removed before the final “no gap” narrative.
- Job 4 fails because clear CV evidence for LangGraph/RAG, PyTorch, Python, Git, AWS/Bedrock, and pgvector is erased, producing an implausible 15/100.
- No human reviewer found an invented 60+ FPS metric; that metric is source-backed. Unsupported product conflation and production/deployment wording remain.
- Decision: `rejected`; another remediation cycle is required.
