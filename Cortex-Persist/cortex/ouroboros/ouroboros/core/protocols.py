"""Shared protocols — structural interfaces for the Ouroboros engine."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ouroboros.core.types import Result


# ── Phase Protocol ────────────────────────────────────────────


@runtime_checkable
class PhaseResult(Protocol):
    """Result returned by phase execution."""

    @property
    def success(self) -> bool: ...

    @property
    def data(self) -> dict[str, Any]: ...

    @property
    def events(self) -> list[dict[str, Any]]: ...


@runtime_checkable
class IPhase(Protocol):
    """Interface for pipeline phases — phases communicate via events, never direct imports."""

    async def execute(self, context: Any) -> Result[Any, Any]: ...


# ── Provider Protocol ─────────────────────────────────────────


@runtime_checkable
class IProvider(Protocol):
    """LLM provider abstraction."""

    async def complete(
        self,
        prompt: str,
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str: ...

    async def complete_json(
        self,
        prompt: str,
        *,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> dict[str, Any]: ...


# ── Event Store Protocol ──────────────────────────────────────


@runtime_checkable
class IEventStore(Protocol):
    """Append-only event persistence."""

    async def append(
        self,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> str: ...

    async def replay(
        self,
        aggregate_type: str,
        aggregate_id: str,
    ) -> list[dict[str, Any]]: ...

    async def checkpoint(self, label: str) -> None: ...

    async def rollback(self, label: str) -> None: ...


# ── Agent Runtime Protocol ────────────────────────────────────


@runtime_checkable
class IAgentRuntime(Protocol):
    """Backend-neutral agent execution."""

    async def execute_task(
        self,
        task: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> Any: ...

    async def execute_task_to_result(
        self,
        task: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> Result[Any, Any]: ...


# ── Autodidact Integration Protocol ──────────────────────────


@runtime_checkable
class IAutopoiesisGate(Protocol):
    """Thermodynamic yield gate for Autodidact-Ω JIT integration."""

    def compute_yield(
        self,
        tokens_saved: int,
        cpu_cycles_saved: int,
        inference_cost: float,
    ) -> float: ...

    def should_proceed(self, net_yield: float) -> bool: ...
