"""Parent fan-in node for search-run finalization."""

from backend.app.graph.state import RunState
from backend.app.observability import span
from backend.app.services.search_store import (
    finalize_search_run,
    get_search_run,
    update_search_run,
)


def persist(state: RunState) -> dict:
    """Finalize once all application branches have persisted their packages."""
    run_id = state["run_id"]
    errors = state.get("errors") or []
    if state.get("status") == "failed" or errors:
        run = get_search_run(run_id)
        if run and run["status"] not in ("failed", "completed"):
            update_search_run(
                run_id,
                status="failed",
                error=errors[0] if errors else "Search run failed.",
                finished=True,
            )
        return {"status": "failed"}

    with span("parent_finalization", search_run_id=run_id):
        finalize_search_run(run_id)
    return {"status": "completed"}
