"""Search subgraph — enqueue task and wait for worker result."""

import uuid

from langgraph.graph import END, START, StateGraph

from backend.app.graph.subgraphs.search.state import SearchState
from backend.app.models.browser import RawJobListing
from backend.app.services.search_store import update_search_run
from backend.app.services.worker_store import (
    build_task_payload,
    create_worker_task,
    get_active_worker_device,
    wait_for_worker_task_result,
)


def enqueue_browser_task(state: SearchState) -> dict:
    """Create a browser_search worker task for the paired Search Helper."""
    run_id = state["run_id"]
    user_id = state["user_id"]

    device = get_active_worker_device(user_id)
    if not device:
        message = "Search Helper not connected."
        update_search_run(run_id, status="failed", error=message, finished=True)
        return {"errors": [message], "task_id": ""}

    task_id = str(uuid.uuid4())
    payload = build_task_payload(
        task_id=task_id,
        run_id=run_id,
        role=state["role"],
        platform=state["platform"],
        country=state["country"],
        work_mode=state["work_mode"],
        max_listings=state["max_listings"],
        job_age=state["job_age"],
        skills_summary=state.get("skills_summary") or "",
    )
    create_worker_task(
        task_id=task_id,
        user_id=user_id,
        run_id=run_id,
        payload=payload,
    )
    return {"task_id": task_id, "errors": []}


def wait_for_listings(state: SearchState) -> dict:
    """Wait for the worker to POST raw listings, without preprocessing yet."""
    if state.get("errors"):
        return {}

    task_id = state.get("task_id") or ""
    if not task_id:
        message = "Missing worker task id."
        update_search_run(
            state["run_id"],
            status="failed",
            error=message,
            finished=True,
        )
        return {"errors": [message]}

    outcome = wait_for_worker_task_result(task_id)
    if outcome["status"] == "failed":
        message = outcome["error"]
        update_search_run(
            state["run_id"],
            status="failed",
            error=message,
            finished=True,
        )
        return {"errors": [message]}

    result = outcome["result"]
    raw_listings = [
        RawJobListing.model_validate(item) for item in result.get("listings", [])
    ]
    warnings = outcome.get("warnings") or result.get("warnings") or []
    return {
        "raw_listings": raw_listings,
        "warnings": warnings,
        "errors": [],
    }


def build_search_subgraph():
    builder = StateGraph(SearchState)

    builder.add_node("enqueue_browser_task", enqueue_browser_task)
    builder.add_node("wait_for_listings", wait_for_listings)

    builder.add_edge(START, "enqueue_browser_task")
    builder.add_edge("enqueue_browser_task", "wait_for_listings")
    builder.add_edge("wait_for_listings", END)

    return builder.compile()
