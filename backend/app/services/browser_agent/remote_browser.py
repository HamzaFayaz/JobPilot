"""BrowserCommandClient that executes tools on the paired Search Helper."""

from __future__ import annotations

from typing import Any

from backend.app.services.browser_agent.session import BrowserAgentSession


class RemoteBrowserClient:
    """Sends WebBridge tool commands to the worker via the agent session queue."""

    def __init__(self, session: BrowserAgentSession) -> None:
        self._session = session

    async def command(
        self,
        action: str,
        args: dict[str, Any] | None = None,
        *,
        session: str,
    ) -> dict[str, Any]:
        # Agent loop awaits this; underlying wait is thread-safe/blocking.
        return self._session.execute_tool_sync(action, args, session=session)
