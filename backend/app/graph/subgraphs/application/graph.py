"""Application subgraph assembly."""

from langgraph.graph import END, START, StateGraph

from backend.app.graph.subgraphs.application.nodes import (
    classify_fit,
    enrich_job,
    package_out,
)
from backend.app.graph.subgraphs.application.state import (
    ApplicationOutputState,
    ApplicationState,
)


def build_application_subgraph():
    builder = StateGraph(ApplicationState, output_schema=ApplicationOutputState)
    builder.add_node("enrich_job", enrich_job)
    builder.add_node("classify_fit", classify_fit)
    builder.add_node("package_out", package_out)
    builder.add_edge(START, "enrich_job")
    builder.add_edge("enrich_job", "classify_fit")
    builder.add_edge("classify_fit", "package_out")
    builder.add_edge("package_out", END)
    return builder.compile()
