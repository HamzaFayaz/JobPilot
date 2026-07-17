"""Non-semantic fit classification for an accepted application result."""

from __future__ import annotations

import copy

from backend.app.config import settings
from backend.app.graph.subgraphs.application.state import ApplicationState


def _fit_fields(score: int | None) -> tuple[bool | None, str, str]:
    if score is None:
        return None, "insufficient", "The listing has insufficient detail for a fit score."
    passes = score >= settings.application_fit_threshold
    if score >= 75:
        tier = "strong"
    elif score >= 60:
        tier = "moderate"
    elif score >= 45:
        tier = "weak"
    else:
        tier = "not_recommended"
    return passes, tier, f"Current visible CV fit is {tier.replace('_', ' ')} ({score}/100)."


def classify_fit(state: ApplicationState) -> dict:
    """Add UI-only fit fields without changing model semantics."""
    if state.get("error") or not state.get("enrich_result"):
        return {"stage_status": "classification_skipped"}

    result = copy.deepcopy(state["enrich_result"])
    passes, tier, message = _fit_fields(result.get("current_cv_score"))
    result.update(
        {
            "passes_threshold": passes,
            "fit_tier": tier,
            "fit_message": message,
            "corrections": [],
        }
    )
    return {"classified_result": result, "stage_status": "classified"}
