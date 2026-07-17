"""Application-package persistence node."""

import hashlib
import json

from backend.app.config import settings
from backend.app.graph.subgraphs.application.state import ApplicationState
from backend.app.observability import span
from backend.app.services.search_store import upsert_job_package
from backend.app.services.application_scoring import SCORING_POLICY_VERSION


def _package_key(job: dict) -> str:
    identity = (
        f"{job.get('platform', '')}|{job.get('url', '')}".lower().strip()
        if job.get("url")
        else "|".join(
            str(job.get(key, "")).lower().strip()
            for key in ("title", "company", "description_text")
        )
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


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
        "schema_version": "job_package_analysis_v2",
        "raw_model_result": eval_payload.get("raw_response"),
        "enrich_result": state.get("enrich_result"),
        "classified_result": classified,
        "scoring_policy_version": SCORING_POLICY_VERSION,
        "corrections": (classified or {}).get("corrections") or [],
        "retrieval": {
            "packed_chunk_ids": retrieval_debug.get("packed_chunk_ids") or [],
            "packed_project_ids": retrieval_debug.get("packed_project_ids") or [],
            "requirement_coverage": retrieval_debug.get("requirement_coverage") or {},
            "fallback_reasons": retrieval_debug.get("fallback_reasons") or [],
        },
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
            package_key=_package_key(job),
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
