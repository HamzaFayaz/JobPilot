"""Strict structured contracts for per-job application analysis."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

AnalysisStatus = Literal["completed", "insufficient_job_detail"]
RequirementImportance = Literal["required", "preferred", "general"]
RequirementCategory = Literal[
    "skill",
    "experience",
    "responsibility",
    "education",
    "location_or_work_mode",
    "eligibility",
    "other",
]
RequirementStatus = Literal["matched", "partial", "not_evidenced", "cannot_assess"]
Confidence = Literal["low", "medium", "high"]
EvidenceSourceType = Literal["cv", "readme_chunk"]
ProjectAction = Literal["keep", "swap"]
SwapImpact = Literal["low", "medium", "high"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class EvidenceReference(StrictModel):
    source_type: EvidenceSourceType
    quote: str = Field(min_length=1)
    cv_section: str | None
    project_id: str | None
    project_name: str | None
    heading_path: str | None
    source_id: str | None
    cv_span_id: str | None

    @model_validator(mode="after")
    def validate_source_identity(self) -> "EvidenceReference":
        if self.source_type == "cv":
            if not self.cv_span_id or self.source_id is not None:
                raise ValueError("CV evidence requires cv_span_id only")
        elif not self.source_id or self.cv_span_id is not None:
            raise ValueError("non-CV evidence requires an exact source_id")
        return self


class RequirementAssessment(StrictModel):
    requirement_id: str
    retrieval_requirement_id: str | None
    job_quote: str = Field(min_length=1)
    job_source_start: int = Field(ge=0)
    job_source_end: int = Field(gt=0)
    text: str
    importance: RequirementImportance
    category: RequirementCategory
    status: RequirementStatus
    evidence_refs: list[EvidenceReference]
    date_fact_ids: list[str]
    rationale: str

    @model_validator(mode="after")
    def validate_current_cv_evidence(self) -> "RequirementAssessment":
        if self.status in ("matched", "partial") and not any(
            ref.source_type == "cv" for ref in self.evidence_refs
        ):
            raise ValueError("matched/partial requirements require current-CV evidence")
        return self


class InferredRequirement(StrictModel):
    text: str
    basis: str


class SwapCoverageItem(StrictModel):
    requirement_id: str
    proposed_status: Literal["partial", "matched"]
    evidence_refs: list[EvidenceReference] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_portfolio_evidence(self) -> "SwapCoverageItem":
        if any(reference.source_type == "cv" for reference in self.evidence_refs):
            raise ValueError("swap coverage requires portfolio evidence only")
        return self


class ProjectDecision(StrictModel):
    slot_index: int
    action: ProjectAction
    current_project_name: str
    swap_in_project_id: str | None
    swap_in_project_name: str | None
    target_requirement_ids: list[str]
    evidence_refs: list[EvidenceReference]
    swap_coverage: list[SwapCoverageItem]
    rationale: str
    impact: SwapImpact | None

    @model_validator(mode="after")
    def validate_action_shape(self) -> "ProjectDecision":
        if self.action == "keep":
            if (
                self.swap_in_project_id is not None
                or self.swap_in_project_name is not None
                or self.impact is not None
                or self.target_requirement_ids
                or self.swap_coverage
                or any(
                    reference.source_type != "cv"
                    for reference in self.evidence_refs
                )
            ):
                raise ValueError("keep decisions cannot contain replacement fields")
            return self
        if not self.swap_in_project_id or not self.swap_in_project_name or not self.impact:
            raise ValueError("swap decisions require replacement identity and impact")
        if not self.target_requirement_ids:
            raise ValueError("swap decisions require target requirements")
        if not self.swap_coverage:
            raise ValueError("swap decisions require target coverage items")
        if {item.requirement_id for item in self.swap_coverage} != set(
            self.target_requirement_ids
        ):
            raise ValueError("swap coverage must match target requirement IDs")
        return self


class EnrichJobResult(StrictModel):
    analysis_status: AnalysisStatus
    explicit_requirements: list[RequirementAssessment]
    inferred_requirements: list[InferredRequirement]
    confidence: Confidence
    current_cv_score: int | None = Field(ge=0, le=100)
    suggested_cv_score: int | None = Field(ge=0, le=100)
    current_score_rationale: str
    suggested_score_rationale: str
    project_decisions: list[ProjectDecision]
    limitations: list[str]
    summary: str

    @model_validator(mode="after")
    def validate_analysis_shape(self) -> "EnrichJobResult":
        if self.analysis_status == "completed":
            if self.current_cv_score is None or self.suggested_cv_score is None:
                raise ValueError("completed analysis requires both scores")
            if not self.explicit_requirements:
                raise ValueError("completed analysis requires an explicit requirement")
            if self.suggested_cv_score < self.current_cv_score:
                raise ValueError("suggested score cannot be lower than current score")
            if all(item.action == "keep" for item in self.project_decisions) and (
                self.suggested_cv_score != self.current_cv_score
            ):
                raise ValueError("all-keep decisions require equal scores")
        else:
            if self.current_cv_score is not None or self.suggested_cv_score is not None:
                raise ValueError("insufficient analysis requires null scores")
            if self.confidence != "low":
                raise ValueError("insufficient analysis requires low confidence")
            if any(decision.action != "keep" for decision in self.project_decisions):
                raise ValueError("insufficient analysis requires all keep decisions")
        return self


class ClassifiedEnrichJobResult(EnrichJobResult):
    passes_threshold: bool | None
    fit_tier: Literal[
        "strong", "moderate", "weak", "not_recommended", "insufficient"
    ]
    fit_message: str
    corrections: list[dict] = Field(default_factory=list)

