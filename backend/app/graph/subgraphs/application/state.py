"""State contract for the application subgraph."""

from typing import NotRequired, Required, TypedDict

from backend.app.graph.state import JobListing, ProfileState
class ApplicationState(TypedDict, total=False):
    """Subgraph memory for scoring and packaging a single job."""

    run_id: Required[int]
    user_id: Required[int]
    job: Required[JobListing]
    profile: Required[ProfileState]
    validation_context: NotRequired[dict]
    eval_payload: NotRequired[dict]
    enrich_result: NotRequired[dict]
    classified_result: NotRequired[dict]
    package_id: NotRequired[int]
    packages: NotRequired[list[dict]]
    stage_status: NotRequired[str]
    error: NotRequired[dict]


class ApplicationOutputState(TypedDict):
    packages: list[dict]
