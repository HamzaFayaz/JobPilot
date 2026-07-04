"""State contract for the search subgraph."""

from typing import TypedDict

from backend.app.graph.state import JobListing
from backend.app.models.browser import Platform, RawJobListing


class SearchState(TypedDict):
    """Subgraph memory used only while producing job listings."""

    run_id: int
    user_id: int
    role: str
    platform: Platform
    raw_listings: list[RawJobListing]
    listings: list[JobListing]
    errors: list[str]
