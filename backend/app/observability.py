"""Optional Logfire setup and safe domain-span helpers."""

from __future__ import annotations

import logging
import os
from contextlib import nullcontext
from functools import wraps
from typing import Any, ContextManager

from fastapi import FastAPI

from backend.app.config import settings

logger = logging.getLogger(__name__)
_configured = False

_SECRET_PATTERNS = (
    "authorization",
    "cookie",
    "password",
    "password_hash",
    "jwt",
    "access_token",
    "refresh_token",
    "api_key",
    "secret",
    "encryption_key",
)


def setup_observability(app: FastAPI) -> bool:
    """Configure Logfire once; failures never prevent API startup."""
    global _configured
    if _configured or not settings.logfire_enabled:
        return _configured

    try:
        import logfire
        from logfire import ScrubbingOptions

        os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = (
            "true" if settings.logfire_capture_content else "false"
        )
        logfire.configure(
            token=settings.logfire_token or None,
            send_to_logfire=True if settings.logfire_token else False,
            service_name=settings.logfire_project_name,
            environment=settings.logfire_environment,
            console=False,
            inspect_arguments=False,
            scrubbing=ScrubbingOptions(extra_patterns=_SECRET_PATTERNS),
        )
        logfire.instrument_fastapi(app, capture_headers=False)
        logfire.instrument_openai()
        _configured = True
    except Exception:
        logger.exception("Logfire setup failed; continuing without exported telemetry.")
    return _configured


def span(name: str, **attributes: Any) -> ContextManager[Any]:
    """Return a safe domain span or a no-op context manager."""
    if not settings.logfire_enabled or not _configured:
        return nullcontext()
    try:
        import logfire

        return logfire.span(name, **attributes)
    except Exception:
        logger.exception("Could not create Logfire span %s.", name)
        return nullcontext()


def instrument(name: str):
    """Instrument a synchronous domain boundary without capturing arguments."""
    def decorator(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            with span(name):
                return function(*args, **kwargs)

        return wrapped

    return decorator

