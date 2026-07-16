"""Structured project evidence produced at GitHub import."""

from pydantic import BaseModel, ConfigDict, Field


class ProjectEvidenceClaim(BaseModel):
    """One README-grounded fact with traceable source section."""

    claim: str
    source_section: str = Field(alias="sourceSection")

    model_config = ConfigDict(populate_by_name=True)


class ProjectEvidenceCard(BaseModel):
    """Compact, source-grounded project knowledge for retrieval and swap suggestions."""

    project_purpose: str = Field(alias="projectPurpose")
    tech_stack: list[str] = Field(default_factory=list, alias="techStack")
    architecture: list[str] = Field(default_factory=list)
    key_features: list[str] = Field(default_factory=list, alias="keyFeatures")
    role_relevance: list[str] = Field(default_factory=list, alias="roleRelevance")
    evidence: list[ProjectEvidenceClaim] = Field(default_factory=list)
    supported_metrics: list[str] = Field(default_factory=list, alias="supportedMetrics")
    limitations_or_unknowns: list[str] = Field(
        default_factory=list, alias="limitationsOrUnknowns"
    )

    model_config = ConfigDict(populate_by_name=True)


class ProjectEvidenceResult(BaseModel):
    """Validated LLM output from build_project_evidence()."""

    name: str
    description: str
    repo_skills: list[str] = Field(default_factory=list, alias="repoSkills")
    portfolio_overview: str = Field(alias="portfolioOverview")
    evidence_card: ProjectEvidenceCard = Field(alias="evidenceCard")

    model_config = ConfigDict(populate_by_name=True)
