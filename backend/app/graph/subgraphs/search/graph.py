"""Search subgraph — browser task boundary (stub)."""

from langgraph.graph import END, START, StateGraph

from backend.app.graph.subgraphs.search.state import SearchState


def enqueue_browser_task(state: SearchState) -> dict:
    pass


def wait_for_listings(state: SearchState) -> dict:
    pass


def normalize_listings(state: SearchState) -> dict:
    pass


def drop_applied(state: SearchState) -> dict:
    pass


def build_search_subgraph():
    builder = StateGraph(SearchState)

    builder.add_node("enqueue_browser_task", enqueue_browser_task)
    builder.add_node("wait_for_listings", wait_for_listings)
    builder.add_node("normalize_listings", normalize_listings)
    builder.add_node("drop_applied", drop_applied)

    builder.add_edge(START, "enqueue_browser_task")
    builder.add_edge("enqueue_browser_task", "wait_for_listings")
    builder.add_edge("wait_for_listings", "normalize_listings")
    builder.add_edge("normalize_listings", "drop_applied")
    builder.add_edge("drop_applied", END)

    return builder.compile()
