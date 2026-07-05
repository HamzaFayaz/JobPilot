"""Background graph execution for search runs."""

import logging

from backend.app.graph.orchestrator import compiled_graph
from backend.app.graph.state import RunState
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


def run_parent_graph(run_id: int, user_id: int) -> None:
    """Execute the parent LangGraph for one search run."""
    logger.info("Starting parent graph for run_id=%s user_id=%s", run_id, user_id)
    try:
        compiled_graph.invoke(_initial_run_state(run_id, user_id))
    except Exception as exc:
        logger.exception("Parent graph failed for run_id=%s", run_id)
        update_search_run(run_id, status="failed", error=str(exc), finished=True)
