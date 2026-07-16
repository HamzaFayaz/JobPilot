# Application Sub-Agent Input Spec (`enrich_job`)

**Status:** Locked for Phase 2 + application subagent implementation (2026-07-16)

**Scope:** Inputs only — how `retrieve_project_evidence()` builds the context
bundle and how that bundle is passed to **one** `enrich_job` LLM call per job.

**Related docs:**

- Outputs, scoring, swap validation → [`application-subagent-ats-compatibility-discussion.md`](application-subagent-ats-compatibility-discussion.md)
- Chunking at import, hybrid search → [`project-evidence-retrieval-discussion.md`](project-evidence-retrieval-discussion.md)
- `portfolio_overview` at import → [`project-evidence-portfolio-overview-addendum.md`](project-evidence-portfolio-overview-addendum.md)
- Phase 2 build plan → [`.agent/plans/jobpilot_project_evidence_phase2_plan.md`](../../.agent/plans/jobpilot_project_evidence_phase2_plan.md)
- Phase 2 storage (SQLite + FAISS) → [`phase-2-retrieval-storage-design.md`](phase-2-retrieval-storage-design.md)

---

## Pipeline position

```text
matched_jobs (from prefilter)
        ↓
retrieve_project_evidence(job, profile)    ← backend code, NO LLM
        ↓
enrich_job(bundle)                         ← ONE LLM call per job
```

There are **not** two LLM calls for “layer 1” and “layer 2”. Layers describe
**detail levels inside one user message** (or one structured JSON payload).

---

## Source data (already stored before retrieval)

### At GitHub import (Phase 1 — done)

Per `StoredProject`:

| Field | Source | Used in enrich_job input |
| --- | --- | --- |
| `id` | profile store | project identity, chunk linkage |
| `name` | import / LLM | display, CV slot matching |
| `description` | import / LLM | light context |
| `repo_full_name` | GitHub | optional match key |
| `readme_md` | GitHub | source of truth; not sent in full |
| `portfolio_overview` | `build_project_evidence()` | layer 1 — all projects |
| `evidence_card` | `build_project_evidence()` | layer 2a — all projects |

### At GitHub import (Phase 2 — to build)

Per README chunk row (SQLite table, not profile JSON):

| Field | Purpose |
| --- | --- |
| `user_id` | isolation |
| `project_id` | which project this chunk belongs to |
| `project_name` | retrieval display / embed prefix |
| `heading_path` | citation, e.g. `Engineering highlights` or `Agentic architecture > Parent graph pipeline` |
| `content` | chunk text |
| `token_count` | budget caps |
| `stack_tags` | optional; from evidence card `tech_stack` |
| `source_start` / `source_end` | optional offsets into `readme_md` |
| `embedding` | dense vector search |
| BM25 index entry | keyword search |

Phase 1 `evidence_card.evidence[]` claims are also retrieval units (no extra LLM
extraction required at import).

---

## `retrieve_project_evidence(job, profile)` output

Function returns a single **`EnrichJobInputBundle`** (name TBD in code) consumed
by `enrich_job`. Built per job, per user, with **no LLM**.

### 1. Job listing (from worker / prefilter)

Unchanged worker contract — only these listing fields are required:

```json
{
  "title": "string",
  "company": "string",
  "url": "string",
  "source_platform": "string",
  "description_text": "string"
}
```

### 2. Profile

| Field | Source | Notes |
| --- | --- | --- |
| `cv_text` | decrypted CV store | full text for fit analysis |
| `skills` | profile | extracted skill list |
| `target_roles` | profile | user intent |
| `cv_project_slots` | **CV parse** (deterministic) | see below |

#### `cv_project_slots` (parsed before LLM)

One entry per project line/entry on the CV project section:

```json
{
  "slot_index": 0,
  "cv_project_name": "JobPilot — Python side project",
  "chars_budget": 140,
  "matched_portfolio_project_id": "proj-abc123"
}
```

- `slot_index` — 0-based order on CV
- `chars_budget` — max characters for `swap_in_text` on this slot (from CV layout parse)
- `matched_portfolio_project_id` — optional; fuzzy/name match to imported portfolio when the same project exists under a weak or outdated CV line

**Swap rules (input context, not output):**

- Portfolio may have **more** projects than CV slots (e.g. 8 imported, 4 on CV).
- Maximum possible swaps = **CV slot count**, not portfolio size.
- Swap can replace with a **different** portfolio project or **refresh the same**
  project name using stronger evidenced text from import.
- Retrieval must support swap-in candidates **not currently on the CV**.

### 3. Portfolio evidence — two detail layers (one bundle)

#### Layer 1 — all portfolio projects (awareness)

**Every** imported project in the user profile. Small, always included.

```json
{
  "project_id": "proj-1",
  "name": "JobPilot",
  "repo_full_name": "alice/JobPilot",
  "portfolio_overview": "30-50 word overview from import"
}
```

Approx. **40–60 tokens per project**. For 8 projects ≈ 300–500 tokens total.

Purpose: full portfolio awareness so the model can consider swap-in projects
that did not receive README chunks.

#### Layer 2a — all portfolio projects (grounded cards)

**Every** imported project. Full `evidence_card` from Phase 1.

```json
{
  "project_id": "proj-1",
  "name": "JobPilot",
  "evidence_card": {
    "project_purpose": "...",
    "tech_stack": ["FastAPI", "LangGraph"],
    "architecture": ["..."],
    "key_features": ["..."],
    "role_relevance": ["..."],
    "evidence": [
      { "claim": "...", "source_section": "Engineering highlights" }
    ],
    "supported_metrics": [],
    "limitations_or_unknowns": ["..."]
  }
}
```

Approx. **200–400 tokens per project**. For 8 projects ≈ 1,600–3,200 tokens.

Purpose: grounded swap text, fit scoring, and claims with `source_section`
without sending full READMEs. Phase 1 cards intentionally omit granular README
detail (API routes, graph node names) — that is what layer 2b chunks recover.

#### Layer 2b — selected projects only (README chunks)

**Not** all projects. README chunks are bulky; include only for a **swap-aware
union** of projects, capped by portfolio size.

**Selection set** (`chunk_project_ids`):

```text
  top job-relevant portfolio projects     (hybrid search vs job description)
∪ portfolio project linked to each CV slot (cv_project_slots[].matched_portfolio_project_id)
∪ top portfolio projects NOT on CV        (swap-in candidates)
→ dedupe by project_id
→ cap project count (see budget table below)
```

**Per-project chunk cap:** ~1–2 chunks per selected project.

**Total chunk cap:** ~4–8 chunks across the whole job (not per project).

Each chunk in the bundle:

```json
{
  "project_id": "proj-1",
  "project_name": "JobPilot",
  "heading_path": "Engineering highlights",
  "content": "LangGraph parent + subgraphs, worker task queue (HTTP)...",
  "retrieval_score": 0.87,
  "source": "readme_chunk"
}
```

Claims from `evidence_card.evidence[]` may appear as lightweight candidates in
retrieval and as rerank inputs; they can be included in the bundle when they
score highly:

```json
{
  "project_id": "proj-1",
  "project_name": "JobPilot",
  "heading_path": "Agentic architecture",
  "content": "The system uses a deterministic LangGraph pipeline with a parent graph, search subgraph, prefilter, and parallel application subgraphs.",
  "source": "evidence_claim"
}
```

Every chunk/claim **must** carry `project_id` and `project_name` for swap
deduplication and UI citations.

---

## Retrieval mechanics (feeds layer 2b only)

Runs once per job inside `retrieve_project_evidence()` — **no LLM**.

```text
Job description_text (+ title)
        ↓
Search ALL user projects:
  - evidence_card fields + claims
  - README chunks (BM25 + dense vectors)
        ↓
Fuse (e.g. RRF) → top ~20–30 candidates (mixed projects)
        ↓
Rerank ONCE per job — all candidates together, not per project
        ↓
Map reranked chunks → chunk_project_ids union (job + CV slots + not-on-CV)
        ↓
Attach layer 1 + 2a for all projects + layer 2b for selected projects
```

### Hybrid search (Phase 2)

| Method | Why |
| --- | --- |
| **BM25 / keyword** | Exact tech names: FastAPI, LangGraph, `enrich_job`, PostgreSQL |
| **Dense vectors** | Conceptual fit: “task queue”, “agent orchestration”, “distributed workers” |
| **Reranker** | Optional Phase 2b; rerank fused top-20 across **all** projects in one batch |

Indexing (chunking, embeddings, BM25) happens at **import/refresh only**, not
during each job search.

### Chunking at import (Phase 2)

```text
readme_md
  → Markdown heading parents (hard boundaries)
  → child splits for long sections (~250–500 tokens, paragraph boundaries)
  → metadata + embeddings + BM25 index
```

v1 may use heading + paragraph splits; centroid-based semantic grouping is
optional tuning later.

Embed prefix per chunk:

```text
Project: JobPilot
Stack: FastAPI, LangGraph, React
Section: Engineering highlights
Content: ...
```

---

## Token budget

Target **~4,000–8,000 input tokens** per `enrich_job` call.

| Input section | Scope | Approx. tokens |
| --- | --- | ---: |
| System prompt + JSON rules | fixed | 400–700 |
| Job title + `description_text` | this listing | 500–1,500 |
| `cv_text` + `skills` + `target_roles` | profile | 1,000–2,000 |
| `cv_project_slots` | parsed | 100–300 |
| **Layer 1** — all `portfolio_overview` | all projects | 300–800 |
| **Layer 2a** — all `evidence_card` | all projects | 1,600–3,200 |
| **Layer 2b** — README chunks + top claims | selected projects only | 1,200–2,500 |
| **Total** | | **4,000–8,000** |

### Layer 2b project cap (scales slightly with portfolio)

README chunks attach to **projects**, not “top 2–3” globally without swap awareness.

```text
chunk_project_cap = min(8, max(4, ceil(portfolio_count * 0.6)))
```

| Portfolio projects | Projects receiving README chunks |
| ---: | ---: |
| ≤ 8 | 4–6 |
| 9–12 | 5–7 |
| 13–16 | 6–8 |
| 16+ | 8 (hard cap) |

Do **not** scale chunk projects 1:1 with portfolio size.

---

## Full bundle shape (illustrative)

What `enrich_job` receives after retrieval packs layers into **one** payload:

```json
{
  "job": {
    "title": "Senior Python Engineer",
    "company": "Acme",
    "url": "https://...",
    "source_platform": "linkedin",
    "description_text": "..."
  },
  "profile": {
    "cv_text": "...",
    "skills": ["Python", "FastAPI"],
    "target_roles": ["Backend Engineer"],
    "cv_project_slots": [
      {
        "slot_index": 0,
        "cv_project_name": "Todo App — Flask CRUD",
        "chars_budget": 120,
        "matched_portfolio_project_id": "proj-3"
      },
      {
        "slot_index": 1,
        "cv_project_name": "JobPilot — Python side project",
        "chars_budget": 140,
        "matched_portfolio_project_id": "proj-1"
      }
    ]
  },
  "portfolio": {
    "layer1_all_projects": [
      {
        "project_id": "proj-1",
        "name": "JobPilot",
        "repo_full_name": "alice/JobPilot",
        "portfolio_overview": "..."
      }
    ],
    "layer2a_all_evidence_cards": [
      {
        "project_id": "proj-1",
        "name": "JobPilot",
        "evidence_card": { }
      }
    ],
    "layer2b_selected_chunks": [
      {
        "project_id": "proj-1",
        "project_name": "JobPilot",
        "heading_path": "Engineering highlights",
        "content": "...",
        "source": "readme_chunk"
      },
      {
        "project_id": "proj-5",
        "project_name": "Search Helper Worker",
        "heading_path": "Architecture",
        "content": "...",
        "source": "readme_chunk"
      }
    ],
    "retrieval_meta": {
      "chunk_project_ids": ["proj-1", "proj-2", "proj-5"],
      "total_chunks": 5,
      "portfolio_count": 8
    }
  }
}
```

`retrieval_meta` is for logging/tests; omit from the LLM prompt if not needed.

---

## What the LLM prompt contains (single call)

Suggested section order in the user message:

```text
1. JOB — title, company, description_text, platform
2. PROFILE — cv_text, skills, target_roles
3. CV PROJECT SLOTS — slot_index, cv_project_name, chars_budget per slot
4. PORTFOLIO LAYER 1 — all portfolio_overview entries
5. PORTFOLIO LAYER 2a — all evidence_card objects
6. PORTFOLIO LAYER 2b — selected readme chunks + top claims (with project_id, heading_path)
7. TASK — return JSON only (see output contract in application-subagent doc)
```

---

## Design decisions recorded (2026-07-16 discussion)

| Topic | Decision |
| --- | --- |
| LLM calls | **One** `enrich_job` call; layers are prompt structure only |
| All projects in input? | **Yes** for overview + evidence card; **no** for full README chunks |
| Chunk project cap | ~4–8 projects (swap-aware union), scales slightly past 8 portfolio repos |
| Chunk count | ~4–8 chunks **total** per job, ~1–2 per selected project |
| Reranker scope | One rerank batch per job across **all** projects' candidates |
| Swap vs retrieval | Retrieval searches all portfolio projects; swap decisions are **per CV slot** |
| Same name on CV + portfolio | Weak CV line + strong import → may `swap` with same `swap_in_project` and better text |
| Phase 1 gaps | Cards miss API routes, graph nodes, module paths — chunks recover that detail |
| Worker contract | Unchanged — retrieval uses `description_text` only from listing |

---

## Phase 2 completion checklist (input path)

- [ ] README chunk table + import-time chunker
- [ ] BM25 + embedding index per user/project
- [ ] `retrieve_project_evidence(job, profile) → EnrichJobInputBundle`
- [ ] CV project slot parser → `cv_project_slots`
- [ ] Swap-aware `chunk_project_ids` selection
- [ ] Bundle packer for `enrich_job` prompt
- [ ] Eval fixtures: job → expected `chunk_project_ids` + expected `heading_path`s
