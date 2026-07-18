"""Browser command client protocol — local WebBridge or remote worker bridge."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class BrowserCommandClient(Protocol):
    """Anything that can run a WebBridge-style tool command in a session."""

    async def command(
        self,
        action: str,
        args: dict[str, Any] | None = None,
        *,
        session: str,
    ) -> dict[str, Any]:
        ...
