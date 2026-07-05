"""OpenAI-compatible tool schemas for Kimi WebBridge actions."""

from __future__ import annotations

from typing import Any

WEBBRIDGE_TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "navigate",
            "description": "Open a URL in the browser. Use newTab=false to reuse the current tab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Full URL to open"},
                    "newTab": {
                        "type": "boolean",
                        "description": "Open in a new tab when true (default true for first page)",
                    },
                    "group_title": {
                        "type": "string",
                        "description": "Chrome tab group label (set on first navigate of the task)",
                    },
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "snapshot",
            "description": (
                "Read the current page accessibility tree with @e element refs. "
                "Use @e refs for click and fill."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Click an element by @e ref from snapshot or CSS selector.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "@e ref or CSS selector"},
                },
                "required": ["selector"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fill",
            "description": "Clear and type into an input, textarea, or contenteditable field.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "value": {"type": "string"},
                },
                "required": ["selector", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "evaluate",
            "description": "Run JavaScript on the page when snapshot has no @e ref.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tabs",
            "description": "List open tabs in the current session.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_tab",
            "description": "Select an already-open tab as current by URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "active": {"type": "boolean"},
                },
                "required": ["url"],
            },
        },
    },
]
