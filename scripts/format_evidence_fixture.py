"""Reformat evidence-card-mini-overview fixtures for readability."""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "docs" / "fixtures" / "evidence-card-mini-overview"
LEGACY_JSON = ROOT / "docs" / "fixtures" / "evidence-card-mini-overview.json"
LEGACY_MD = ROOT / "docs" / "fixtures" / "evidence-card-mini-overview.md"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def main() -> None:
    data = json.loads(LEGACY_JSON.read_text(encoding="utf-8"))
    inp = data["input"]
    out = data["output"]
    card = out["evidence_card"]

    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    _write(FIXTURE_DIR / "input-system-prompt.txt", inp["system_prompt"])
    _write(FIXTURE_DIR / "input-cv-summary.txt", inp["cv_summary"])
    _write(FIXTURE_DIR / "input-user-message.txt", inp["user_message"])
    shutil.copy2(ROOT / "README.md", FIXTURE_DIR / "input-readme.md")

    manifest = {
        "test": data["test"],
        "generated_from": data["generated_from"],
        "model_config": data["model_config"],
        "input_files": {
            "system_prompt": "input-system-prompt.txt",
            "cv_summary": "input-cv-summary.txt",
            "user_message": "input-user-message.txt",
            "readme": "input-readme.md",
            "repository": inp["repository"],
            "readme_char_count": inp["readme_char_count"],
        },
        "output_file": "output.json",
        "full_record_file": "full-record.json",
        "overview_file": "evidence-card-mini-overview.md",
    }
    _write(
        FIXTURE_DIR / "full-record.json",
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
    )
    _write(
        FIXTURE_DIR / "manifest.json",
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
    )
    _write(
        FIXTURE_DIR / "output.json",
        json.dumps(out, indent=2, ensure_ascii=False) + "\n",
    )

    evidence_rows = "\n".join(
        f"| {index} | {item['source_section']} | {item['claim']} |"
        for index, item in enumerate(card["evidence"], start=1)
    )

    md = f"""# Evidence Card — Mini Overview

Frozen Phase 1 test snapshot for **JobPilot** using root `README.md` and `build_project_evidence()`.

| Item | Value |
| --- | --- |
| Repository | `{inp['repository']}` |
| Model | `{data['model_config']['model']}` |
| Temperature | `{data['model_config']['temperature']}` |
| README chars | {inp['readme_char_count']} |
| Evidence claims | {len(card['evidence'])} |

## Portfolio mini overview

```text
{out['portfolio_overview']}
```

## Project summary

**Name:** {out['name']}

**Description:**

```text
{out['description']}
```

**Repo skills:** {', '.join(out['repo_skills'])}

## Evidence card

### Purpose

{card['project_purpose']}

### Tech stack

{_bullet_list(card['tech_stack'])}

### Architecture

{_bullet_list(card['architecture'])}

### Key features

{_bullet_list(card['key_features'])}

### Role relevance

{_bullet_list(card['role_relevance'])}

### Grounded evidence

| # | README section | Claim |
| ---: | --- | --- |
{evidence_rows}

### Supported metrics

{_bullet_list(card['supported_metrics']) if card['supported_metrics'] else '- _(none stated in README)_'}

### Limitations / unknowns

{_bullet_list(card['limitations_or_unknowns'])}

## Input files (verbatim)

| File | Contents |
| --- | --- |
| [`input-system-prompt.txt`](./input-system-prompt.txt) | LLM system prompt |
| [`input-cv-summary.txt`](./input-cv-summary.txt) | CV context passed to the model |
| [`input-user-message.txt`](./input-user-message.txt) | Full user message sent to the model |
| [`input-readme.md`](./input-readme.md) | Exact README used as evidence source |

## Output file (verbatim JSON)

See [`output.json`](./output.json) for the complete structured `build_project_evidence()` result.

## Manifest

See [`manifest.json`](./manifest.json) for file index and model config.
"""
    _write(FIXTURE_DIR / "evidence-card-mini-overview.md", md)

    # Keep top-level pointers for existing links.
    pointer = {
        "fixture_dir": "evidence-card-mini-overview/",
        "manifest": "evidence-card-mini-overview/manifest.json",
        "overview": "evidence-card-mini-overview/evidence-card-mini-overview.md",
        "output": "evidence-card-mini-overview/output.json",
        "note": "Formatted fixture set. Verbatim text lives in the fixture directory files.",
    }
    _write(LEGACY_JSON, json.dumps(pointer, indent=2, ensure_ascii=False) + "\n")
    _write(
        LEGACY_MD,
        "# Evidence Card — Mini Overview\n\n"
        "This fixture has been reformatted into a directory for readability.\n\n"
        "- **Overview:** [evidence-card-mini-overview/evidence-card-mini-overview.md](./evidence-card-mini-overview/evidence-card-mini-overview.md)\n"
        "- **Output JSON:** [evidence-card-mini-overview/output.json](./evidence-card-mini-overview/output.json)\n"
        "- **Full record:** [evidence-card-mini-overview/full-record.json](./evidence-card-mini-overview/full-record.json)\n"
        "- **Manifest:** [evidence-card-mini-overview/manifest.json](./evidence-card-mini-overview/manifest.json)\n",
    )

    print(f"Wrote formatted fixture dir: {FIXTURE_DIR}")


if __name__ == "__main__":
    main()
