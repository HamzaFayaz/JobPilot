"""Application subgraph — per-job enrich + package (stub)."""

from langgraph.graph import END, START, StateGraph

from backend.app.graph.subgraphs.application.state import ApplicationState


def enrich_job(state: ApplicationState) -> dict:
    pass


def score_threshold_gate(state: ApplicationState) -> dict:
    pass


def package_out(state: ApplicationState) -> dict:
    pass


def build_application_subgraph():
    builder = StateGraph(ApplicationState)

    builder.add_node("enrich_job", enrich_job)
    builder.add_node("score_threshold_gate", score_threshold_gate)
    builder.add_node("package_out", package_out)

    builder.add_edge(START, "enrich_job")
    builder.add_edge("enrich_job", "score_threshold_gate")
    builder.add_edge("score_threshold_gate", "package_out")
    builder.add_edge("package_out", END)

    return builder.compile()
