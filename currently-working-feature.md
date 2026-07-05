# Currently Working On

**Active:** Search agent — migrate Search Helper from Browser-Use to **Kimi WebBridge**.

→ [`System Design/kimi-webbridge-provider.md`](System%20Design/kimi-webbridge-provider.md) — **WebBridge setup, architecture, migration checklist**

→ [`docs/discussion/search-subgraph-discussion-and-finalization.md`](docs/discussion/search-subgraph-discussion-and-finalization.md) — search agent build agreement (ECS subgraph + worker contract)

Related:

- [`docs/phase-a-step-1-contracts.md`](docs/phase-a-step-1-contracts.md) — Phase A contracts (complete)
- [`docs/discussion/discussion-agentic-design.md`](docs/discussion/discussion-agentic-design.md) — broader agent design discussion
- [`System Design/jobpilot-agent-build-guide.md`](System%20Design/jobpilot-agent-build-guide.md) — locked build phases
- [`System Design/browser-provider-abstraction.md`](System%20Design/browser-provider-abstraction.md) — provider interface (WebBridge v1)

**Next code step:** Implement `worker/providers/webbridge.py` + Qwen agent loop; then wire ECS search subgraph if not complete.
