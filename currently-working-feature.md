# Currently Working On

**Active:** Search agent — design locked, implementation next.

→ [`docs/discussion/search-subgraph-discussion-and-finalization.md`](docs/discussion/search-subgraph-discussion-and-finalization.md) — **Agreed way to build the search agent** (architecture, stops, ECS↔worker contract, Helper UI, build order)

Related:

- [`docs/phase-a-step-1-contracts.md`](docs/phase-a-step-1-contracts.md) — Phase A contracts (complete)
- [`docs/discussion/discussion-agentic-design.md`](docs/discussion/discussion-agentic-design.md) — broader agent design discussion
- [`System Design/jobpilot-agent-build-guide.md`](System%20Design/jobpilot-agent-build-guide.md) — locked build phases

**Next code step:** ECS search subgraph (`enqueue_browser_task` → `wait_for_listings` → `normalize_listings` → `drop_applied`). Graph not wired to frontend yet.
