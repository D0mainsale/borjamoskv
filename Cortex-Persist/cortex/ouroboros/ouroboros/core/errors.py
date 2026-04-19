"""Error hierarchy for Ouroboros — all expected failures, no bare exceptions."""

from __future__ import annotations


class OuroborosError(Exception):
    """Base error for all Ouroboros operations."""

    def __init__(self, message: str, *, phase: str | None = None) -> None:
        self.phase = phase
        super().__init__(message)


class AmbiguityGateError(OuroborosError):
    """Ambiguity score exceeds ≤0.2 threshold — seed cannot be generated."""

    def __init__(self, score: float) -> None:
        self.score = score
        super().__init__(
            f"Ambiguity gate failed: {score:.3f} > 0.2 threshold",
            phase="big_bang",
        )


class SecurityLimitError(OuroborosError):
    """Input exceeds DoS prevention limits."""

    def __init__(self, field: str, actual: int, limit: int) -> None:
        self.field = field
        self.actual = actual
        self.limit = limit
        super().__init__(
            f"Security limit exceeded: {field} = {actual:,} > {limit:,}",
            phase="security",
        )


class StagnationError(OuroborosError):
    """Stagnation pattern detected — lateral thinking required."""

    def __init__(self, pattern: str, iterations: int) -> None:
        self.pattern = pattern
        self.iterations = iterations
        super().__init__(
            f"Stagnation detected: {pattern} after {iterations} iterations",
            phase="resilience",
        )


class EscalationError(OuroborosError):
    """Tier escalation failed — already at FRONTIER."""

    def __init__(self, current_tier: str) -> None:
        self.current_tier = current_tier
        super().__init__(
            f"Cannot escalate beyond {current_tier}",
            phase="routing",
        )


class ConvergenceError(OuroborosError):
    """Evolutionary loop failed to converge within max generations."""

    def __init__(self, generations: int, similarity: float) -> None:
        self.generations = generations
        self.similarity = similarity
        super().__init__(
            f"Failed to converge after {generations} generations "
            f"(similarity: {similarity:.3f} < 0.95)",
            phase="evolution",
        )


class ProviderError(OuroborosError):
    """LLM provider call failed."""

    def __init__(self, provider: str, detail: str) -> None:
        self.provider = provider
        super().__init__(f"Provider {provider} failed: {detail}", phase="providers")


class EventStoreError(OuroborosError):
    """Persistence layer failure."""

    def __init__(self, operation: str, detail: str) -> None:
        self.operation = operation
        super().__init__(
            f"EventStore {operation} failed: {detail}", phase="persistence"
        )


class ThermoYieldError(OuroborosError):
    """Autodidact thermodynamic net yield is negative — abort branch."""

    def __init__(self, score: float) -> None:
        self.score = score
        super().__init__(
            f"Thermodynamic yield negative: {score:.4f} — branch aborted (Ω3)",
            phase="autopoiesis",
        )
