# Project Evidence Portfolio Overview Addendum

**Status:** Design discussion — implementation deferred

This addendum extends
[`project-evidence-retrieval-discussion.md`](project-evidence-retrieval-discussion.md).
Refer to that document for the full README storage, hierarchical semantic
chunking, evidence-card, and hybrid-retrieval design.

## Decision: include an all-project portfolio overview

Each imported project should generate and store a short `portfolio_overview`
field alongside its evidence card. Generate both fields in the same GitHub
import/refresh LLM response; do not make another LLM call only for the
overview.

Each overview should be approximately 30–50 tokens and include the project
name, strongest stack or domain signals, and primary outcome. Example:

```text
JobPilot: FastAPI and LangGraph job-search platform with a desktop browser
worker and human-approved application workflow.
```

For every job-analysis call, provide the application sub-agent with the stored
portfolio overview for all user projects. This gives it broad awareness of the
complete portfolio and helps it identify when a relevant project may not be in
the detailed retrieval results.

Detailed evidence remains selective:

```text
Job description + CV/profile
    + all-project portfolio overview
    + top 2–3 retrieved evidence cards
    + selected supporting README chunks
        ↓
Application sub-agent: score fit and recommend keep/swap
```

The all-project overview is for awareness, not proof. Scores, project-swap
decisions, and CV rewrite claims must be grounded in the CV plus the selected
detailed evidence cards, atomic claims, and README source chunks.

## Per-job context budget

| Context sent for one job | Approx. tokens |
| --- | ---: |
| System prompt + JSON rules | 400–700 |
| Job title + description | 500–1,500 |
| CV/profile summary | 1,000–2,000 |
| All-project portfolio overview | 300–800 |
| Top 2–3 evidence cards | 600–1,200 |
| Retrieved README evidence chunks | 1,200–2,500 |
| **Total per job** | **4,000–8,000** |

For eight application-agent calls, the all-project overview adds approximately
2,400–6,400 input tokens in total. The overview itself is generated once at
project import and then reused for every future job analysis.
