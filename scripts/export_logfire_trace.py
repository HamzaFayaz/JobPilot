"""Export one Logfire trace to local JSON and CSV files."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from logfire.experimental.query_client import LogfireQueryClient


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace_id")
    parser.add_argument("--min-timestamp", required=True)
    parser.add_argument("--max-timestamp", required=True)
    parser.add_argument("--output-dir", default="logfire-logs")
    args = parser.parse_args()

    load_dotenv(".env.local")
    token = os.environ.get("LOGFIRE_READ_TOKEN")
    if not token:
        raise RuntimeError("LOGFIRE_READ_TOKEN is not configured in .env.local")

    start = datetime.fromisoformat(args.min_timestamp)
    end = datetime.fromisoformat(args.max_timestamp)
    sql = (
        "SELECT * FROM records "
        f"WHERE trace_id = '{args.trace_id}' "
        "ORDER BY start_timestamp ASC, span_id ASC"
    )
    client = LogfireQueryClient(token)
    result = client.query_json_rows(
        sql,
        min_timestamp=start,
        max_timestamp=end,
        limit=10_000,
    )
    csv_data = client.query_csv(
        sql,
        min_timestamp=start,
        max_timestamp=end,
        limit=10_000,
    )

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stem = f"evaluation-trace-{args.trace_id}"
    (output / f"{stem}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    (output / f"{stem}.csv").write_text(csv_data, encoding="utf-8")
    (output / "manifest.json").write_text(
        json.dumps(
            {
                "trace_id": args.trace_id,
                "min_timestamp": start.isoformat(),
                "max_timestamp": end.isoformat(),
                "record_count": len(result["rows"]),
                "formats": ["json", "csv"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Exported {len(result['rows'])} records to {output.resolve()}")


if __name__ == "__main__":
    main()
