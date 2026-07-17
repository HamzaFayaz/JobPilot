"""Parent node adapter for the worker-backed search subgraph."""

from backend.app.graph.state import RunState
from backend.app.graph.subgraphs.search.graph import build_search_subgraph
from backend.app.graph.subgraphs.search.state import SearchState
from backend.app.services.search_store import get_search_run, update_search_run

_compiled_search_subgraph = build_search_subgraph()


def search_subgraph(state: RunState) -> dict:
    search_input: SearchState = {
        "run_id": state["run_id"],
        "user_id": state["user_id"],
        "role": state["role"],
        "platform": state["platform"],
        "country": state["country"],
        "work_mode": state["work_mode"],
        "max_listings": state["max_listings"],
        "job_age": state["job_age"],
        "skills_summary": ", ".join(state["profile"].get("skills") or []),
        "task_id": "",
        "raw_listings": [],
        "listings": [],
        "warnings": [],
        "errors": [],
    }
    result = _compiled_search_subgraph.invoke(search_input)
    errors = (state.get("errors") or []) + (result.get("errors") or [])
    updates: dict = {
        "raw_listings": result.get("raw_listings") or [],
        "listings": [],
        "warnings": result.get("warnings") or [],
        "errors": errors,
    }
    if errors:
        run = get_search_run(state["run_id"])
        if run and run["status"] not in ("failed", "completed"):
            update_search_run(
                state["run_id"],
                status="failed",
                error=errors[0],
                finished=True,
            )
        updates["status"] = "failed"
    return updates
