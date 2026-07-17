"""Objective evaluators for the real complete-pipeline corpus."""

from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext

from tests.evals.models import EvaluationCaseInput


@dataclass
class DeterministicContracts(Evaluator):
    """Expose every precomputed objective contract as a named boolean."""

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, bool]:
        case = EvaluationCaseInput.model_validate(ctx.output)
        return case.deterministic_checks

    def get_evaluator_version(self) -> str:
        return "phase_3_v1"


@dataclass
class JudgeContract(Evaluator):
    """Surface semantic verdict, hard failures, and per-criterion scores."""

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, bool | int]:
        output = ctx.output
        results: dict[str, bool | int] = {
            "judge_pass": output["overall_verdict"] == "pass",
            "no_hard_failures": not output["hard_failures"],
            "human_review_not_required": not output["human_review_required"],
        }
        for name, criterion in output["criteria"].items():
            results[f"criterion_{name}"] = int(criterion["score"])
        return results

    def get_evaluator_version(self) -> str:
        return "jobpilot_rubric_v1"
