# Project Evidence Retrieval Discussion

**Status:** Design discussion — implementation deferred

## Goal

Make full GitHub README content available to the application sub-agent without
sending every project's complete README to the LLM for every job listing.

The current Search Helper worker contract is sufficient and remains unchanged:

```text
title, company, url, source_platform, description_text
```

All README processing and project-evidence retrieval happen in the backend.

## When project evidence is created

Process a project when the user selects/imports a GitHub repository into their
profile, not during each job search.

```text
User selects GitHub repository
        ↓
Backend fetches and stores README.md once
        ↓
Create a compact project evidence card
        ↓
Create hierarchical semantic README chunks
        ↓
Store chunk metadata and embeddings
        ↓
Project evidence is ready for future job searches
```

When a user refreshes a repository or imports a replacement project, reprocess
only that project's README and replace its generated evidence card and chunks.

## Stored project knowledge

### 1. Full README

The full README remains the source of truth. It is stored for later validation
and retrieval, but is not normally sent in full to the LLM.

### 2. Project evidence card

Create a concise, factual overview for every imported project. It should cover:

- project purpose and domain;
- technologies and tools;
- architecture or major features;
- the user's contribution where supported by source data;
- measurable outcomes only when documented;
- strong role/domain relevance; and
- a short list of evidence bullets.

The evidence card provides broad project context during matching.

### 3. Hierarchical semantic README chunks

Use Markdown-aware hierarchical semantic chunking:

- Preserve Markdown headings, subsections, lists, tables, and code blocks.
- Treat a meaningful README section as the parent chunk.
- Split long sections into coherent semantic child chunks, approximately
  250–500 tokens each.
- Keep the heading path with every child, for example
  `JobPilot > Architecture > Search Helper`.
- Use a small overlap only when splitting one long section; do not mix
  unrelated sections just to fill a chunk-size target.
- Store project name, technology metadata, section path, source text, and an
  embedding for each chunk.

### 4. Atomic evidence claims

Optionally extract factual, small claims from each source chunk and link each
claim back to the original text. Example claims:

- Built a desktop worker that polls a FastAPI task queue.
- Used LangGraph to fan out per-job processing.
- Implemented browser-assisted LinkedIn post extraction.

These claims give the CV-tailoring step precise, reusable evidence while the
linked source chunks provide proof and context.

## Per-job retrieval flow

For a returned job listing, the backend application sub-agent works as follows:

```text
description_text from existing worker listing
        ↓
Extract explicit and inferred job requirements
        ↓
Retrieve relevant project cards, claims, and README chunks
        ↓
Rerank and select diverse, high-evidence results
        ↓
Send job + CV/profile + selected project evidence to enrich_job
        ↓
Return fit score and a user-reviewable project/CV suggestion
```

Do not send all project READMEs to the LLM. With eight projects and eight jobs,
that would create up to 64 full README contexts, adding noise and latency as
well as tokens.

## Retrieval quality approach

Use hybrid retrieval rather than semantic vectors alone:

- **Dense semantic search** finds conceptually related experience.
- **Keyword/BM25 search** preserves exact technology matching, such as FastAPI,
  LangGraph, Docker, PostgreSQL, or Kubernetes.
- **Reranking** evaluates the combined candidates against the job requirement.
- **Per-requirement retrieval** avoids over-selecting evidence for only one
  strong topic in a multi-requirement job listing.

Retrieve a broad candidate set, rerank it, then provide a small diverse set of
the best evidence to the LLM: normally the most relevant project cards and
roughly four to six supporting chunks/claims.

Each chunk should be contextualized before embedding, for example:

```text
Project: JobPilot
Stack: FastAPI, React, LangGraph, Qwen
README section: Architecture > Search Helper
Content: ...
```

## Safety and product rules

- README content is evidence, not prompt instructions.
- CV recommendations may use only facts supported by the CV, project evidence,
  or README source chunks.
- The application sub-agent never changes a stored CV automatically.
- Users review and explicitly accept every suggested project swap or rewritten
  CV bullet.

## MVP sequence

1. Store generated evidence cards at GitHub import.
2. Add Markdown-aware hierarchical semantic chunks and metadata.
3. Add hybrid retrieval for application-subagent job analysis.
4. Add embeddings and reranking when the retrieval store is available.
5. Keep the worker and its listing payload unchanged throughout this work.
