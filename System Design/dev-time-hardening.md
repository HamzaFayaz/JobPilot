# JobPilot — Dev-Time Hardening (Handle During Build)

**Related:** [JobPilot-System-Design.md](./JobPilot-System-Design.md) · [design-decisions.md](./design-decisions.md)

These gaps are real but do not block starting implementation. Address them naturally as you write `state.py`, graph nodes, and API routes. No need to lock them in the main design doc upfront.

---

## 1. `user_id` in run state

**Gap:** No `user_id` in `RunState` — cannot correlate runs across concurrent users.

**When to handle:** **Now** — active phase (login/signup + per-user profiles).

**Approach:** Add `users` table; scope `profiles`, `oauth_tokens`, uploads, and graph state by `user_id`. See [`currently-working-feature.md`](../currently-working-feature.md).

---

## 2. Strict types for `status` and `cv_decision`

**Gap:** `JobPackage.status` and `cv_decision` are documented as `"ready" | "applied" | "failed"` and `"keep" | "swap"` but typed as plain `str`. Qwen may return variants (`"Keep"`, `"swap_project"`, etc.).

**When to handle:** First pass on `app/graph/state.py`.

**Recommended fix:**

```python
from typing import Literal

CvDecision = Literal["keep", "swap"]
PackageStatus = Literal["ready", "applied", "failed"]

class JobPackage(TypedDict):
    ...
    cv_decision: CvDecision
    status: PackageStatus
```

- Validate and normalize LLM JSON in `application.py` before writing to state (e.g. lower-case, map aliases).
- Use Pydantic models for LLM output parsing if you want runtime validation with clear error messages.

---

## 3. Explicit `Profile` model (replace `profile: dict`)

**Gap:** `profile: dict` in `RunState` is a black box. Every node must know key names implicitly.

**When to handle:** When creating `state.py` alongside `RunState`.

**Recommended shape:**

```python
class Project(TypedDict):
    name: str
    description: str          # full text as it appears in CV
    chars_per_line: int | None  # optional precomputed for swap formatting

class Profile(TypedDict):
    cv_text: str
    skills: list[str]
    projects: list[Project]

class RunState(TypedDict):
    run_id: str
    ...
    profile: Profile
```

GitHub scanner stays post-MVP; user maintains projects manually via `POST /profile`.

---

## 4. LangGraph `Send` parallelism (wire-up detail)

**Gap:** Main design mentions fan-out via LangGraph `Send` API (Section 10) but the overview diagram does not show it. Serial processing of 10 jobs will make the demo painfully slow.

**When to handle:** When implementing `match.py` → `application.py` routing in `orchestrator.py`.

**Intended pattern:**

```python
from langgraph.types import Send

def route_to_application(state: RunState):
    passing_jobs = state["matched_jobs"]  # after prefilter + cap N
    return [Send("application", {"job": job, "profile": state["profile"]}) for job in passing_jobs]
```

- `match.py` node: prefilter, optional cap to top N, emit list of jobs to process.
- Conditional edge from `match` fans out one `application` node invocation per job.
- Results merge back into `state["packages"]` via LangGraph's reducer on that field.

**Verify:** After compile, run `graph.get_graph().draw_mermaid()` and confirm parallel fan-out appears in the generated diagram.

---

## 5. Match prefilter mechanism (already decided — implement it)

**Gap:** Section 13 of the main doc still lists prefilter as an open question, but Sections 2 and 10 already specify keyword/skills overlap then LLM score.

**When to handle:** `app/graph/nodes/match.py`.

**Locked approach (no change needed in main doc):**

1. **Stage 1 (free):** Tokenize JD + user `skills`; require minimum overlap (e.g. ≥2 skill hits or ≥30% of listed skills). Drop obvious non-matches with zero API cost.
2. **Stage 2 (LLM):** Application sub-agent scores only survivors; drop below threshold (e.g. &lt;60).
3. **Cap:** Process top N by prefilter score or first N survivors (e.g. N=8 for demo).

Do not add embedding similarity for MVP — keeps scope and infra minimal.

---

## 6. Per-job error propagation to UI

**Gap:** `RunState.errors: list[str]` exists but no API surfaces per-job failures. If sub-agent fails on job 3 of 8, the user may see 7 jobs and no explanation.

**When to handle:** `application.py` error handling + `GET /jobs` response shape.

**Recommended approach:**

```python
class JobPackage(TypedDict):
    ...
    status: PackageStatus       # "failed" when sub-agent errors
    error: str | None           # human-readable message for UI
```

- On sub-agent exception: write a `JobPackage` with `status: "failed"`, `error: "Scoring timed out"`, minimal job metadata — or skip the package and append to `run.errors` with `job_id`.
- `GET /jobs?run_id=...` returns both `ready` and `failed` packages so the UI can show "3 jobs ready, 1 failed".
- Optional: `GET /runs/{run_id}/errors` for run-level errors (browser crash, search timeout) separate from per-job failures.

---

## Checklist (during implementation)

| Item | File(s) | Priority |
|------|---------|----------|
| `Literal` / Pydantic for enums | `state.py`, `application.py` | Early |
| `Profile` + `Project` TypedDict | `state.py` | Early |
| `Send` fan-out in orchestrator | `orchestrator.py`, `match.py` | Before demo |
| Keyword prefilter | `match.py` | Before demo |
| `error` on failed `JobPackage` | `application.py`, `routes/jobs.py` | Before UI integration |
| `user_id` | everywhere | Post-MVP |
