"""Test a specific model on Qwen Cloud (usage: python scripts/test_model.py deepseek-v4-flash)."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

JOB_SCORE_PROMPT = (
    "Score this job 0-100 for a Python developer with FastAPI and LangGraph experience.\n"
    "Job: Senior Python Engineer - build multi-agent systems with LLMs, FastAPI, browser automation.\n"
    'Reply JSON only: {"score": number, "reason": "one sentence"}'
)


def main() -> int:
    model = sys.argv[1] if len(sys.argv) > 1 else os.getenv("QWEN_MODEL", "qwen3.7-plus")
    api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    base_url = os.getenv(
        "QWEN_BASE_URL",
        "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    ).strip()

    if not api_key:
        print("FAIL: DASHSCOPE_API_KEY missing in .env")
        return 1

    print(f"Model: {model}")
    client = OpenAI(api_key=api_key, base_url=base_url)

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": JOB_SCORE_PROMPT}],
            max_tokens=256,
        )
    except Exception as exc:
        print(f"FAIL: {exc}")
        return 1

    reply = (completion.choices[0].message.content or "").strip()
    tokens = completion.usage.total_tokens if completion.usage else "?"
    print(f"Response:\n{reply}")
    print(f"\nTokens used: {tokens}")
    print("SUCCESS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
