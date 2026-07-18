"""In-memory tool round-trip sessions between cloud agent and Search Helper.

The ReAct loop uses a sync OpenAI client, so it runs in a worker thread.
FastAPI long-poll / tool-result routes stay on the asyncio event loop.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

logger = logging.getLogger(__name__)

CommandType = Literal["tool", "done", "fail"]


@dataclass
class AgentPollItem:
    type: CommandType
    call_id: str | None = None
    name: str | None = None
    arguments: dict[str, Any] | None = None
    session: str | None = None
    error: str | None = None
    code: str | None = None


@dataclass
class _PendingTool:
    event: threading.Event = field(default_factory=threading.Event)
    result: Any = None
    error: Exception | None = None


@dataclass
class BrowserAgentSession:
    task_id: str
    user_id: int
    status: Literal["starting", "running", "done", "failed"] = "starting"
    error: str | None = None
    error_code: str | None = None
    agent_thread: threading.Thread | None = None
    agent_started: bool = False
    _command_queue: list[AgentPollItem] = field(default_factory=list, repr=False)
    _command_cv: threading.Condition = field(
        default_factory=threading.Condition, repr=False
    )
    _pending: dict[str, _PendingTool] = field(default_factory=dict, repr=False)
    _start_lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def execute_tool_sync(
        self,
        name: str,
        args: dict[str, Any] | None,
        *,
        session: str,
        timeout_seconds: float = 120.0,
    ) -> dict[str, Any]:
        """Called from the agent worker thread — blocks until the Helper returns."""
        call_id = str(uuid.uuid4())
        pending = _PendingTool()
        with self._command_cv:
            self._pending[call_id] = pending
            self._command_queue.append(
                AgentPollItem(
                    type="tool",
                    call_id=call_id,
                    name=name,
                    arguments=args or {},
                    session=session,
                )
            )
            self._command_cv.notify_all()

        if not pending.event.wait(timeout=timeout_seconds):
            with self._command_cv:
                self._pending.pop(call_id, None)
            raise TimeoutError(
                f"Worker timed out executing tool {name} (call {call_id})"
            )
        if pending.error is not None:
            raise pending.error
        result = pending.result
        if isinstance(result, dict):
            return result
        return {"value": result}

    def wait_for_command_sync(self, *, timeout_seconds: float) -> AgentPollItem | None:
        """Called from a thread (or via asyncio.to_thread) for long-poll."""
        with self._command_cv:
            if self.status in ("done", "failed") and not self._command_queue:
                return AgentPollItem(
                    type="fail" if self.status == "failed" else "done",
                    error=self.error,
                    code=self.error_code,
                )
            if not self._command_queue:
                self._command_cv.wait(timeout=timeout_seconds)
            if self._command_queue:
                return self._command_queue.pop(0)
            if self.status in ("done", "failed"):
                return AgentPollItem(
                    type="fail" if self.status == "failed" else "done",
                    error=self.error,
                    code=self.error_code,
                )
            return None

    def submit_tool_result(self, call_id: str, result: Any) -> bool:
        with self._command_cv:
            pending = self._pending.pop(call_id, None)
        if pending is None:
            return False
        pending.result = result
        pending.event.set()
        return True

    def mark_done(self) -> None:
        with self._command_cv:
            self.status = "done"
            self._command_queue.append(AgentPollItem(type="done"))
            self._command_cv.notify_all()

    def mark_failed(self, error: str, *, code: str = "cloud_agent_failed") -> None:
        with self._command_cv:
            self.status = "failed"
            self.error = error
            self.error_code = code
            self._command_queue.append(
                AgentPollItem(type="fail", error=error, code=code)
            )
            for pending in self._pending.values():
                pending.error = RuntimeError(error)
                pending.event.set()
            self._pending.clear()
            self._command_cv.notify_all()


_SESSIONS: dict[str, BrowserAgentSession] = {}
_SESSIONS_LOCK = threading.Lock()


def get_session(task_id: str) -> BrowserAgentSession | None:
    with _SESSIONS_LOCK:
        return _SESSIONS.get(task_id)


def get_or_create_session(task_id: str, user_id: int) -> BrowserAgentSession:
    with _SESSIONS_LOCK:
        existing = _SESSIONS.get(task_id)
        if existing:
            return existing
        session = BrowserAgentSession(task_id=task_id, user_id=user_id)
        _SESSIONS[task_id] = session
        return session


def drop_session(task_id: str) -> None:
    with _SESSIONS_LOCK:
        _SESSIONS.pop(task_id, None)
