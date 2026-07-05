"""State contract for the search subgraph."""

from typing import TypedDict

from backend.app.graph.state import JobListing
from backend.app.models.browser import Platform, RawJobListing
from backend.app.models.search_prefs import JobAgePreset, WorkMode


class SearchState(TypedDict):
    """Subgraph memory used only while producing job listings."""

    run_id: int
    user_id: int
    role: str
    platform: Platform
    country: str
    work_mode: WorkMode
    max_listings: int
    job_age: JobAgePreset
    skills_summary: str
    task_id: str
    raw_listings: list[RawJobListing]
    listings: list[JobListing]
    warnings: list[str]
    errors: list[str]
