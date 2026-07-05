"""Parent LangGraph orchestrator — node names and edges only."""

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from backend.app.graph.nodes.init_run import init_run
from backend.app.graph.state import RunState
from backend.app.services.search_store import get_search_run, save_raw_listings_as_packages, update_search_run
from backend.app.graph.subgraphs.application.graph import build_application_subgraph
from backend.app.graph.subgraphs.search.graph import build_search_subgraph
from backend.app.graph.subgraphs.search.state import SearchState

_compiled_search_subgraph = build_search_subgraph()


def _route_after_init(state: RunState) -> str:
    if state.get("status") == "failed":
        return END
    return "search_subgraph"


def _skills_summary(profile: RunState["profile"]) -> str:
    skills = profile.get("skills") or []
    return ", ".join(skills)


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
        "skills_summary": _skills_summary(state["profile"]),
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

    return updates


def prefilter(state: RunState) -> dict:
    """Placeholder until listing normalization and scoring are implemented."""
    return {}


def persist(state: RunState) -> dict:
    """Save browser listings and mark the run complete for the current E2E slice."""
    run_id = state["run_id"]
    user_id = state["user_id"]
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

    raw_listings = state.get("raw_listings") or []
    if raw_listings:
        save_raw_listings_as_packages(run_id, user_id, raw_listings)
        return {"status": "completed"}

    run = get_search_run(run_id)
    if run and run["status"] not in ("failed", "completed"):
        update_search_run(run_id, status="completed", finished=True)

    return {"status": "completed"}


def fan_out_applications(state: RunState) -> list[Send] | str:
    matched_jobs = state.get("matched_jobs") or []
    if not matched_jobs:
        return "persist"
    return [
        Send(
            "application_subgraph",
            {
                "run_id": state["run_id"],
                "user_id": state["user_id"],
                "job": job,
                "profile": state["profile"],
            },
        )
        for job in matched_jobs
    ]


def build_parent_graph():
    builder = StateGraph(RunState)

    builder.add_node("init_run", init_run)
    builder.add_node("search_subgraph", search_subgraph)
    builder.add_node("prefilter", prefilter)
    builder.add_node("application_subgraph", build_application_subgraph())
    builder.add_node("persist", persist)

    builder.add_edge(START, "init_run")
    builder.add_conditional_edges(
        "init_run",
        _route_after_init,
        ["search_subgraph", END],
    )
    builder.add_edge("search_subgraph", "prefilter")
    builder.add_conditional_edges(
        "prefilter",
        fan_out_applications,
        ["application_subgraph", "persist"],
    )
    builder.add_edge("application_subgraph", "persist")
    builder.add_edge("persist", END)

    return builder.compile()


compiled_graph = build_parent_graph()
