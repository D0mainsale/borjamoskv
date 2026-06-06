"""
CORTEX Hooks — Deterministic Lifecycle Event Bus.
Law Ω6: Handlers are pure functions. 5s timeout. No LLM calls.
Law Ω9: C5-REAL. Every emission is a verified state transition.

Hook Types:
  session_start  — Daemon boots
  pre_tool_use   — Before any tool call (can ABORT)
  post_tool_use  — After tool returns
  pre_eval       — Before evaluator gate
  post_eval      — After evaluator verdict
  session_end    — Session closes
"""
from __future__ import annotations

import signal
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Callable, Optional


# ── Types ──────────────────────────────────────────────────────────

VALID_HOOK_TYPES = frozenset({
    "session_start",
    "pre_tool_use",
    "post_tool_use",
    "pre_eval",
    "post_eval",
    "session_end",
})

HANDLER_TIMEOUT_SECONDS = 5


class HookAction(Enum):
    """Terminal action returned by a hook handler."""
    CONTINUE = auto()   # Proceed normally
    ABORT = auto()      # Veto the operation
    RETRY = auto()      # Request re-execution
    TRANSFORM = auto()  # Modify payload and continue


@dataclass(frozen=True)
class HookEvent:
    """Immutable event emitted to hook handlers."""
    type: str
    payload: dict
    session_id: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass(frozen=True)
class HookResult:
    """Aggregated result after all handlers for an event."""
    action: HookAction
    event: HookEvent
    modified_payload: Optional[dict] = None
    abort_reason: Optional[str] = None
    handler_count: int = 0
    errors: tuple[str, ...] = ()


# ── Timeout helper ─────────────────────────────────────────────────

class _HandlerTimeout(Exception):
    pass


def _timeout_handler(signum, frame):
    raise _HandlerTimeout("Handler exceeded timeout")


# ── Registry ───────────────────────────────────────────────────────

class HookRegistry:
    """
    FIFO-ordered hook handler registry.
    Handlers: (HookEvent) -> Optional[HookResult]
    If any handler returns ABORT, chain stops immediately.
    If any handler returns RETRY, result is RETRY (unless ABORT overrides).
    """

    def __init__(self):
        self._handlers: dict[str, list[tuple[str, Callable]]] = {
            t: [] for t in VALID_HOOK_TYPES
        }

    def on(
        self,
        event_type: str,
        handler: Callable[[HookEvent], Optional[HookResult]],
        name: Optional[str] = None,
    ) -> str:
        """
        Register a handler for the given event type.
        Returns handler ID for later removal.
        """
        if event_type not in VALID_HOOK_TYPES:
            raise ValueError(
                f"Invalid hook type '{event_type}'. "
                f"Valid: {sorted(VALID_HOOK_TYPES)}"
            )
        handler_id = name or uuid.uuid4().hex[:8]
        self._handlers[event_type].append((handler_id, handler))
        return handler_id

    def off(self, event_type: str, handler_id: str) -> bool:
        """Remove a handler by ID. Returns True if found."""
        if event_type not in VALID_HOOK_TYPES:
            return False
        before = len(self._handlers[event_type])
        self._handlers[event_type] = [
            (hid, fn) for hid, fn in self._handlers[event_type]
            if hid != handler_id
        ]
        return len(self._handlers[event_type]) < before

    def clear(self, event_type: Optional[str] = None) -> None:
        """Clear all handlers, or handlers for a specific type."""
        if event_type:
            if event_type in self._handlers:
                self._handlers[event_type] = []
        else:
            for t in self._handlers:
                self._handlers[t] = []

    def emit(self, event: HookEvent) -> HookResult:
        """
        Emit event to all registered handlers (FIFO order).
        Returns aggregated result.

        Chain semantics:
          - ABORT from any handler → immediate stop, return ABORT
          - RETRY from any handler → continue chain, return RETRY
          - TRANSFORM → merge modified_payload forward
          - CONTINUE → no effect
        """
        if event.type not in VALID_HOOK_TYPES:
            raise ValueError(f"Cannot emit invalid hook type '{event.type}'")

        handlers = self._handlers.get(event.type, [])
        if not handlers:
            return HookResult(
                action=HookAction.CONTINUE,
                event=event,
                handler_count=0,
            )

        final_action = HookAction.CONTINUE
        merged_payload = dict(event.payload)
        errors: list[str] = []

        for handler_id, handler_fn in handlers:
            try:
                result = self._call_with_timeout(handler_fn, event)
            except _HandlerTimeout:
                errors.append(
                    f"Handler '{handler_id}' timed out ({HANDLER_TIMEOUT_SECONDS}s)"
                )
                continue
            except Exception as exc:
                errors.append(f"Handler '{handler_id}' raised: {exc}")
                continue

            if result is None:
                continue

            # ABORT overrides everything
            if result.action == HookAction.ABORT:
                return HookResult(
                    action=HookAction.ABORT,
                    event=event,
                    abort_reason=result.abort_reason or f"Aborted by '{handler_id}'",
                    handler_count=handlers.index((handler_id, handler_fn)) + 1,
                    errors=tuple(errors),
                )

            # RETRY escalates (but doesn't stop chain)
            if result.action == HookAction.RETRY:
                final_action = HookAction.RETRY

            # TRANSFORM merges payload
            if result.action == HookAction.TRANSFORM and result.modified_payload:
                merged_payload.update(result.modified_payload)

        return HookResult(
            action=final_action,
            event=event,
            modified_payload=merged_payload if merged_payload != event.payload else None,
            handler_count=len(handlers),
            errors=tuple(errors),
        )

    def _call_with_timeout(
        self,
        handler: Callable,
        event: HookEvent,
    ) -> Optional[HookResult]:
        """Call handler with SIGALRM timeout (Unix only)."""
        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(HANDLER_TIMEOUT_SECONDS)
        try:
            return handler(event)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    @property
    def handler_count(self) -> int:
        """Total registered handlers across all types."""
        return sum(len(h) for h in self._handlers.values())

    def describe(self) -> dict[str, int]:
        """Return handler counts per event type."""
        return {t: len(h) for t, h in self._handlers.items()}


# ── Global Registry (Singleton Pattern) ───────────────────────────

_global_registry: Optional[HookRegistry] = None


def get_registry() -> HookRegistry:
    """Get or create the global hook registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = HookRegistry()
    return _global_registry


# ── Decorators ─────────────────────────────────────────────────────

def hooked_tool_execution(tool_name: str):
    """
    Decorator to wrap a tool execution with pre/post hooks.
    Law Ω6: Handlers are deterministic and timed.
    Law Ω9: Verified state transitions.
    """
    def decorator(func: Callable):
        from functools import wraps

        @wraps(func)
        def wrapper(*args, **kwargs):
            registry = get_registry()
            session_id = kwargs.get("session_id", "unknown_session")

            # 1. Pre-tool Hook
            pre_event = HookEvent(
                type="pre_tool_use",
                payload={"tool": tool_name, "args": args, "kwargs": kwargs},
                session_id=session_id,
            )
            pre_result = registry.emit(pre_event)

            if pre_result.action == HookAction.ABORT:
                return {
                    "status": "ABORTED",
                    "reason": pre_result.abort_reason or "Vetoed by hook",
                }

            # Merge transformed payload if needed
            effective_kwargs = kwargs
            if pre_result.modified_payload:
                effective_kwargs = {**kwargs, **pre_result.modified_payload}

            # 2. Execution
            try:
                result = func(*args, **effective_kwargs)
            except Exception as e:
                result = {"status": "ERROR", "error": str(e)}

            # 3. Post-tool Hook
            post_event = HookEvent(
                type="post_tool_use",
                payload={"tool": tool_name, "result": result},
                session_id=session_id,
            )
            registry.emit(post_event)

            return result

        return wrapper
    return decorator
