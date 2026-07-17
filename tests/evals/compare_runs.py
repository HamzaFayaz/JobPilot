"""Deterministic comparison of two complete-pipeline evaluation runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _cases(report: dict[str, Any], phase: str) -> list[dict[str, Any]]:
    return [
        case
        for case in report.get("canonical_cases") or []
        if case.get("phase") == phase
    ]


def _assertion_rate(report: dict[str, Any]) -> float:
    values = [
        bool(value.get("value"))
        for case in report.get("deterministic") or []
        for value in (case.get("assertions") or {}).values()
    ]
    return round(100 * sum(values) / len(values), 2) if values else 0.0


def _semantic_scores(report: dict[str, Any]) -> dict[str, float]:
    grouped: dict[str, list[int]] = {}
    for case in report.get("semantic") or []:
        phase = case.get("name", "").split(":", 1)[0]
        scores = [
            int(item.get("score", 0))
            for item in (case.get("output", {}).get("criteria") or {}).values()
        ]
        if scores:
            grouped.setdefault(phase, []).extend(scores)
    return {
        phase: round(sum(scores) / len(scores), 2)
        for phase, scores in grouped.items()
    }


def _job_metrics(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    metrics: dict[str, dict[str, Any]] = {}
    for case in _cases(report, "phase_3_application"):
        payload = case.get("payload") or {}
        result = payload.get("classified_result") or {}
        retrieval = payload.get("retrieved_evidence") or {}
        decisions = result.get("project_decisions") or []
        metrics[case["case_name"]] = {
            "requirement_count": len(result.get("explicit_requirements") or []),
            "current_score": result.get("current_cv_score"),
            "suggested_score": result.get("suggested_cv_score"),
            "valid_swaps": sum(item.get("action") == "swap" for item in decisions),
            "correction_codes": sorted(
                item.get("code") for item in result.get("corrections") or []
            ),
            "packed_chunk_ids": sorted(
                item.get("source_id") for item in retrieval.get("chunks") or []
            ),
        }
    return metrics


def summarize(report: dict[str, Any], trace: dict[str, Any]) -> dict[str, Any]:
    retrieval_cases = _cases(report, "phase_2_retrieval")
    packed = [
        chunk
        for case in retrieval_cases
        for chunk in (case.get("payload") or {}).get("selected_chunks") or []
    ]
    fingerprints = [chunk.get("content_hash") for chunk in packed if chunk.get("content_hash")]
    uncovered = [
        requirement_id
        for case in retrieval_cases
        for requirement_id in (
            (case.get("payload") or {}).get("retrieval_debug") or {}
        ).get("uncovered_requirement_ids")
        or []
    ]
    jobs = _job_metrics(report)
    scores = [
        item["current_score"]
        for item in jobs.values()
        if isinstance(item.get("current_score"), int)
    ]
    return {
        "git_commit": report.get("git_commit"),
        "deterministic_contract_pass_rate": _assertion_rate(report),
        "semantic_mean_scores": _semantic_scores(report),
        "cv_slot_counts": {
            case["case_name"]: len(
                ((case.get("payload") or {}).get("profile") or {}).get("cv_project_slots")
                or (case.get("payload") or {}).get("classified_result", {}).get("project_decisions")
                or []
            )
            for case in _cases(report, "phase_3_application")
        },
        "packed_chunk_count": len(packed),
        "duplicate_packed_content_count": len(fingerprints) - len(set(fingerprints)),
        "uncovered_requirement_count": len(uncovered),
        "jobs": jobs,
        "mean_current_score": round(sum(scores) / len(scores), 2) if scores else None,
        "trace": {
            "trace_id": trace.get("trace_id"),
            "record_count": trace.get("record_count"),
            "required_spans_present": trace.get("required_spans_present"),
        },
    }


def compare(
    baseline_report: dict[str, Any],
    new_report: dict[str, Any],
    baseline_trace: dict[str, Any],
    new_trace: dict[str, Any],
) -> dict[str, Any]:
    baseline = summarize(baseline_report, baseline_trace)
    current = summarize(new_report, new_trace)
    job_scores = [
        item["current_score"]
        for item in current["jobs"].values()
        if isinstance(item.get("current_score"), int)
    ]
    improvement_targets_pass = (
        current["mean_current_score"] is not None
        and current["mean_current_score"] >= 75
        and bool(job_scores)
        and min(job_scores) >= 60
    )
    return {
        "baseline": baseline,
        "new": current,
        "deltas": {
            "deterministic_contract_pass_rate": round(
                current["deterministic_contract_pass_rate"]
                - baseline["deterministic_contract_pass_rate"],
                2,
            ),
            "packed_chunk_count": current["packed_chunk_count"]
            - baseline["packed_chunk_count"],
            "duplicate_packed_content_count": current["duplicate_packed_content_count"]
            - baseline["duplicate_packed_content_count"],
            "uncovered_requirement_count": current["uncovered_requirement_count"]
            - baseline["uncovered_requirement_count"],
        },
        "acceptance": {
            "hard_contracts_pass": current["deterministic_contract_pass_rate"] == 100,
            "duplicates_zero": current["duplicate_packed_content_count"] == 0,
            "improvement_targets_pass": improvement_targets_pass,
            "human_review_required": True,
            "decision": (
                "requires_human_review"
                if improvement_targets_pass
                else "rejected"
            ),
        },
    }


def _markdown(comparison: dict[str, Any]) -> str:
    baseline = comparison["baseline"]
    current = comparison["new"]
    deltas = comparison["deltas"]
    lines = [
        "# JobPilot Phase 1–3 accuracy comparison",
        "",
        "## Deterministic evidence",
        f"- Contract pass rate: {baseline['deterministic_contract_pass_rate']}% → "
        f"{current['deterministic_contract_pass_rate']}% "
        f"({deltas['deterministic_contract_pass_rate']:+.2f} points).",
        f"- Packed chunks: {baseline['packed_chunk_count']} → "
        f"{current['packed_chunk_count']}. Changes reflect requirement-aware packing.",
        f"- Duplicate packed content: {baseline['duplicate_packed_content_count']} → "
        f"{current['duplicate_packed_content_count']}.",
        f"- Uncovered requirements: {baseline['uncovered_requirement_count']} → "
        f"{current['uncovered_requirement_count']}.",
        f"- Mean current-fit score: {baseline['mean_current_score']} → "
        f"{current['mean_current_score']} (target: at least 75).",
        "",
        "## Per-job scoring",
    ]
    for name, result in current["jobs"].items():
        previous = baseline["jobs"].get(name) or {}
        lines.append(
            f"- {name}: current {previous.get('current_score')} → "
            f"{result.get('current_score')}; suggested "
            f"{previous.get('suggested_score')} → {result.get('suggested_score')}; "
            f"validated swaps {result.get('valid_swaps')}."
        )
    lines.extend(
        [
            "",
            "## Acceptance",
            "- Deterministic hard contracts: "
            + ("pass." if comparison["acceptance"]["hard_contracts_pass"] else "fail."),
            "- Human review of all four source-grounded job results remains required.",
            f"- Decision: `{comparison['acceptance']['decision']}`.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline_report", type=Path)
    parser.add_argument("new_report", type=Path)
    parser.add_argument("baseline_trace_manifest", type=Path)
    parser.add_argument("new_trace_manifest", type=Path)
    parser.add_argument("--json-output", type=Path, default=Path("phase1-3-system-accuracy-comparison.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("phase1-3-system-accuracy-comparison.md"))
    args = parser.parse_args()
    result = compare(
        _load(args.baseline_report),
        _load(args.new_report),
        _load(args.baseline_trace_manifest),
        _load(args.new_trace_manifest),
    )
    args.json_output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    args.markdown_output.write_text(_markdown(result), encoding="utf-8")
    print(f"Wrote {args.json_output} and {args.markdown_output}")


if __name__ == "__main__":
    main()
