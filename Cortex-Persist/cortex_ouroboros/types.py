"""
Ouroboros Evolutionary Loop — Foundation Types.
Law Ω5: Zero-Rhetoric. Every type earns its place.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Generic, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")


# ── Enums ──────────────────────────────────────────────────────────

class EvolutionAction(Enum):
    """Terminal action after each evolutionary step."""
    CONTINUE = auto()
    CONVERGED = auto()
    STAGNATED = auto()
    ABORTED = auto()


class EvalStage(Enum):
    """3-stage evaluation pipeline."""
    MECHANICAL = auto()   # $0 — lint, hash, structure
    SEMANTIC = auto()     # Heuristic local scoring
    CONSENSUS = auto()    # Multi-evaluator (conditional)


class StagnationPattern(Enum):
    """4-pattern stagnation taxonomy (Q00/ouroboros)."""
    SPINNING = auto()           # SHA-256 output hash repeated ≥3x
    OSCILLATION = auto()        # A→B→A→B alternation ≥2 cycles
    NO_DRIFT = auto()           # Drift delta ε < 0.01 for ≥3 iter
    DIMINISHING_RETURNS = auto()  # Progress rate < 0.01 for ≥3 iter


class LateralPersona(Enum):
    """5 personas for stagnation escape."""
    HACKER = auto()       # Affinity: SPINNING
    RESEARCHER = auto()   # Affinity: NO_DRIFT, DIMINISHING
    SIMPLIFIER = auto()   # Affinity: DIMINISHING, OSCILLATION
    ARCHITECT = auto()    # Affinity: OSCILLATION, NO_DRIFT
    CONTRARIAN = auto()   # Affinity: ALL


# ── Stagnation → Persona routing ──────────────────────────────────

STAGNATION_PERSONA_MAP: dict[StagnationPattern, LateralPersona] = {
    StagnationPattern.SPINNING: LateralPersona.HACKER,
    StagnationPattern.OSCILLATION: LateralPersona.ARCHITECT,
    StagnationPattern.NO_DRIFT: LateralPersona.RESEARCHER,
    StagnationPattern.DIMINISHING_RETURNS: LateralPersona.SIMPLIFIER,
}


# ── Result Type ───────────────────────────────────────────────────

@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T

@dataclass(frozen=True)
class Err(Generic[E]):
    error: E

Result = Union[Ok[T], Err[E]]


# ── Generation ────────────────────────────────────────────────────

@dataclass(frozen=True)
class Generation:
    """One generation in the evolutionary lineage."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    number: int = 0
    seed_hash: str = ""
    eval_score: float = 0.0
    drift: float = 1.0
    ontology_similarity: float = 0.0
    output_hash: str = ""
    action: EvolutionAction = EvolutionAction.CONTINUE
    persona: LateralPersona | None = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ── Event ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Event:
    """Append-only event for the EventStore. Dot-notation types."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    aggregate_type: str = ""      # e.g. "evolution"
    aggregate_id: str = ""        # session or lineage id
    event_type: str = ""          # e.g. "evolution.generation.created"
    payload: dict = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ── Constants ─────────────────────────────────────────────────────

CONVERGENCE_THRESHOLD: float = 0.95
MAX_GENERATIONS: int = 30
AMBIGUITY_GATE: float = 0.2
DRIFT_THRESHOLD: float = 0.3
EVAL_PASS_SCORE: float = 0.8

STAGNATION_WINDOW: int = 3       # Minimum history length for detection
SPINNING_REPEAT_COUNT: int = 3
OSCILLATION_CYCLE_COUNT: int = 2
DRIFT_EPSILON: float = 0.01
PROGRESS_EPSILON: float = 0.01


def hash_content(content: str) -> str:
    """SHA-256 hash for identity tracking."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
