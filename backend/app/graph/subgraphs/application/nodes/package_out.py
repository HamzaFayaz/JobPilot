"""Application-package persistence node."""

import hashlib
import json

from backend.app.config import settings
from backend.app.graph.subgraphs.application.state import ApplicationState
from backend.app.observability import span
from backend.app.services.search_store import package_key_for_job, upsert_job_package


def _profile_hash(profile: dict) -> str:
    serialized = json.dumps(
        profile, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return f"sha256:{hashlib.sha256(serialized.encode('utf-8')).hexdigest()}"


def package_out(state: ApplicationState) -> dict:
    """Persist one ready or failed package and expose compact parent state."""
    job = state["job"]
    profile_hash = _profile_hash(state["profile"])
    classified = state.get("classified_result")
    error = state.get("error")
    eval_payload = state.get("eval_payload") or {}
    retrieval_debug = (eval_payload.get("bundle") or {}).get("retrieval_debug") or {}
    envelope = {
        "schema_version": "job_package_analysis_v3",
        "raw_model_result": eval_payload.get("raw_response"),
        "raw_model_attempts": eval_payload.get("raw_attempts") or [],
        "parsed_model_result": eval_payload.get("parsed_model_result"),
        "accepted_model_result": state.get("enrich_result"),
        "enrich_result": state.get("enrich_result"),
        "accepted_user_facing_result": classified,
        "classified_result": classified,
        "contract_validation": eval_payload.get("contract_validation"),
        "heuristic_score_not_user_facing": eval_payload.get(
            "heuristic_score_not_user_facing"
        ),
        "retrieval": {
            "packed_chunk_ids": retrieval_debug.get("packed_chunk_ids") or [],
            "packed_project_ids": retrieval_debug.get("packed_project_ids") or [],
            "retrieval_supply": retrieval_debug.get("retrieval_supply") or {},
            "fallback_reasons": retrieval_debug.get("fallback_reasons") or [],
        },
        "requirement_extraction": (
            (eval_payload.get("bundle") or {}).get("requirement_extraction")
        ),
        "retrieval_bundle": eval_payload.get("bundle"),
        "error": error,
        "metadata": {
            "model_name": settings.application_model,
            "prompt_version": settings.application_prompt_version,
            "result_schema_version": settings.application_schema_version,
            "profile_snapshot_hash": profile_hash,
        },
    }
    status = "ready" if classified is not None and error is None else "failed"
    with span(
        "package_result",
        user_id=state["user_id"],
        search_run_id=state["run_id"],
        job_title=job.get("title", ""),
    ):
        package_id = upsert_job_package(
            run_id=state["run_id"],
            user_id=state["user_id"],
            job=job,
            package_key=package_key_for_job(job),
            analysis=envelope,
            status=status,
            summary=(classified or {}).get("summary", ""),
            current_cv_score=(classified or {}).get("current_cv_score"),
            suggested_cv_score=(classified or {}).get("suggested_cv_score"),
            error=error,
            model_name=settings.application_model,
            prompt_version=settings.application_prompt_version,
            profile_snapshot_hash=profile_hash,
        )
    return {
        "package_id": package_id,
        "stage_status": "packaged",
        "packages": [
            {
                "package_id": package_id,
                "job_url": job.get("url", ""),
                "status": status,
                "error": error,
            }
        ],
    }
