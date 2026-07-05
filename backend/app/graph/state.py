"""Shared typed state contracts for the JobPilot graph."""

import operator
from typing import Annotated, TypedDict

from backend.app.models.browser import Platform, RawJobListing
from backend.app.models.search_prefs import JobAgePreset, WorkMode
from backend.app.models.search import CvDecision, JobPackageStatus, RunStatus


class ProjectState(TypedDict):
    """Project data carried into search/application graph execution."""

    id: str
    name: str
    description: str
    source: str | None
    repo_full_name: str | None
    readme_md: str | None
    chars_per_line: int | None


class ProfileState(TypedDict):
    """Profile snapshot used while a search run is executing."""

    cv_text: str
    skills: list[str]
    target_roles: list[str]
    projects: list[ProjectState]


class JobListing(TypedDict):
    """Normalized job listing shape after browser output is cleaned."""

    title: str
    company: str
    url: str
    platform: Platform
    description_text: str


class JobPackageState(TypedDict):
    """Per-job result accumulated by the application subgraph."""

    job: JobListing
    run_id: int
    match_score: int
    cv_decision: CvDecision
    swap_out_project: str | None
    swap_in_text: str | None
    current_cv_score: int
    suggested_cv_score: int
    draft_email: str
    status: JobPackageStatus
    error: str | None


class AppliedJobState(TypedDict):
    """Dedupe memory for jobs that were already applied to."""

    url: str
    platform: Platform
    title: str
    company: str
    applied_at: str
    cv_version: str


class RunState(TypedDict):
    """Parent graph memory for a full search run."""

    run_id: int
    user_id: int
    role: str
    platform: Platform
    country: str
    work_mode: WorkMode
    max_listings: int
    job_age: JobAgePreset
    profile: ProfileState
    listings: list[JobListing]
    raw_listings: list[RawJobListing]
    warnings: list[str]
    matched_jobs: list[JobListing]
    packages: Annotated[list[JobPackageState], operator.add]
    errors: list[str]
    status: RunStatus
