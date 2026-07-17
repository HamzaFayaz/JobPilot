# Complete pipeline test corpus

Real Phase 1–3 evaluation fixtures (`profile/evidence` → retrieval → application analysis) using portfolio READMEs, a CV, and job posts.

**No mock LLM tests** — run the pipeline against this data and review output by hand.

## Layout

```text
complete-pipeline-test/
  projects/     # Portfolio READMEs (8 repos)
  cv/           # Your CV — add here
  jobs/         # Four real job post descriptions
  results/      # Generated, sensitive local reports (gitignored)
```

## Projects (`projects/`)

| File | Source |
| --- | --- |
| `jobpilot.md` | This repo |
| `agentic-rag-sub-agents.md` | [agentic-rag-sub-agents](https://github.com/HamzaFayaz/agentic-rag-sub-agents) |
| `voice-automation.md` | [voice-automation](https://github.com/HamzaFayaz/voice-automation) |
| `whatsapp-mcp-assistant.md` | [whatsapp-mcp-assistant](https://github.com/HamzaFayaz/whatsapp-mcp-assistant) |
| `premcrest-van-sales.md` | [Premcrest-Van-Sales](https://github.com/HamzaFayaz/Premcrest-Van-Sales) |
| `youtube-anime-shorts-automation.md` | [Youtube-Anime-Shorts-Automation](https://github.com/HamzaFayaz/Youtube-Anime-Shorts-Automation) |
| `linnwork-orders-automation.md` | [Linnwork-Orders-Automation](https://github.com/HamzaFayaz/Linnwork-Orders-Automation) (`Docs/README.md`) |
| `project-igi-aimbot-computervision.md` | [project-igi-aimbot-computervision](https://github.com/HamzaFayaz/project-igi-aimbot-computervision) |

Copied from [`tests/rag/pipeline/`](../rag/pipeline/) (4) + downloaded from GitHub (4).

## CV (`cv/`)

Add your CV here (`.docx` or `.txt`). Example:

```text
cv/hamza-cv.docx
cv/hamza-cv.txt
```

## Jobs (`jobs/`)

The corpus contains four real job descriptions. One file represents one case.

```text
jobs/job-01-senior-python.md
jobs/job-02-backend-engineer.md
```

Suggested fields per file: `title`, `company`, `platform`, `description_text`.

## Related

- Phase 2 chunking corpus: [`tests/rag/pipeline/`](../rag/pipeline/)
- `enrich_job` input spec: [`docs/discussion/application-subagent-input-spec.md`](../../docs/discussion/application-subagent-input-spec.md)

## Run the real evaluation

This command makes paid Qwen calls and sends fixture content to Logfire when
Logfire and content capture are enabled:

```bash
PYDANTIC_EVALS_ENABLED=true python -m tests.evals.run_complete_pipeline
```

The runner refuses to execute when `PYDANTIC_EVALS_ENABLED` is false, uses a
temporary database/uploads/FAISS directory, performs Phase 1 once, evaluates all
four jobs, runs deterministic checks before the 17 semantic judge cases, and
writes JSON/Markdown reports under `results/`. The CV and generated reports are
ignored by git because they contain personal or full-payload data.
