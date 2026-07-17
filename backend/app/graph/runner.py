"""Background graph execution for search runs."""

import logging
import threading

from backend.app.graph.orchestrator import compiled_graph
from backend.app.graph.state import RunState
from backend.app.observability import span
from backend.app.services.search_store import update_search_run

logger = logging.getLogger(__name__)


def _initial_run_state(run_id: int, user_id: int) -> RunState:
    return RunState(
        run_id=run_id,
        user_id=user_id,
        role="",
        platform="linkedin",
        country="",
        work_mode="both",
        max_listings=8,
        job_age="week",
        profile={
            "cv_text": "",
            "skills": [],
            "target_roles": [],
            "projects": [],
        },
        listings=[],
        raw_listings=[],
        warnings=[],
        matched_jobs=[],
        packages=[],
        errors=[],
        status="pending",
    )


def _execute_graph(run_id: int, user_id: int) -> None:
    """Run LangGraph in a worker thread so ECS can keep serving heartbeats."""
    logger.info("Starting parent graph for run_id=%s user_id=%s", run_id, user_id)
    try:
        with span(
            "background_graph_run",
            search_run_id=run_id,
            user_id=user_id,
        ):
            compiled_graph.invoke(_initial_run_state(run_id, user_id))
    except Exception as exc:
        logger.exception("Parent graph failed for run_id=%s", run_id)
        update_search_run(run_id, status="failed", error=str(exc), finished=True)


def run_parent_graph(run_id: int, user_id: int) -> None:
    """Kick off graph execution without blocking the API request thread."""
    thread = threading.Thread(
        target=_execute_graph,
        args=(run_id, user_id),
        name=f"jobpilot-graph-{run_id}",
        daemon=True,
    )
    thread.start()
