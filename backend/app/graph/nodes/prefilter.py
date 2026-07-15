"""Parent graph node — normalize, dedupe, and drop already-applied listings."""

from backend.app.graph.state import RunState
from backend.app.services.listing_prefilter import run_prefilter


def prefilter(state: RunState) -> dict:
    if state.get("status") == "failed" or state.get("errors"):
        return {}

    raw_listings = state.get("raw_listings") or []
    listings, matched_jobs = run_prefilter(raw_listings, user_id=state["user_id"])
    return {
        "listings": listings,
        "matched_jobs": matched_jobs,
    }
