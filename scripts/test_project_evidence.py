"""Manual smoke test: generate project evidence from the repo README.md.

Usage:
  python scripts/test_project_evidence.py

Requires DASHSCOPE_API_KEY in .env or environment.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.models.project_evidence import ProjectEvidenceResult
from backend.app.services.profile_llm import EVIDENCE_SYSTEM_PROMPT, build_project_evidence


def main() -> int:
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")

    print("=" * 72)
    print("EVIDENCE SYSTEM PROMPT")
    print("=" * 72)
    print(EVIDENCE_SYSTEM_PROMPT)
    print()

    print("=" * 72)
    print("INPUT")
    print("=" * 72)
    print(f"Repository: JobPilot/JobPilot")
    print(f"README path: {readme_path}")
    print(f"README chars: {len(readme)}")
    print()

    result = build_project_evidence(
        readme=readme,
        repo_full_name="JobPilot/JobPilot",
        cv_summary="Software engineer with Python, FastAPI, and agent systems experience.",
    )

    validated = ProjectEvidenceResult.model_validate(
        {
            "name": result["name"],
            "description": result["description"],
            "repo_skills": result["repo_skills"],
            "portfolio_overview": result["portfolio_overview"],
            "evidence_card": result["evidence_card"],
        }
    )

    print("=" * 72)
    print("VALIDATED MODEL: ProjectEvidenceResult")
    print("=" * 72)
    print(validated.model_dump_json(indent=2))
    print()

    print("=" * 72)
    print("STORED PROJECT FIELDS (server-side)")
    print("=" * 72)
    stored_preview = {
        "name": validated.name,
        "description": validated.description[:200] + ("..." if len(validated.description) > 200 else ""),
        "portfolio_overview": validated.portfolio_overview,
        "evidence_card": validated.evidence_card.model_dump(),
        "repo_skills": validated.repo_skills,
    }
    print(json.dumps(stored_preview, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
