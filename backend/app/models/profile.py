"""Pydantic schemas for profile API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.browser import Platform
from backend.app.models.project_evidence import ProjectEvidenceCard
from backend.app.models.search_prefs import (
    DEFAULT_JOB_AGE,
    DEFAULT_MAX_LISTINGS,
    DEFAULT_WORK_MODE,
    JobAgePreset,
    WorkMode,
    clamp_max_listings,
)

SkillsExtractionStatus = Literal["idle", "pending", "ready", "failed"]
ProjectSource = Literal["manual", "github"]

# Max README bytes stored per GitHub project (server-side only).
README_MAX_CHARS = 65_536


class Project(BaseModel):
    """Project fields exposed to the frontend API."""

    id: str
    name: str
    description: str
    source: ProjectSource | None = None
    repo_full_name: str | None = Field(None, alias="repoFullName")

    model_config = ConfigDict(populate_by_name=True)


class StoredProject(Project):
    """Full project record persisted in SQLite (includes server-only fields)."""

    readme_md: str | None = Field(None, alias="readmeMd")
    portfolio_overview: str | None = Field(None, alias="portfolioOverview")
    evidence_card: ProjectEvidenceCard | None = Field(None, alias="evidenceCard")

    model_config = ConfigDict(populate_by_name=True)

    def to_api(self) -> Project:
        return Project(
            id=self.id,
            name=self.name,
            description=self.description,
            source=self.source,
            repo_full_name=self.repo_full_name,
        )


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    target_roles: list[str] | None = Field(None, alias="targetRoles")
    search_role: str | None = Field(None, alias="searchRole")
    search_platform: Platform | None = Field(None, alias="searchPlatform")
    search_country: str | None = Field(None, alias="searchCountry")
    search_work_mode: WorkMode | None = Field(None, alias="searchWorkMode")
    search_max_listings: int | None = Field(None, alias="searchMaxListings")
    search_job_age: JobAgePreset | None = Field(None, alias="searchJobAge")
    projects: list[Project] | None = None


class ProfileResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    cv_filename: str | None = Field(None, alias="cvFilename")
    cv_file_meta: dict | None = Field(None, alias="cvFileMeta")
    skills: list[str] = []
    skills_extraction_status: SkillsExtractionStatus = Field(
        "idle", alias="skillsExtractionStatus"
    )
    target_roles: list[str] = Field(default_factory=list, alias="targetRoles")
    search_role: str | None = Field(None, alias="searchRole")
    search_platform: Platform = Field("linkedin", alias="searchPlatform")
    search_country: str | None = Field(None, alias="searchCountry")
    search_work_mode: WorkMode = Field(DEFAULT_WORK_MODE, alias="searchWorkMode")
    search_max_listings: int = Field(DEFAULT_MAX_LISTINGS, alias="searchMaxListings")
    search_job_age: JobAgePreset = Field(DEFAULT_JOB_AGE, alias="searchJobAge")
    projects: list[Project] = []
    gmail_connected: bool = Field(False, alias="gmailConnected")
    gmail_email: str | None = Field(None, alias="gmailEmail")
    github_connected: bool = Field(False, alias="githubConnected")
    github_username: str | None = Field(None, alias="githubUsername")
    updated_at: datetime | None = Field(None, alias="updatedAt")
