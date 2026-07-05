"""Qwen ReAct loop driving Kimi WebBridge tools for job search."""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

from worker.config import WorkerSettings
from worker.models import WorkerTask
from worker.prompts import build_search_task
from worker.providers.webbridge import WebBridgeClient
from worker.webbridge_tools import WEBBRIDGE_TOOL_DEFINITIONS

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are JobPilot Search Helper — a browser agent that searches job sites.

Rules:
- Use WebBridge tools to navigate, read pages (snapshot), click, and fill fields.
- Prefer @e refs from snapshot for click/fill — they survive layout changes.
- Use ONE browser tab for the entire task — navigate with newTab=false after the first page load.
- One session per task: keep using the same browser tab group.
- Follow the user task steps exactly (filters, date posted, workplace type).
- When you have enough jobs, respond with ONLY a JSON array of job objects — no markdown fences.
- Each job object: title, company, url, descriptionText, sourcePlatform.
- If blocked by captcha or login wall, stop and explain briefly in plain text instead of JSON.
"""


def _build_client(settings: WorkerSettings) -> OpenAI:
    return OpenAI(
        api_key=settings.dashscope_api_key,
        base_url=settings.qwen_base_url,
    )


def _truncate(text: str, max_chars: int = 12000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n…[truncated]"


async def _run_tool(
    client: WebBridgeClient,
    name: str,
    args: dict[str, Any],
    *,
    session: str,
) -> str:
    try:
        result = await client.command(name, args, session=session)
        return _truncate(json.dumps(result, ensure_ascii=False))
    except Exception as exc:
        logger.warning("WebBridge tool %s failed: %s", name, exc)
        return json.dumps({"error": str(exc)})


async def run_search_agent(
    task: WorkerTask,
    settings: WorkerSettings,
    webbridge: WebBridgeClient,
) -> str:
    """Run Qwen + WebBridge until final text (expected JSON array)."""
    session = f"jobpilot-run-{task.run_id}"
    user_task = build_search_task(task)
    llm = _build_client(settings)

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_task},
    ]

    for step in range(settings.agent_max_steps):
        completion = llm.chat.completions.create(
            model=settings.qwen_model,
            temperature=0.2,
            messages=messages,
            tools=WEBBRIDGE_TOOL_DEFINITIONS,
            tool_choice="auto",
        )
        choice = completion.choices[0].message

        if choice.tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": choice.content or "",
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments,
                            },
                        }
                        for call in choice.tool_calls
                    ],
                }
            )
            for call in choice.tool_calls:
                fn_name = call.function.name
                try:
                    fn_args = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    fn_args = {}
                if not isinstance(fn_args, dict):
                    fn_args = {}

                if fn_name == "navigate":
                    fn_args.setdefault("group_title", "JobPilot search")
                    # Reuse the user's Chrome tab — do not spawn extra windows/tabs.
                    fn_args.setdefault("newTab", False)

                logger.info("WebBridge step %s: %s %s", step + 1, fn_name, list(fn_args.keys()))
                tool_result = await _run_tool(webbridge, fn_name, fn_args, session=session)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": tool_result,
                    }
                )
            continue

        final_text = (choice.content or "").strip()
        if final_text:
            logger.info("Agent finished after %s steps", step + 1)
            return final_text

        messages.append({"role": "assistant", "content": ""})
        messages.append(
            {
                "role": "user",
                "content": "Continue with tools or return the final JSON array of jobs.",
            }
        )

    raise RuntimeError(f"Search agent exceeded {settings.agent_max_steps} steps without finishing.")
