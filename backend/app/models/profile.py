"""Pydantic schemas for profile API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SkillsExtractionStatus = Literal["idle", "pending", "ready", "failed"]
ProjectSource = Literal["manual", "github"]


class Project(BaseModel):
    id: str
    name: str
    description: str
    source: ProjectSource | None = None


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    target_roles: list[str] | None = Field(None, alias="targetRoles")
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
    projects: list[Project] = []
    gmail_connected: bool = Field(False, alias="gmailConnected")
    gmail_email: str | None = Field(None, alias="gmailEmail")
    github_connected: bool = Field(False, alias="githubConnected")
    github_username: str | None = Field(None, alias="githubUsername")
    updated_at: datetime | None = Field(None, alias="updatedAt")
