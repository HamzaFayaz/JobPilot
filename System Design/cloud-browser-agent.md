# Cloud browser agent (Qwen ReAct on ECS)

**Status:** Feature branch `feat/cloud-react-worker`  
**Goal:** Judges install Search Helper + WebBridge only — **no Dashscope key on the PC**.

## Architecture

```text
UI / LangGraph (ECS)
  → enqueue worker_tasks (agentMode=cloud)
  → wait for completed listings (unchanged contract)

Cloud ReAct (ECS: backend/app/services/browser_agent/)
  → Qwen tool decisions (server DASHSCOPE_API_KEY)
  → queue tool commands for the Helper

Search Helper (user PC)
  → claim task → POST .../agent/attach
  → long-poll GET .../agent/next
  → execute navigate/snapshot/click/fill/evaluate/cdp via WebBridge
  → POST .../agent/tool-result
  → exit when type=done (backend already completed the task + rewrite)
```

## Protocol (WORKER_TOKEN auth)

| Step | Method | Path |
|------|--------|------|
| Claim | `GET` | `/api/worker/tasks/next` (payload includes `agentMode`) |
| Attach | `POST` | `/api/worker/tasks/{id}/agent/attach` |
| Poll | `GET` | `/api/worker/tasks/{id}/agent/next?timeout=25` |
| Result | `POST` | `/api/worker/tasks/{id}/agent/tool-result` `{callId, result}` |

Poll body: `{type: tool|done|fail, callId?, name?, arguments?, session?, error?, code?}`

## Flags

| Where | Env | Default | Meaning |
|-------|-----|---------|---------|
| Backend | `BROWSER_AGENT_MODE` | `cloud` | Task payload `agentMode` |
| Helper | `AGENT_MODE` | `cloud` | `local` forces on-PC ReAct (needs Dashscope) |

Local fallback: set Helper `AGENT_MODE=local` + `DASHSCOPE_API_KEY` — uses existing `worker/agent_loop.py` and `POST .../result`.

## Judge setup

1. Pair in JobPilot Settings → paste token into Search Helper  
2. Install Kimi WebBridge **daemon v1.10.0** + **extension 1.11.3** (do not auto-upgrade)  
3. Open Chrome, LinkedIn logged in, start Helper  
4. Run Posts search — no model key on the PC  

Server must have `DASHSCOPE_API_KEY` for ReAct + listing rewrite + analysis.

## WebBridge lock

Unchanged — see `System Design/kimi-webbridge-provider.md`.
