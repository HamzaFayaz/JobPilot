"""Write evidence-card-mini-overview.md from the JSON fixture."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "docs/fixtures/evidence-card-mini-overview.json").read_text(encoding="utf-8"))

lines = [
    "# Evidence Card — Mini Overview (JobPilot README test)",
    "",
    "Frozen snapshot from `scripts/test_project_evidence.py` against root `README.md`.",
    "Characters in input and output are preserved exactly in the JSON companion file.",
    "",
    "**Canonical verbatim record:** [`evidence-card-mini-overview.json`](./evidence-card-mini-overview.json)",
    "",
    "## Model",
    "",
]
for key, value in data["model_config"].items():
    lines.append(f"- **{key}:** {value}")

lines.extend(
    [
        "",
        "## Portfolio mini overview (`portfolio_overview`)",
        "",
        "```text",
        data["output"]["portfolio_overview"],
        "```",
        "",
        "## Input summary",
        "",
        f"- **repository:** `{data['input']['repository']}`",
        f"- **cv_summary:** `{data['input']['cv_summary']}`",
        f"- **readme_path:** `{data['input']['readme_path']}`",
        f"- **readme_char_count:** {data['input']['readme_char_count']}",
        "",
        "## System prompt (complete)",
        "",
        "```text",
        data["input"]["system_prompt"],
        "```",
        "",
        "## User message (complete)",
        "",
        "```text",
        data["input"]["user_message"],
        "```",
        "",
        "## Output (complete JSON)",
        "",
        "```json",
        json.dumps(data["output"], indent=2, ensure_ascii=False),
        "```",
        "",
    ]
)

out = ROOT / "docs/fixtures/evidence-card-mini-overview.md"
out.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {out}")
