"""Parent LangGraph assembly and routing."""

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from backend.app.graph.nodes import init_run, persist, prefilter, search_subgraph
from backend.app.graph.state import RunState
from backend.app.graph.subgraphs.application.graph import build_application_subgraph


def _route_after_init(state: RunState) -> str:
    return END if state.get("status") == "failed" else "search_subgraph"


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
        "init_run", _route_after_init, ["search_subgraph", END]
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
