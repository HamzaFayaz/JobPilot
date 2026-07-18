"""Pinned Qwen Max semantic judge used only by the explicit eval runner."""

import json
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from backend.app.config import settings
from tests.evals.models import EvaluationCaseInput, JudgeResult

RUBRICS = {
    "phase_1_cv_skills": [
        "unsupported skills",
        "important technical-skill omissions",
        "inappropriate non-technical entries",
        "normalization quality",
    ],
    "phase_1_project_evidence": [
        "factual grounding",
        "major feature and architecture coverage",
        "technical specificity",
        "source-section attribution",
        "unsupported metrics or impact",
        "CV-context contamination",
        "honest limitations",
        "summary quality",
    ],
    "phase_2_retrieval": [
        "relevance to explicit job requirements",
        "requirement coverage",
        "evidence usefulness",
        "project diversity and swap awareness",
        "irrelevant or duplicate noise",
        "traceability",
    ],
    "phase_3_application": [
        "requirement classification",
        "evidence grounding",
        "current-score reasonableness",
        "suggested-score uplift reasonableness",
        "project-swap quality",
        "confidence calibration",
        "hallucination or exaggeration",
        "user-facing summary quality",
    ],
}

JUDGE_SYSTEM_PROMPT = """
You are the independent quality judge for a JobPilot evaluation run. Apply only
the supplied rubric to the supplied source data and output. Do not alter the
main result. Rate every criterion from 0 to 4: 4 excellent, 3 acceptable,
2 warning, 1 poor, 0 invalid. Scores 3-4 pass, 2 warning, and 0-1 fail.
Invented candidate technologies, metrics, outcomes, projects, or evidence
sources are hard failures. Return a reasonable score range rather than claiming
one exact true fit score. Use null for reasonable_current_score_range outside
Phase 3. Return only JSON matching the trusted schema.
""".strip()


def _messages(case: EvaluationCaseInput) -> list[dict[str, str]]:
    schema = json.dumps(
        JudgeResult.model_json_schema(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    payload = {
        "phase": case.phase,
        "case_name": case.case_name,
        "rubric": RUBRICS[case.phase],
        "source_and_output": case.payload,
    }
    return [
        {
            "role": "system",
            "content": f"{JUDGE_SYSTEM_PROMPT}\n\nTRUSTED JSON SCHEMA:\n{schema}",
        },
        {
            "role": "user",
            "content": json.dumps(
                payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ),
        },
    ]


def judge_case(
    case: EvaluationCaseInput, *, client: Any | None = None
) -> JudgeResult:
    """Judge one phase case and retry invalid JSON/schema exactly once."""
    llm = client or OpenAI(
        api_key=settings.dashscope_api_key,
        base_url=settings.qwen_base_url,
        timeout=120.0,
    )
    messages = _messages(case)
    last_error = ""
    invalid_response = ""
    for attempt in range(2):
        request_messages = list(messages)
        if attempt:
            request_messages.extend(
                [
                    {"role": "assistant", "content": invalid_response},
                    {
                        "role": "user",
                        "content": (
                            "Return the complete corrected JSON object only. "
                            f"Validation errors: {last_error}"
                        ),
                    },
                ]
            )
        response = llm.chat.completions.create(
            model=settings.eval_judge_model,
            messages=request_messages,
            temperature=settings.eval_judge_temperature,
            response_format={"type": "json_object"},
            extra_body={"enable_thinking": False},
        )
        invalid_response = (
            response.choices[0].message.content if response.choices else ""
        ) or ""
        try:
            result = JudgeResult.model_validate(json.loads(invalid_response))
            expected = set(RUBRICS[case.phase])
            if set(result.criteria) != expected:
                raise ValueError(
                    "criteria keys must exactly match rubric; "
                    f"expected={sorted(expected)}, actual={sorted(result.criteria)}"
                )
            scores = [criterion.score for criterion in result.criteria.values()]
            expected_verdict = (
                "fail"
                if result.hard_failures or any(score <= 1 for score in scores)
                else "warning"
                if any(score == 2 for score in scores)
                else "pass"
            )
            if result.overall_verdict != expected_verdict:
                raise ValueError(
                    f"overall verdict must be {expected_verdict} for supplied scores"
                )
            if not result.human_review_required:
                raise ValueError("human_review_required must be true")
            return result
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            last_error = str(exc)
    raise ValueError(f"Judge response failed validation after one retry: {last_error}")
