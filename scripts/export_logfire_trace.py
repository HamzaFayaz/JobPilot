"""Export one Logfire trace to local JSON and CSV files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from logfire.experimental.query_client import LogfireQueryClient


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve_trace_id(target: str) -> tuple[str, str | None]:
    path = Path(target)
    if path.is_file():
        report = json.loads(path.read_text(encoding="utf-8"))
        trace_id = report.get("trace_id") or (
            report.get("reproducibility") or {}
        ).get("trace_id")
        if not trace_id:
            trace_ids = {
                case.get("trace_id")
                for section in ("deterministic", "semantic")
                for case in report.get(section) or []
                if case.get("trace_id")
            }
            if len(trace_ids) == 1:
                trace_id = trace_ids.pop()
        if not trace_id:
            raise RuntimeError("Report does not identify one exact Logfire trace.")
        return str(trace_id), report.get("evaluation_run_id")
    if not re.fullmatch(r"[0-9a-fA-F]{16,64}", target):
        raise RuntimeError("Target must be a report path or hexadecimal trace ID.")
    return target, None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="Trace ID or canonical report path")
    parser.add_argument("--min-timestamp", required=True)
    parser.add_argument("--max-timestamp", required=True)
    parser.add_argument("--output-dir", default="logfire-logs")
    args = parser.parse_args()
    trace_id, run_id = _resolve_trace_id(args.target)

    load_dotenv(".env.local")
    token = os.environ.get("LOGFIRE_READ_TOKEN")
    if not token:
        raise RuntimeError("LOGFIRE_READ_TOKEN is not configured in .env.local")

    start = datetime.fromisoformat(args.min_timestamp)
    end = datetime.fromisoformat(args.max_timestamp)
    client = LogfireQueryClient(token)
    page_size = 1000
    rows: list[dict] = []
    offset = 0
    while True:
        sql = (
            "SELECT * FROM records "
            f"WHERE trace_id = '{trace_id}' "
            "ORDER BY start_timestamp ASC, span_id ASC "
            f"LIMIT {page_size} OFFSET {offset}"
        )
        page = client.query_json_rows(
            sql,
            min_timestamp=start,
            max_timestamp=end,
            limit=page_size,
        ).get("rows") or []
        rows.extend(page)
        if len(page) < page_size:
            break
        offset += page_size

    csv_buffer = io.StringIO()
    if rows:
        fieldnames = sorted({key for row in rows for key in row})
        writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: json.dumps(value, ensure_ascii=False)
                    if isinstance(value, (dict, list))
                    else value
                    for key, value in row.items()
                }
            )
    csv_data = csv_buffer.getvalue()

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stem = f"evaluation-trace-{trace_id}"
    json_path = output / f"{stem}.json"
    csv_path = output / f"{stem}.csv"
    json_path.write_text(
        json.dumps({"rows": rows}, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    csv_path.write_text(csv_data, encoding="utf-8")
    names = [
        str(row.get("span_name") or row.get("message") or "")
        for row in rows
    ]
    span_counts = {
        expected: sum(expected in name for name in names)
        for expected in (
            "complete_pipeline_evaluation",
            "job_requirement_extraction_model",
            "bm25_search",
            "rerank_candidates",
            "pack_retrieval_candidates",
            "application_model",
            "application_contract_validation",
            "package_result",
            "parent_finalization",
        )
    }
    required = {
        "complete_pipeline_evaluation": span_counts["complete_pipeline_evaluation"] >= 1,
        "four_requirement_extractions": span_counts["job_requirement_extraction_model"] >= 4,
        "requirement_retrieval": span_counts["bm25_search"] >= 4,
        "reranking": span_counts["rerank_candidates"] >= 1,
        "packing": span_counts["pack_retrieval_candidates"] >= 4,
        "four_application_models": span_counts["application_model"] >= 4,
        "four_contract_validations": span_counts["application_contract_validation"] >= 4,
        "four_package_persistences": span_counts["package_result"] >= 4,
        "one_parent_finalization": span_counts["parent_finalization"] >= 1,
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "trace_id": trace_id,
                "run_id": run_id,
                "min_timestamp": start.isoformat(),
                "max_timestamp": end.isoformat(),
                "record_count": len(rows),
                "formats": ["json", "csv"],
                "required_spans_present": required,
                "required_spans_complete": all(required.values()),
                "span_counts": span_counts,
                "file_hashes": {
                    json_path.name: _sha256(json_path),
                    csv_path.name: _sha256(csv_path),
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Exported {len(rows)} records to {output.resolve()}")


if __name__ == "__main__":
    main()
