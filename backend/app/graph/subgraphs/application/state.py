"""State contract for the application subgraph."""

from typing import TypedDict

from backend.app.graph.state import JobListing, ProfileState
from backend.app.models.search import CvDecision, JobPackageStatus


class ApplicationState(TypedDict):
    """Subgraph memory for scoring and packaging a single job."""

    run_id: int
    user_id: int
    job: JobListing
    profile: ProfileState
    match_score: int | None
    cv_decision: CvDecision | None
    swap_out_project: str | None
    swap_in_text: str | None
    current_cv_score: int | None
    suggested_cv_score: int | None
    draft_email: str | None
    status: JobPackageStatus
    error: str | None
