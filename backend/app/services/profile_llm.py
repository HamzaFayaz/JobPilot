"""Profile LLM: skill extraction and repo summarization."""

import json
import re

from openai import OpenAI

from backend.app.config import settings


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
                    "skill strings, e.g. [\"Python\", \"React\"]. No markdown."
                ),
            },
            {"role": "user", "content": cv_text[:12000]},
        ],
    )
    reply = completion.choices[0].message.content or "[]"
    return _parse_json_array(reply)


def summarize_repo(readme: str, cv_summary: str) -> dict:
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
                    "Summarize a GitHub repo for a job profile. Return ONLY JSON: "
                    '{"name": "...", "description": "...", "repo_skills": ["..."]}'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"CV summary:\n{cv_summary[:1500]}\n\n"
                    f"README (truncated):\n{readme[:4000]}"
                ),
            },
        ],
    )
    reply = completion.choices[0].message.content or "{}"
    data = _parse_json_object(reply)
    return {
        "name": str(data.get("name", "Project")),
        "description": str(data.get("description", "")),
        "repo_skills": [str(s) for s in data.get("repo_skills", [])],
    }
