"""Pydantic schemas for browser-facing search contracts."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.search_prefs import (
    DEFAULT_JOB_AGE,
    DEFAULT_MAX_LISTINGS,
    job_age_to_days,
)

Platform = Literal["linkedin", "indeed"]


class BrowserHealth(str, Enum):
    READY = "ready"
    NOT_INSTALLED = "not_installed"
    DAEMON_DOWN = "daemon_down"
    PROFILE_SETUP = "profile_setup"
    BUSY = "busy"
    ERROR = "error"


class RawJobListing(BaseModel):
    """Browser provider output before normalization and dedupe."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    title: str
    company: str
    url: str
    description_text: str = Field(default="", alias="descriptionText")
    # UI-only formatted body (+ apply header). Analysis always uses description_text.
    display_description_text: str = Field(default="", alias="displayDescriptionText")
    source_platform: Platform = Field(alias="sourcePlatform")


class SearchListingsRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    role: str
    platform: Platform
    country: str = ""
    work_mode: str = "both"
    max_listings: int = Field(DEFAULT_MAX_LISTINGS, alias="maxListings")
    job_age: str = Field(DEFAULT_JOB_AGE, alias="jobAge")
    max_job_age_days: int = Field(
        job_age_to_days(DEFAULT_JOB_AGE),
        alias="maxJobAgeDays",
    )
    max_pages: int = Field(3, alias="maxPages")
    skills_summary: str = Field(default="", alias="skillsSummary")


class SearchListingsResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    listings: list[RawJobListing] = Field(default_factory=list)
    provider: str
    duration_ms: int = Field(alias="durationMs")
    warnings: list[str] = Field(default_factory=list)
