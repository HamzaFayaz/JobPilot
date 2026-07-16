"""Profile LLM: skill extraction and project evidence generation."""

import json
import re

from openai import OpenAI
from pydantic import ValidationError

from backend.app.config import settings
from backend.app.models.project_evidence import ProjectEvidenceResult

EVIDENCE_SYSTEM_PROMPT = """You are extracting factual, source-grounded project evidence for a job-search profile.

Use only facts present in the supplied repository README and project metadata.
Do not invent the candidate's role, technologies, achievements, metrics, users,
scale, architecture, or outcomes. If something is unclear or unsupported, put
it in limitations_or_unknowns.

Return ONLY valid JSON with these fields:
- name: short project name
- description: technical project description of at least 80 words, as newline-separated lines
- repo_skills: string[]
- portfolio_overview: 30-50 word overview
- evidence_card: object with project_purpose, tech_stack, architecture,
  key_features, role_relevance, evidence, supported_metrics, and
  limitations_or_unknowns
- evidence items: objects with claim and source_section

Every evidence claim must be specific and traceable to a README heading or
section. Use only technologies and facts supported by the README. Return no
markdown and no text outside the JSON object."""


class ProjectEvidenceError(ValueError):
    """Raised when project evidence JSON is missing or invalid."""


def _client() -> OpenAI:
    return OpenAI(
        api_key=settings.dashscope_api_key,
        base_url=settings.qwen_base_url,
    )


def _parse_json_array(text: str) -> list[str]:
    text = text.strip()
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        text = match.group(0)
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [str(s).strip() for s in data if str(s).strip()]
    except json.JSONDecodeError:
        pass
    return []


def _parse_json_object(text: str) -> dict:
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def _as_string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _normalize_evidence_payload(data: dict) -> dict:
    """Coerce common LLM shape drift before Pydantic validation."""
    card = data.get("evidence_card")
    if isinstance(card, dict):
        for field in (
            "tech_stack",
            "architecture",
            "key_features",
            "role_relevance",
            "supported_metrics",
            "limitations_or_unknowns",
        ):
            if field in card:
                card[field] = _as_string_list(card.get(field))
        evidence = card.get("evidence")
        if isinstance(evidence, list):
            card["evidence"] = [
                item for item in evidence if isinstance(item, dict) and item.get("claim")
            ]
    data["repo_skills"] = _as_string_list(data.get("repo_skills"))
    return data


def _validate_project_evidence(data: dict) -> ProjectEvidenceResult:
    try:
        return ProjectEvidenceResult.model_validate(_normalize_evidence_payload(data))
    except ValidationError as exc:
        raise ProjectEvidenceError(f"Invalid project evidence shape: {exc}") from exc


def extract_skills(cv_text: str) -> list[str]:
    if not settings.dashscope_api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not configured")

    client = _client()
    completion = client.chat.completions.create(
        model=settings.profile_model,
        temperature=settings.profile_temperature,
        max_tokens=settings.profile_max_tokens,
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract technical skills from the CV. Return ONLY a JSON array of "
                    'skill strings, e.g. ["Python", "React"]. No markdown.'
                ),
            },
            {"role": "user", "content": cv_text[:12000]},
        ],
    )
    reply = completion.choices[0].message.content or "[]"
    return _parse_json_array(reply)


def build_project_evidence(readme: str, repo_full_name: str, cv_summary: str) -> dict:
    """One structured Qwen call: description, skills, portfolio overview, evidence card."""
    if not settings.dashscope_api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not configured")

    client = _client()
    completion = client.chat.completions.create(
        model=settings.evidence_model,
        temperature=settings.evidence_temperature,
        max_tokens=settings.evidence_max_tokens,
        messages=[
            {"role": "system", "content": EVIDENCE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Repository: {repo_full_name}\n\n"
                    f"CV summary (context only — do not invent facts from this):\n"
                    f"{cv_summary[:1500]}\n\n"
                    f"README:\n{readme}"
                ),
            },
        ],
    )
    reply = completion.choices[0].message.content or ""
    if not reply.strip():
        raise ProjectEvidenceError("Empty project evidence response")

    try:
        data = _parse_json_object(reply)
    except json.JSONDecodeError as exc:
        raise ProjectEvidenceError(f"Project evidence response was not valid JSON: {exc}") from exc

    result = _validate_project_evidence(data)
    return {
        "name": result.name,
        "description": result.description,
        "repo_skills": list(result.repo_skills),
        "portfolio_overview": result.portfolio_overview,
        "evidence_card": result.evidence_card.model_dump(by_alias=False),
    }
