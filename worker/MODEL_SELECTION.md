# Search Helper — Qwen model selection

Guide for picking a model from the Qwen free-trial quota (~1M tokens per model).
Set the choice in `worker/.env`:

```env
QWEN_MODEL=<model-id>
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

## What the worker needs

- **Text** chat (compressed WebBridge snapshots — not screenshots)
- **Function / tool calling** (`click`, `snapshot`, `navigate`, `evaluate`)
- **Multi-step** ReAct loop + JSON job arrays

## Skip these categories

| Category | Examples |
|----------|----------|
| Vision (VL) | `qwen3-vl-*`, `qwen-vl-*`, `qwen2.5-vl-*`, `qwen-vl-plus-*` |
| Visual reasoning | `qvq-max`, `qvq-max-latest`, `qvq-max-2025-03-25` |
| Thinking (extra tokens) | `*-thinking-*`, `qwen3-next-80b-a3b-thinking` |
| Code-only | `qwen3-coder-plus-*`, `qwen3-coder-flash`, `qwen3-coder-30b-a3b-instruct` |
| Translation | `qwen-mt-turbo`, `qwen-mt-plus` |

---

## Tier 1 — Diagnostic (“LLM issue or code issue?”)

Run **one** search with one of these. If it still fails like run-41 (stuck on first job, same reject loop), the problem is **code / prompts / WebBridge**, not model IQ.

| Priority | Model ID |
|----------|----------|
| 1 | `qwen3-max-2025-10-30` |
| 2 | `qwen-max` |
| 3 | `qwen-max-2025-01-25` |
| 4 | `qwen3-235b-a22b-instruct-2507` |
| 5 | `qwen3-235b-a22b` |
| 6 | `qwen2.5-72b-instruct` |
| 7 | `qwen3-next-80b-a3b-instruct` |

**Recommended first diagnostic pick:** `qwen3-max-2025-10-30`

---

## Tier 2 — Daily dev (after diagnostic passes)

Strong enough for browser agent; much cheaper than max tier.

| Priority | Model ID |
|----------|----------|
| 1 | `qwen-plus-2025-09-11` |
| 2 | `qwen-plus-2025-07-28` |
| 3 | `qwen-plus-latest` |
| 4 | `qwen-plus-2025-07-14` |
| 5 | `qwen-plus-2025-04-28` |

**Recommended production dev pick:** `qwen-plus-2025-09-11`

---

## Tier 3 — Mid-size instruct (backup)

| Model ID |
|----------|
| `qwen3-32b` |
| `qwen3-30b-a3b` |
| `qwen3-30b-a3b-instruct-2507` |
| `qwen3-8b` *(marginal — may struggle on 40-step agent loop)* |

---

## Tier 4 — Quota-saving smoke tests only

| Model ID |
|----------|
| `qwen-flash-2025-07-28` |
| `qwen-turbo-latest` |

Use for API / worker startup checks — not reliable to judge agent quality.

---

## Suggested test plan (separate 1M quota per model)

| Run | Model | Purpose |
|-----|-------|---------|
| A | `qwen3-max-2025-10-30` | Rule out LLM weakness |
| B | `qwen-plus-2025-09-11` | Realistic ongoing dev model |
| C | `qwen-flash-2025-07-28` | Cheap sanity check |

### How to read results

| Outcome | Likely cause |
|---------|----------------|
| A works, B works | Code fixes OK — use **plus** going forward |
| A works, B fails | Need stronger model or prompt tweaks |
| A fails same as run-41 | **Code / guard / WebBridge** — not model shopping |

### Log signals

| Log pattern | Meaning |
|-------------|---------|
| `accumulated=1` stuck, `job_rows=7+` | Agent loop / accumulation |
| Nudge says `Next click: @e28` but clicks `@e26` | LLM not following hints |
| `jobDetailReady: false` forever | Detail panel / WebBridge |

---

## Quick smoke test

After changing `worker/.env`:

```powershell
cd ..
python scripts/test_qwen.py
```

Then restart the worker:

```powershell
cd worker
.\.venv\Scripts\python.exe main.py
```

---

## References

- [Qwen OpenAI compatible API](https://docs.qwencloud.com/api-reference/toolkitframework/openai-compatible/overview)
- [Function calling](https://docs.qwencloud.com/developer-guides/text-generation/function-calling)
- Project: `System Design/llm-routing-and-cost-plan.md`
