# Cursor Guidance

- Check whether a proposed change is necessary for the complete JobPilot system, not just for a short demo.
- Prefer the simplest solution that keeps the full system architecture correct.
- Avoid extra abstraction, protocols, nodes, tables, realtime infrastructure, or polish unless they solve a current system need.
- Do not build demo-only shortcuts if they move the codebase away from the intended full-system design.
- When a suggestion feels complex, ask whether it is required now or premature.
- Prefer end-to-end working flow over sophisticated but partial architecture.
- Keep frontend, backend, database, and agent design aligned around one source of truth.
- Defer speculative work cleanly instead of adding scaffolding for it.
