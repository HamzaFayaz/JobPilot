"""Application-model node."""

from backend.app.graph.subgraphs.application.state import ApplicationState
from backend.app.services.application_llm import ApplicationAnalysisError, analyze_job


def enrich_job(state: ApplicationState) -> dict:
    """Retrieve project evidence and call the structured application model."""
    try:
        result, context, eval_payload = analyze_job(
            state["user_id"], state["job"], state["profile"]
        )
        return {
            "enrich_result": result,
            "validation_context": context,
            "eval_payload": eval_payload,
            "stage_status": "enriched",
        }
    except ApplicationAnalysisError as exc:
        return {
            "error": exc.safe_dict(),
            "eval_payload": {
                "raw_response": exc.raw_response,
                "raw_attempts": exc.raw_attempts or [],
                "bundle": exc.bundle,
                "contract_validation": {
                    "valid": False,
                    "errors": exc.validation_details or exc.message,
                },
            },
            "stage_status": "failed",
        }
    except Exception:
        return {
            "error": {
                "stage": "enrich_job",
                "code": "unexpected_enrich_error",
                "message": "Application analysis failed unexpectedly.",
                "retryable": False,
            },
            "stage_status": "failed",
        }
