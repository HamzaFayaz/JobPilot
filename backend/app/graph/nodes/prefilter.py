"""Parent graph node — normalize, dedupe, and drop already-applied listings."""

from backend.app.graph.state import RunState
from backend.app.services.listing_prefilter import run_prefilter
from backend.app.services.search_store import seed_analyzing_packages


def prefilter(state: RunState) -> dict:
    if state.get("status") == "failed" or state.get("errors"):
        return {}

    raw_listings = state.get("raw_listings") or []
    listings, matched_jobs = run_prefilter(raw_listings, user_id=state["user_id"])
    if matched_jobs:
        seed_analyzing_packages(state["run_id"], state["user_id"], matched_jobs)
    return {
        "listings": listings,
        "matched_jobs": matched_jobs,
    }
