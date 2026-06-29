"""Quick smoke test for Qwen Cloud API (Dashscope compatible mode)."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def main() -> int:
    api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    base_url = os.getenv(
        "QWEN_BASE_URL",
        "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    ).strip()
    model = os.getenv("QWEN_MODEL", "qwen3.7-plus").strip()

    if not api_key:
        print("FAIL: DASHSCOPE_API_KEY is missing in .env")
        return 1

    print(f"Base URL: {base_url}")
    print(f"Model:    {model}")
    print(f"API key:  {api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "API key:  (set)")
    print("Calling Qwen API...")

    client = OpenAI(api_key=api_key, base_url=base_url)

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Reply with exactly: JobPilot API OK"
                    ),
                }
            ],
            max_tokens=32,
        )
    except Exception as exc:
        print(f"FAIL: API request failed — {exc}")
        return 1

    reply = completion.choices[0].message.content or ""
    print(f"Response: {reply.strip()}")
    print("SUCCESS: Qwen API is working.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
