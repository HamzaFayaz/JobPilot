"""Schemas shared by complete-pipeline evaluators and the Qwen judge."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictEvalModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class EvaluationCaseInput(StrictEvalModel):
    phase: Literal[
        "phase_1_cv_skills",
        "phase_1_project_evidence",
        "phase_2_retrieval",
        "phase_3_application",
    ]
    case_name: str
    payload: dict
    deterministic_checks: dict[str, bool] = Field(default_factory=dict)


class JudgeCriterion(StrictEvalModel):
    score: int = Field(ge=0, le=4)
    verdict: Literal["pass", "warning", "fail"]
    reason: str


class JudgeResult(StrictEvalModel):
    phase: str
    case_name: str
    criteria: dict[str, JudgeCriterion]
    reasonable_current_score_range: list[int] | None = None
    unsupported_claims: list[str]
    hard_failures: list[str]
    overall_verdict: Literal["pass", "warning", "fail"]
    human_review_required: bool

    @model_validator(mode="after")
    def validate_score_range(self) -> "JudgeResult":
        if self.reasonable_current_score_range is not None:
            if len(self.reasonable_current_score_range) != 2:
                raise ValueError("score range must contain exactly two integers")
            low, high = self.reasonable_current_score_range
            if not 0 <= low <= high <= 100:
                raise ValueError("score range must be ordered within 0..100")
        return self
