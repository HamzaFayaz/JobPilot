"""Build private, source-resolved human-review labels for the real corpus."""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.services.cv_evidence_spans import build_cv_evidence_spans
from backend.app.services.cv_parser import extract_text_from_docx
from backend.app.services.cv_project_slots import parse_cv_project_slots
from tests.evals.dataset import CORPUS_ROOT, load_cv_path, load_jobs, load_projects

SPECS = {
    "job1_deerbiation": {
        "quotes": [
            "Riyadh, Saudi Arabia",
            "Python development",
            "Azure AI Foundry and Azure OpenAI",
            "Microsoft Azure cloud services",
            "SQL and Azure data warehousing",
            "AI model and agent integration",
            "React and full-stack AI application development",
            "Building and deploying production-grade AI solutions",
        ],
        "current_score_range": [60, 75],
        "suggested_score_range": [60, 78],
        "allowed_cv_terms": ["Python", "Azure", "agent", "React", "full-stack"],
        "portfolio_candidates": ["jobpilot"],
        "no_portfolio_evidence": ["Azure AI Foundry", "Azure OpenAI", "data warehousing"],
        "prohibited_claims": [
            "General Azure proves Azure AI Foundry or Azure OpenAI",
            "Portfolio-only evidence changes current fit",
        ],
    },
    "job2_deerbiation": {
        "quotes": [
            "Remote",
            "1+ year",
            "1+ year of experience in web development",
            "Hands-on experience with AI tools such as ChatGPT, Claude, Cursor, GitHub Copilot, Lovable, Bolt, or similar",
            "Ability to create and ship websites using AI-assisted workflows",
            "Good understanding of HTML, CSS, JavaScript, and modern web frameworks",
            "Strong problem-solving skills and willingness to learn",
        ],
        "current_score_range": [55, 70],
        "suggested_score_range": [55, 72],
        "allowed_cv_terms": ["JavaScript", "React", "Cursor", "AI"],
        "portfolio_candidates": ["jobpilot"],
        "no_portfolio_evidence": ["1+ year of experience in web development", "HTML, CSS"],
        "prohibited_claims": [
            "React proves HTML, CSS, and Tailwind",
            "AI project use proves one year of web-development employment",
        ],
    },
    "job3_deerbiation": {
        "quotes": [
            "OPF Society, Lahore (Onsite)",
            "1–2 years",
            "BSCS, BSIT, Software Engineering, AI, Data Science, or a relevant degree",
            "Basic understanding of AI/ML concepts",
            "Strong communication and problem-solving skills",
            "Passion for learning and professional growth",
        ],
        "current_score_range": [65, 85],
        "suggested_score_range": [65, 85],
        "allowed_cv_terms": ["AI", "Machine Learning", "Python", "2025", "2026"],
        "portfolio_candidates": [],
        "no_portfolio_evidence": ["Lahore", "Onsite", "degree", "communication"],
        "prohibited_claims": [
            "Project evidence proves onsite location",
            "Overlapping CV date ranges are double counted",
            "Agentic RAG is recommended as a replacement when already on the CV",
        ],
    },
    "job4_deerbiation": {
        "quotes": [
            "Remote",
            "Fresher with good hands-on experience, or mid-level with 1–3 years",
            "Multi-agent systems using LangChain and LangGraph",
            "Generative AI deployment on AWS Bedrock",
            "RAG pipelines with vector databases",
            "Core machine learning in Python",
            "TensorFlow or PyTorch",
            "Natural language processing",
            "Git-based engineering workflows",
        ],
        "current_score_range": [70, 85],
        "suggested_score_range": [70, 88],
        "allowed_cv_terms": [
            "LangGraph",
            "RAG",
            "PyTorch",
            "Python",
            "Git",
            "AWS",
            "Bedrock",
            "pgvector",
        ],
        "portfolio_candidates": ["jobpilot", "agentic-rag-sub-agents"],
        "no_portfolio_evidence": [],
        "prohibited_claims": [
            "A generic vector database proves pgvector",
            "AWS proves Bedrock",
            "Related orchestration products are treated as identical",
        ],
    },
}


def _cv_text() -> str:
    path = load_cv_path()
    return (
        extract_text_from_docx(path)
        if path.suffix.casefold() == ".docx"
        else path.read_text(encoding="utf-8")
    )


def build_labels() -> dict:
    cv_text = _cv_text()
    projects = load_projects()
    slots = parse_cv_project_slots(cv_text, projects)
    spans = build_cv_evidence_spans(cv_text, slots)
    labels: dict[str, dict] = {}
    for job in load_jobs():
        spec = SPECS[job["case_name"]]
        description = job["description_text"]
        requirements = []
        for index, quote in enumerate(spec["quotes"], start=1):
            start = description.index(quote)
            requirements.append(
                {
                    "requirement_id": f"gold_req_{index:02d}",
                    "job_quote": quote,
                    "source_start": start,
                    "source_end": start + len(quote),
                    "importance": "required",
                    "acceptable_statuses": ["matched", "partial", "not_evidenced"],
                }
            )
        allowed_terms = [term.casefold() for term in spec["allowed_cv_terms"]]
        valid_spans = [
            span
            for span in spans
            if any(term in span["content"].casefold() for term in allowed_terms)
        ]
        labels[job["case_name"]] = {
            "requirements": requirements,
            "valid_cv_spans": valid_spans,
            "portfolio_evidence_candidates": spec["portfolio_candidates"],
            "requirements_without_portfolio_evidence": spec["no_portfolio_evidence"],
            "valid_swaps": [],
            "invalid_swaps": ["replacement already on CV", "swap without gap-closing evidence"],
            "current_score_range": spec["current_score_range"],
            "suggested_score_range": spec["suggested_score_range"],
            "prohibited_claims": spec["prohibited_claims"],
            "human_review": {"accepted": None, "notes": ""},
        }
    return {
        "schema_version": "jobpilot_human_labels_v1",
        "private_local_artifact": True,
        "jobs": labels,
    }


def main() -> None:
    output = CORPUS_ROOT / "labels" / "human-review-labels.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(build_labels(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
