"""Phase and workflow context — stateful containers for pipeline execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .seed import Seed
from .types import (
    AmbiguityScore,
    DriftScore,
    Phase,
    Tier,
)


@dataclass
class DriftMetrics:
    """3-component drift measurement."""

    goal: float = 0.0
    constraint: float = 0.0
    ontology: float = 0.0

    @property
    def composite(self) -> DriftScore:
        """Weighted drift: 0.50 × goal + 0.30 × constraint + 0.20 × ontology."""
        return 0.50 * self.goal + 0.30 * self.constraint + 0.20 * self.ontology

    @property
    def is_within_threshold(self) -> bool:
        """Drift ≤ 0.3 is acceptable."""
        return self.composite <= 0.3


@dataclass
class PhaseContext:
    """Context passed to each phase execution."""

    phase: Phase
    seed: Seed
    iteration: int = 0
    drift: DriftMetrics = field(default_factory=DriftMetrics)
    tier: Tier = Tier.FRUGAL
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def ambiguity(self) -> AmbiguityScore:
        return self.seed.ambiguity_score


@dataclass
class WorkflowContext:
    """Aggregate state across the full 6-phase pipeline."""

    seed: Seed
    current_phase: Phase = Phase.BIG_BANG
    tier: Tier = Tier.FRUGAL
    drift: DriftMetrics = field(default_factory=DriftMetrics)
    total_iterations: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)
    started_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    # Autodidact integration: thermodynamic yield accumulator
    thermo_yield_total: float = 0.0

    def phase_context(self) -> PhaseContext:
        """Create a PhaseContext snapshot for current state."""
        return PhaseContext(
            phase=self.current_phase,
            seed=self.seed,
            iteration=self.total_iterations,
            drift=self.drift,
            tier=self.tier,
        )

    def advance_phase(self) -> None:
        """Move to next phase in the pipeline."""
        phases = list(Phase)
        idx = phases.index(self.current_phase)
        if idx < len(phases) - 1:
            self.current_phase = phases[idx + 1]

    def record_event(self, event_type: str, payload: dict[str, Any]) -> None:
        """Append event to local history."""
        self.events.append(
            {
                "event_type": event_type,
                "payload": payload,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "phase": self.current_phase.name,
            }
        )
        self.total_iterations += 1
