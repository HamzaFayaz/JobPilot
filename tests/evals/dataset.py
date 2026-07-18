"""Fixture discovery and Pydantic Evals dataset construction."""

import hashlib
import re
from pathlib import Path

from pydantic_evals import Case, Dataset

from tests.evals.evaluators import DeterministicContracts, JudgeContract
from tests.evals.models import EvaluationCaseInput

CORPUS_ROOT = Path(__file__).resolve().parents[1] / "complete-pipeline-test"


def fixture_manifest(root: Path = CORPUS_ROOT) -> list[dict[str, str | int]]:
    files = sorted(
        [
            *root.joinpath("cv").glob("*.docx"),
            *root.joinpath("cv").glob("*.txt"),
            *root.joinpath("projects").glob("*.md"),
            *root.joinpath("jobs").glob("*.md"),
        ]
    )
    files = [path for path in files if path.name.lower() != "readme.md"]
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        }
        for path in files
    ]


def load_jobs(root: Path = CORPUS_ROOT) -> list[dict]:
    jobs: list[dict] = []
    for path in sorted(root.joinpath("jobs").glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        text = path.read_text(encoding="utf-8")
        heading = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        company = re.search(r"^\*\*Company:\*\*\s*(.+?)\s*$", text, re.MULTILINE)
        platform = re.search(r"^\*\*Platform:\*\*\s*(.+?)\s*$", text, re.MULTILINE)
        jobs.append(
            {
                "case_name": path.stem,
                "title": heading.group(1).strip() if heading else path.stem,
                "company": company.group(1).strip() if company else "Unknown",
                "url": f"fixture://{path.name}",
                "platform": (
                    platform.group(1).strip().lower().replace(" ", "_")
                    if platform
                    else "linkedin"
                ),
                "description_text": text,
            }
        )
    return jobs


def load_projects(root: Path = CORPUS_ROOT) -> list[dict]:
    return [
        {
            "id": path.stem,
            "name": path.stem.replace("-", " ").title(),
            "repo_full_name": f"HamzaFayaz/{path.stem}",
            "readme_md": path.read_text(encoding="utf-8"),
            "source": "github",
        }
        for path in sorted(root.joinpath("projects").glob("*.md"))
    ]


def load_cv_path(root: Path = CORPUS_ROOT) -> Path:
    candidates = sorted(
        [
            *root.joinpath("cv").glob("*.docx"),
            *root.joinpath("cv").glob("*.txt"),
        ]
    )
    if not candidates:
        raise FileNotFoundError("No CV fixture found in complete-pipeline-test/cv")
    return candidates[0]


def deterministic_dataset(cases: list[EvaluationCaseInput]) -> Dataset:
    return Dataset(
        name="jobpilot_phase_1_to_3_deterministic",
        cases=[
            Case(
                name=f"{case.phase}:{case.case_name}",
                inputs=case.model_dump(mode="json"),
            )
            for case in cases
        ],
        evaluators=[DeterministicContracts()],
    )


def semantic_dataset(cases: list[EvaluationCaseInput]) -> Dataset:
    return Dataset(
        name="jobpilot_phase_1_to_3_semantic",
        cases=[
            Case(
                name=f"{case.phase}:{case.case_name}",
                inputs=case.model_dump(mode="json"),
            )
            for case in cases
        ],
        evaluators=[JudgeContract()],
    )
