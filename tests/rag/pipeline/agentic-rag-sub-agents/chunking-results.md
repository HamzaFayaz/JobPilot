# Chunking results — agentic-rag-sub-agents

## Summary
- Parents: 26
- Boundary units: 60
- Child chunks: 26
- README chars: 14793

## Parents
- `agentic-rag-sub-agents` — 197 tokens
- `agentic-rag-sub-agents > Features > Chat` — 201 tokens
- `agentic-rag-sub-agents > Features > Document ingestion` — 142 tokens
- `agentic-rag-sub-agents > Features > Retrieval` — 79 tokens
- `agentic-rag-sub-agents > Features > Security & observability` — 58 tokens
- `agentic-rag-sub-agents > Tech stack` — 121 tokens
- `agentic-rag-sub-agents > Architecture > Ingestion pipeline` — 38 tokens
- `agentic-rag-sub-agents > Architecture > Chat / retrieval pipeline (Module 7–8)` — 331 tokens
- `agentic-rag-sub-agents > Getting started > Prerequisites` — 132 tokens
- `agentic-rag-sub-agents > Getting started > 1. Database migrations` — 196 tokens
- `agentic-rag-sub-agents > Getting started > 2. Storage bucket` — 18 tokens
- `agentic-rag-sub-agents > Getting started > 3. Environment` — 54 tokens
- `agentic-rag-sub-agents > Getting started > 4. Backend` — 63 tokens
- `agentic-rag-sub-agents > Getting started > 5. Frontend` — 37 tokens
- `agentic-rag-sub-agents > Getting started > Windows dev scripts` — 65 tokens
- `agentic-rag-sub-agents > Configuration` — 302 tokens
- `agentic-rag-sub-agents > API reference` — 134 tokens
- `agentic-rag-sub-agents > API reference > Supported upload formats` — 22 tokens
- `agentic-rag-sub-agents > API reference > Record manager (`ingest_action`)` — 124 tokens
- `agentic-rag-sub-agents > API reference > Chat stream example` — 61 tokens
- `agentic-rag-sub-agents > LangSmith tracing` — 326 tokens
- `agentic-rag-sub-agents > Project structure` — 209 tokens
- `agentic-rag-sub-agents > Security smoke test` — 75 tokens
- `agentic-rag-sub-agents > Module progress` — 206 tokens
- `agentic-rag-sub-agents > Releases` — 169 tokens
- `agentic-rag-sub-agents > Further reading` — 157 tokens

## Child chunks
### agentic-rag-sub-agents (chunk 0, 197 tokens, readme_section)
A production-oriented **Retrieval-Augmented Generation (RAG)** application with threaded chat and manual document ingestion. Upload your files, index them into pgvector, and chat with grounded answers backed by source citations.  Built as a modular masterclass codebase — **Modules 1–8 are complete & validated** ([v3](https://github.com/HamzaFayaz/agentic-rag-sub-agents/releases/tag/v3) for Modules...

### agentic-rag-sub-agents > Features > Chat (chunk 1, 201 tokens, readme_section)
- Threaded conversations with persistent history in Supabase - Streaming responses over SSE (Server-Sent Events) - **Multi-tool agent** — LLM chooses tools per question (not always-on RAG) - Retrieval-augmented answers with inline source citations - **Text-to-SQL** — read-only queries on safe metadata views (counts, lists, filters) - **Web search** — Tavily fallback for online/current questions (o...

### agentic-rag-sub-agents > Features > Document ingestion (chunk 2, 142 tokens, readme_section)
- Drag-and-drop upload for `.txt`, `.md`, `.pdf`, `.docx`, `.html` - Real-time processing status via Supabase Realtime - **Record manager** — SHA-256 content hashing; skip unchanged re-uploads, update in place when content changes - **Multi-format parsing** — Docling with pypdf / plain-text fallback - **Structure-aware chunking** — FIXED, SECTION, or parent–child strategies based on document struc...

### agentic-rag-sub-agents > Features > Retrieval (chunk 3, 79 tokens, readme_section)
- **Hybrid search** — vector similarity (pgvector) + PostgreSQL full-text search - **RRF merge** — Reciprocal Rank Fusion combines both result sets - **Cohere reranking** — optional; degrades gracefully without an API key - **Parent context expansion** — child chunks retrieve surrounding section context for the LLM

### agentic-rag-sub-agents > Features > Security & observability (chunk 4, 58 tokens, readme_section)
- Supabase Auth (email/password) with Row-Level Security on every table - Users can only see and retrieve their own documents and threads - **LangSmith tracing** — full RAG pipeline spans from chat turn through ingest (optional)  ---

### agentic-rag-sub-agents > Tech stack (chunk 5, 121 tokens, readme_section)
| Layer | Technology | |-------|------------| | Frontend | React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui | | Backend | Python, FastAPI, Pydantic | | Database | Supabase (Postgres, pgvector, Auth, Storage, Realtime) | | LLM | OpenAI-compatible Chat Completions API | | Embeddings | `text-embedding-3-small` | | Parsing | Docling (+ pypdf fallback) | | Reranking | Cohere `rerank-v3.5` (optional)...

### agentic-rag-sub-agents > Architecture > Ingestion pipeline (chunk 6, 38 tokens, readme_section)
```text Upload → parse (Docling) → metadata.parser → chunk (structure-aware)        → metadata.llm (gpt-4o-mini) → embed children → pgvector → ready ```

### agentic-rag-sub-agents > Architecture > Chat / retrieval pipeline (Module 7–8) (chunk 7, 331 tokens, readme_section)
```text User message → LLM tool loop (max 3 iterations)              → search_documents | query_database | web_search | analyze_document              → stream final answer → save metadata (sources, tools, SQL) ```  **Sub-agent routing (`analyze_document`):** If the document's total tokens fit `SUB_AGENT_CONTEXT_TOKEN_BUDGET`, the analyst runs a single LLM pass over stitched chunks. Larger document...

### agentic-rag-sub-agents > Getting started > Prerequisites (chunk 8, 132 tokens, readme_section)
1. [Supabase](https://supabase.com) project with **Email** auth enabled 2. [OpenAI](https://platform.openai.com) API key — `gpt-4o-mini` + `text-embedding-3-small` 3. **Optional:** [Cohere](https://cohere.com) API key for reranking (`COHERE_API_KEY`) 4. **Optional:** [Tavily](https://tavily.com) API key for web search (`TAVILY_API_KEY`) 5. **Optional:** Postgres pooler URL (`DATABASE_URL`) for Tex...

### agentic-rag-sub-agents > Getting started > 1. Database migrations (chunk 9, 196 tokens, readme_section)
Run in the Supabase **SQL Editor**, in order:  | # | Migration | Purpose | |---|-----------|---------| | 1 | `001_threads_messages.sql` | Chat threads and messages + RLS | | 2 | `002_documents_rag.sql` | Documents, chunks, pgvector, storage RLS | | 3 | `003_record_manager.sql` | Content hash, unique `(user_id, filename)` | | 4 | `004_metadata.sql` | `documents.metadata` jsonb | | 5 | `005_chunk_st...

### agentic-rag-sub-agents > Getting started > 2. Storage bucket (chunk 10, 18 tokens, readme_section)
Dashboard → **Storage** → create a **private** bucket named `documents`.

### agentic-rag-sub-agents > Getting started > 3. Environment (chunk 11, 54 tokens, readme_section)
```bash cp .env.example backend/.env cp .env.example frontend/.env ```  Fill in `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `OPENAI_API_KEY`, and matching `VITE_*` values. See [Configuration](#configuration) for all options.

### agentic-rag-sub-agents > Getting started > 4. Backend (chunk 12, 63 tokens, readme_section)
```bash cd backend python -m venv venv venv\Scripts\activate          # Windows # source venv/bin/activate     # macOS/Linux pip install -r requirements.txt uvicorn app.main:app --reload --port 8000 ```  Health check: `curl http://localhost:8000/health`

### agentic-rag-sub-agents > Getting started > 5. Frontend (chunk 13, 37 tokens, readme_section)
```bash cd frontend npm install npm run dev ```  Open **http://localhost:5173** — sign up, upload documents on **Documents**, then chat on **Chat**.

### agentic-rag-sub-agents > Getting started > Windows dev scripts (chunk 14, 65 tokens, readme_section)
From the repo root:  ```bat Scripts\start-dev.bat    # launches backend + frontend in separate windows Scripts\stop-dev.bat     # stops project servers ```  The start script auto-selects an available backend port (8000–8002) and configures the Vite proxy.  ---

### agentic-rag-sub-agents > Configuration (chunk 15, 302 tokens, readme_section)
All variables are documented in `.env.example`. Key groups:  | Group | Variables | Notes | |-------|-----------|-------| | Core | `SUPABASE_*`, `OPENAI_*`, `CORS_ORIGINS` | Required | | RAG | `RAG_TOP_K`, `RAG_MATCH_THRESHOLD`, `CHUNK_SIZE`, `CHUNK_OVERLAP` | Retrieval tuning | | Chunking | `MAX_CHUNK_TOKENS`, `MIN_HEADINGS_FOR_SECTION` | Structure-aware routing | | Metadata | `METADATA_EXTRACTION...

### agentic-rag-sub-agents > API reference (chunk 16, 134 tokens, readme_section)
| Method | Path | Description | |--------|------|-------------| | `GET` | `/health` | Health check | | `GET` | `/api/me` | Auth test (Bearer JWT) | | `GET` | `/api/documents` | List current user's documents (includes `content_hash`, `metadata`) | | `POST` | `/api/documents/upload` | Multipart upload; response includes `ingest_action` | | `DELETE` | `/api/documents/{id}` | Delete document, chunks, ...

### agentic-rag-sub-agents > API reference > Supported upload formats (chunk 17, 22 tokens, readme_section)
`.txt` · `.md` · `.pdf` · `.docx` · `.html` (max size: `MAX_UPLOAD_BYTES`, default 10 MB)

### agentic-rag-sub-agents > API reference > Record manager (`ingest_action`) (chunk 18, 124 tokens, readme_section)
Per user, each **filename** is one logical slot:  | Scenario | `ingest_action` | Behavior | |----------|-----------------|----------| | New filename | `created` | New row; parse, chunk, embed | | Same filename, same SHA-256 hash, status `ready` | `unchanged` | Return existing row; no re-processing | | Same filename, different hash | `updated` | Same document `id`; replace storage, re-index |  Hash...

### agentic-rag-sub-agents > API reference > Chat stream example (chunk 19, 61 tokens, readme_section)
```bash curl -N -X POST http://localhost:8000/api/chat/stream \   -H "Authorization: Bearer YOUR_SUPABASE_JWT" \   -H "Content-Type: application/json" \   -d '{"thread_id":"THREAD_UUID","content":"What does the document say about X?"}' ```  ---

### agentic-rag-sub-agents > LangSmith tracing (chunk 20, 326 tokens, readme_section)
Enable in `backend/.env`:  ```env LANGSMITH_API_KEY=lsv2_... LANGSMITH_TRACING=true LANGSMITH_PROJECT=agentic-rag-module-1 ```  Set `LANGSMITH_LOG_CHUNK_TEXT=true` to log full chunk bodies (default: 200-char snippets).  | Span | When | What you see | |------|------|--------------| | `chat_turn` | Each chat message | `thread_id`, query, tool usage | | `rag_retrieve` | `search_documents` tool | File...

### agentic-rag-sub-agents > Project structure (chunk 21, 209 tokens, readme_section)
```text agentic-rag-sub-agents/ ├── backend/app/ │   ├── main.py              FastAPI entry point │   ├── config.py            Settings (Pydantic) │   ├── routes/              chat.py, documents.py │   └── services/            chunking, embedding, hybrid, reranker, │                            ingestion, metadata, parsing, retrieval, │                            sub_agent, tracing, tool_dispatcher...

### agentic-rag-sub-agents > Security smoke test (chunk 22, 75 tokens, readme_section)
1. Create User A and User B (separate sign-ups) 2. User A uploads a document and asks a grounded question 3. As User B, confirm the document is not visible and chat does not retrieve User A's chunks 4. Optional: `POST /api/chat/stream` with User B's JWT and User A's `thread_id` → expect **403**  ---

### agentic-rag-sub-agents > Module progress (chunk 23, 206 tokens, readme_section)
| Module | Status | Summary | |--------|--------|---------| | 1 — App shell + observability | Complete | Auth, threaded chat, SSE streaming, LangSmith | | 2 — BYO retrieval + RAG | Complete | Upload, chunk, embed, pgvector, source citations | | 3 — Record manager | Complete | Content hashing, skip unchanged, update in place | | 4 — Metadata extraction | Complete | LLM structured metadata per docum...

### agentic-rag-sub-agents > Releases (chunk 24, 169 tokens, readme_section)
| Version | Scope | |---------|-------| | [v1](https://github.com/HamzaFayaz/agentic-rag-sub-agents/releases/tag/v1) | Modules 1 & 2 — App shell + RAG | | [v2](https://github.com/HamzaFayaz/agentic-rag-sub-agents/releases/tag/v2) | Module 3 — Record manager + UI polish | | [v3](https://github.com/HamzaFayaz/agentic-rag-sub-agents/releases/tag/v3) | Modules 4–6 — Metadata, multi-format, hybrid retr...

### agentic-rag-sub-agents > Further reading (chunk 25, 157 tokens, readme_section)
- [`PRD.md`](PRD.md) — full product scope and module roadmap - [`PROGRESS.md`](PROGRESS.md) — implementation checklist - [`Discussion/module-7-tool-routing-flow.md`](Discussion/module-7-tool-routing-flow.md) — Module 7 agent flow (diagram + file map) - [`Discussion/modules-7-8.md`](Discussion/modules-7-8.md) — Module 8 sub-agent design - [`cursor.md`](cursor.md) — agent / development conventions -...
