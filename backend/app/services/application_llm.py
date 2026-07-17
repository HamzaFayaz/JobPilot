"""Qwen JSON-mode client for one grounded application analysis."""

from __future__ import annotations

import json
import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from backend.app.config import settings
from backend.app.models.application import EnrichJobResult
from backend.app.observability import span
from backend.app.services.application_prompt import ENRICH_JOB_SYSTEM_PROMPT_V1
from backend.app.services.retrieve_project_evidence import retrieve_project_evidence


@dataclass
class ApplicationAnalysisError(Exception):
    code: str
    message: str
    retryable: bool = False
    raw_response: str | None = None
    validation_details: str | None = None

    def safe_dict(self) -> dict[str, Any]:
        return {
            "stage": "enrich_job",
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }


def _compact_schema() -> str:
    return json.dumps(
        EnrichJobResult.model_json_schema(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def build_messages(bundle: dict[str, Any]) -> tuple[list[dict[str, str]], str]:
    """Build deterministic messages without sending retrieval diagnostics."""
    model_bundle = {key: value for key, value in bundle.items() if key != "retrieval_debug"}
    user_message = json.dumps(
        model_bundle, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    system_message = (
        f"{ENRICH_JOB_SYSTEM_PROMPT_V1}\n\n"
        "TRUSTED RESPONSE JSON SCHEMA:\n"
        f"{_compact_schema()}"
    )
    return (
        [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
        user_message,
    )


def _validation_context(bundle: dict[str, Any]) -> dict[str, Any]:
    sources: dict[str, dict[str, Any]] = {}
    for key, source_type in (
        ("layer1_portfolio_overviews", "portfolio_overview"),
        ("layer2a_evidence_cards", "evidence_card"),
        ("layer2b_readme_chunks", None),
    ):
        for item in bundle.get(key) or []:
            source_id = item.get("source_id")
            if not source_id:
                continue
            resolved_type = source_type or item.get("source") or "readme_chunk"
            if resolved_type == "portfolio_overview":
                content = item.get("portfolio_overview") or ""
            elif resolved_type == "evidence_card":
                content = json.dumps(
                    item.get("evidence_card") or {},
                    ensure_ascii=False,
                    sort_keys=True,
                )
            else:
                content = item.get("content") or ""
            sources[source_id] = {
                "source_type": resolved_type,
                "project_id": item.get("project_id"),
                "project_name": item.get("project_name") or item.get("name"),
                "content": content,
                "content_hash": item.get("content_hash")
                or hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "heading_path": item.get("heading_path"),
                "source_start": item.get("source_start"),
                "source_end": item.get("source_end"),
                "requirement_ids": item.get("requirement_ids") or [],
            }
    cv_text = bundle["profile"].get("cv_text") or ""
    slots = bundle["profile"].get("cv_project_slots") or []
    retrieval_debug = bundle.get("retrieval_debug") or {}
    return {
        "cv_text": cv_text,
        "normalized_cv_text": re.sub(r"\s+", " ", cv_text).strip(),
        "cv_section_spans": [
            {
                "slot_index": slot.get("slot_index"),
                "source_start": slot.get("source_start"),
                "source_end": slot.get("source_end"),
            }
            for slot in slots
        ],
        "job_description": bundle.get("job", {}).get("description_text") or "",
        "cv_project_slots": slots,
        "cv_project_ids": [
            slot.get("matched_portfolio_project_id")
            for slot in slots
            if slot.get("matched_portfolio_project_id")
        ],
        "portfolio_project_ids": [
            item.get("project_id")
            for item in bundle.get("layer1_portfolio_overviews") or []
            if item.get("project_id")
        ],
        "evidence_sources": sources,
        "requirement_queries": retrieval_debug.get("requirement_queries") or [],
        "requirement_coverage": retrieval_debug.get("requirement_coverage") or {},
        "packed_chunk_ids": retrieval_debug.get("packed_chunk_ids") or [],
        "run_date": datetime.now(timezone.utc).date().isoformat(),
    }


def _parse_result(raw: str | None) -> EnrichJobResult:
    if raw is None or not raw.strip():
        raise ApplicationAnalysisError(
            "empty_model_response", "Application model returned empty content."
        )
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ApplicationAnalysisError(
            "invalid_model_json",
            "Application model returned invalid JSON.",
            raw_response=raw,
            validation_details=str(exc),
        ) from exc
    try:
        return EnrichJobResult.model_validate(payload)
    except ValidationError as exc:
        raise ApplicationAnalysisError(
            "invalid_model_response",
            "Application analysis failed schema validation.",
            raw_response=raw,
            validation_details=str(exc),
        ) from exc


def analyze_job(
    user_id: int,
    job: dict[str, Any],
    profile: dict[str, Any],
    *,
    client: Any | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Retrieve evidence and return result, validation context, and eval payload."""
    try:
        with span(
            "hybrid_project_evidence_retrieval",
            user_id=user_id,
            job_title=job.get("title", ""),
        ):
            bundle = retrieve_project_evidence(user_id, job, profile)
    except Exception as exc:
        raise ApplicationAnalysisError(
            "retrieval_failed", "Project evidence retrieval failed.", retryable=True
        ) from exc

    messages, _ = build_messages(bundle)
    llm = client or OpenAI(
        api_key=settings.dashscope_api_key,
        base_url=settings.qwen_base_url,
        timeout=120.0,
    )
    invalid_raw: str | None = None
    validation_details: str | None = None

    with span(
        "application_model",
        user_id=user_id,
        job_title=job.get("title", ""),
        model=settings.application_model,
        prompt_version=settings.application_prompt_version,
    ):
        for attempt in range(settings.application_repair_retries + 1):
            request_messages = list(messages)
            if attempt and invalid_raw is not None:
                request_messages.append({"role": "assistant", "content": invalid_raw})
                request_messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Return the complete corrected JSON object only. "
                            f"Validation errors: {validation_details}"
                        ),
                    }
                )
            try:
                response = llm.chat.completions.create(
                    model=settings.application_model,
                    messages=request_messages,
                    temperature=settings.application_temperature,
                    response_format={"type": "json_object"},
                    extra_body={
                        "enable_thinking": settings.application_enable_thinking
                    },
                )
            except Exception as exc:
                raise ApplicationAnalysisError(
                    "model_unavailable",
                    "Application analysis model is unavailable.",
                    retryable=True,
                ) from exc

            raw = response.choices[0].message.content if response.choices else None
            try:
                result = _parse_result(raw)
                dumped = result.model_dump(mode="json")
                return (
                    dumped,
                    _validation_context(bundle),
                    {
                        "bundle": bundle,
                        "messages": request_messages,
                        "raw_response": raw,
                        "validated_response": dumped,
                    },
                )
            except ApplicationAnalysisError as exc:
                invalid_raw = exc.raw_response if exc.raw_response is not None else raw
                validation_details = exc.validation_details or exc.message
                if attempt >= settings.application_repair_retries:
                    exc.message = (
                        "Application analysis failed schema validation after "
                        f"{settings.application_repair_retries} repair retry."
                    )
                    raise

    raise ApplicationAnalysisError(
        "unexpected_enrich_error", "Application analysis failed unexpectedly."
    )

