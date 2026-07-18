"""Deterministic three-run comparison for the complete-pipeline evaluation."""

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


def _job_metrics(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    metrics: dict[str, dict[str, Any]] = {}
    for case in _cases(report, "phase_3_application"):
        payload = case.get("payload") or {}
        result = payload.get("classified_result") or {}
        decisions = result.get("project_decisions") or []
        requirements = result.get("explicit_requirements") or []
        metrics[case["case_name"]] = {
            "requirement_count": len(requirements),
            "requirement_statuses": {
                item.get("requirement_id"): item.get("status") for item in requirements
            },
            "current_score": result.get("current_cv_score"),
            "suggested_score": result.get("suggested_cv_score"),
            "swap_count": sum(item.get("action") == "swap" for item in decisions),
            "cv_span_reference_count": sum(
                bool(reference.get("cv_span_id"))
                for requirement in requirements
                for reference in requirement.get("evidence_refs") or []
            ),
            "contract_validation": payload.get("contract_validation"),
        }
    return metrics


def summarize(report: dict[str, Any], trace: dict[str, Any]) -> dict[str, Any]:
    retrieval_cases = _cases(report, "phase_2_retrieval")
    packed = [
        chunk
        for case in retrieval_cases
        for chunk in (case.get("payload") or {}).get("selected_chunks") or []
    ]
    hashes = [item.get("content_hash") for item in packed if item.get("content_hash")]
    jobs = _job_metrics(report)
    scores = [
        item["current_score"]
        for item in jobs.values()
        if isinstance(item.get("current_score"), int)
    ]
    extraction = [
        (case.get("payload") or {}).get("requirement_extraction") or {}
        for case in retrieval_cases
    ]
    unsupplied = [
        requirement_id
        for case in retrieval_cases
        for requirement_id in (
            ((case.get("payload") or {}).get("retrieval_debug") or {}).get(
                "unsupplied_requirement_ids"
            )
            or []
        )
    ]
    return {
        "git_commit": report.get("git_commit"),
        "deterministic_contract_pass_rate": _assertion_rate(report),
        "packed_chunk_count": len(packed),
        "packed_project_count": len(
            {item.get("project_id") for item in packed if item.get("project_id")}
        ),
        "duplicate_packed_content_count": len(hashes) - len(set(hashes)),
        "unsupplied_requirement_count": len(unsupplied),
        "requirement_extraction": {
            "job_count": len(extraction),
            "llm_count": sum(not item.get("fallback_used") for item in extraction),
            "fallback_count": sum(bool(item.get("fallback_used")) for item in extraction),
            "repair_count": sum(int(item.get("repair_count") or 0) for item in extraction),
        },
        "full_job_fallback_count": sum(
            bool(
                ((case.get("payload") or {}).get("retrieval_debug") or {}).get(
                    "full_job_fallback_executed"
                )
            )
            for case in retrieval_cases
        ),
        "jobs": jobs,
        "mean_current_score": round(sum(scores) / len(scores), 2) if scores else None,
        "trace": {
            "trace_id": trace.get("trace_id"),
            "record_count": trace.get("record_count"),
            "required_spans_present": trace.get("required_spans_present"),
            "required_spans_complete": trace.get("required_spans_complete")
            if "required_spans_complete" in trace
            else all((trace.get("required_spans_present") or {}).values()),
        },
    }


def compare(
    run1_report: dict[str, Any],
    run2_report: dict[str, Any],
    run3_report: dict[str, Any],
    run1_trace: dict[str, Any],
    run2_trace: dict[str, Any],
    run3_trace: dict[str, Any],
) -> dict[str, Any]:
    runs = {
        "run_1_broad_retrieval": summarize(run1_report, run1_trace),
        "run_2_deterministic_scoring": summarize(run2_report, run2_trace),
        "run_3_llm_authority": summarize(run3_report, run3_trace),
    }
    current = runs["run_3_llm_authority"]
    hard_contracts = current["deterministic_contract_pass_rate"] == 100
    trace_complete = bool(current["trace"].get("required_spans_complete"))
    return {
        "runs": runs,
        "interpretation": (
            "Scores are descriptive model outputs and are not accuracy targets. "
            "Run 3 acceptance depends on source-grounded human review."
        ),
        "acceptance": {
            "hard_contracts_pass": hard_contracts,
            "duplicates_zero": current["duplicate_packed_content_count"] == 0,
            "trace_complete": trace_complete,
            "human_review_required": True,
            "all_four_jobs_human_accepted": None,
            "decision": "requires_human_review",
        },
    }


def _markdown(comparison: dict[str, Any]) -> str:
    lines = [
        "# JobPilot Phase 1–3 three-run accuracy comparison",
        "",
        comparison["interpretation"],
        "",
    ]
    for label, run in comparison["runs"].items():
        lines.extend(
            [
                f"## {label.replace('_', ' ').title()}",
                f"- Commit: `{run['git_commit']}`",
                f"- Deterministic contract pass rate: {run['deterministic_contract_pass_rate']}%.",
                f"- Packed chunks/projects: {run['packed_chunk_count']}/{run['packed_project_count']}.",
                f"- Duplicate packed content: {run['duplicate_packed_content_count']}.",
                f"- Mean current score (not an accuracy target): {run['mean_current_score']}.",
                f"- Requirement extraction LLM/fallback: "
                f"{run['requirement_extraction']['llm_count']}/"
                f"{run['requirement_extraction']['fallback_count']}.",
                "",
            ]
        )
    lines.extend(
        [
            "## Acceptance",
            "- Human review of every Run 3 job remains authoritative.",
            f"- Current decision: `{comparison['acceptance']['decision']}`.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run1_report", type=Path)
    parser.add_argument("run2_report", type=Path)
    parser.add_argument("run3_report", type=Path)
    parser.add_argument("run1_trace_manifest", type=Path)
    parser.add_argument("run2_trace_manifest", type=Path)
    parser.add_argument("run3_trace_manifest", type=Path)
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("phase1-3-system-accuracy-three-run-comparison.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("phase1-3-system-accuracy-three-run-comparison.md"),
    )
    args = parser.parse_args()
    result = compare(
        _load(args.run1_report),
        _load(args.run2_report),
        _load(args.run3_report),
        _load(args.run1_trace_manifest),
        _load(args.run2_trace_manifest),
        _load(args.run3_trace_manifest),
    )
    args.json_output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    args.markdown_output.write_text(_markdown(result), encoding="utf-8")
    print(f"Wrote {args.json_output} and {args.markdown_output}")


if __name__ == "__main__":
    main()
