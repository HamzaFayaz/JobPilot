"""Pydantic schemas for search and jobs APIs."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.browser import Platform

RunStatus = Literal["pending", "running", "completed", "failed"]
JobPackageStatus = Literal["analyzing", "ready", "applied", "skipped", "failed"]
CvDecision = Literal["keep", "swap"]
JobDecisionAction = Literal["applied", "skipped"]


class JobDecisionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    decision: JobDecisionAction


class SearchStartResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    run_id: int = Field(alias="runId")
    status: RunStatus


class SearchRunStatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    run_id: int = Field(alias="runId")
    status: RunStatus
    jobs_ready_count: int = Field(0, alias="jobsReadyCount")
    progress: float | None = None
    error: str | None = None


class JobListingResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    title: str
    company: str
    url: str
    platform: Platform
    description_text: str = Field(default="", alias="descriptionText")


class JobPackageResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int | None = None
    run_id: int | None = Field(default=None, alias="runId")
    title: str
    company: str
    url: str
    platform: Platform
    description_text: str = Field(default="", alias="descriptionText")
    summary: str = ""
    match_score: int | None = Field(default=None, alias="matchScore")
    current_cv_score: int | None = Field(default=None, alias="currentCvScore")
    suggested_cv_score: int | None = Field(default=None, alias="suggestedCvScore")
    cv_decision: CvDecision | None = Field(default=None, alias="cvDecision")
    swap_out_project: str | None = Field(default=None, alias="swapOutProject")
    swap_in_text: str | None = Field(default=None, alias="swapInText")
    draft_email: str = Field(default="", alias="draftEmail")
    analysis: dict = Field(default_factory=dict)
    model_name: str | None = Field(default=None, alias="modelName")
    prompt_version: str | None = Field(default=None, alias="promptVersion")
    status: JobPackageStatus = "ready"
    error: str | None = None
    created_at: datetime | None = Field(default=None, alias="createdAt")
    updated_at: datetime | None = Field(default=None, alias="updatedAt")
