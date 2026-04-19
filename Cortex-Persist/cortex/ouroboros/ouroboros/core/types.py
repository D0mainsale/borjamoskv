"""Result[T,E] monad, enums, and type aliases for Ouroboros."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Generic, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")


# ── Result Monad ──────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    """Success variant."""

    value: T

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self.value

    def unwrap_err(self) -> None:
        raise ValueError("Called unwrap_err on Ok")


@dataclass(frozen=True, slots=True)
class Err(Generic[E]):
    """Error variant."""

    error: E

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def unwrap(self) -> None:
        raise ValueError(f"Called unwrap on Err: {self.error}")

    def unwrap_err(self) -> E:
        return self.error


Result = Union[Ok[T], Err[E]]


# ── Enums ─────────────────────────────────────────────────────


class Tier(Enum):
    """PAL Router cost tiers."""

    FRUGAL = "frugal"  # 1x cost
    STANDARD = "standard"  # 10x cost
    FRONTIER = "frontier"  # 30x cost

    @property
    def cost_multiplier(self) -> int:
        return {Tier.FRUGAL: 1, Tier.STANDARD: 10, Tier.FRONTIER: 30}[self]


class Phase(Enum):
    """6-phase pipeline stages."""

    BIG_BANG = 0
    PAL_ROUTER = 1
    DOUBLE_DIAMOND = 2
    RESILIENCE = 3
    EVALUATION = 4
    SECONDARY = 5


class StagnationPattern(Enum):
    """4 deterministic stagnation detection patterns."""

    SPINNING = auto()  # SHA-256 output hash repeated ≥3
    OSCILLATION = auto()  # A→B→A→B alternation ≥2 cycles
    NO_DRIFT = auto()  # Drift delta ε < 0.01 for 3 iterations
    DIMINISHING_RETURNS = auto()  # Progress rate < 0.01 for 3 iterations


class Persona(Enum):
    """5 lateral thinking personas."""

    HACKER = "hacker"
    RESEARCHER = "researcher"
    SIMPLIFIER = "simplifier"
    ARCHITECT = "architect"
    CONTRARIAN = "contrarian"


class DiamondPhase(Enum):
    """Double Diamond 4-phase cycle."""

    DISCOVER = auto()
    DEFINE = auto()
    DESIGN = auto()
    DELIVER = auto()


class EvalStage(Enum):
    """3-stage evaluation pipeline."""

    MECHANICAL = 1  # $0 checks
    SEMANTIC = 2  # $$ LLM verification
    CONSENSUS = 3  # $$$ multi-model voting


class RealityLevel(Enum):
    """Ω9 truth enforcement."""

    C5_REAL = "C5-REAL"
    C4_SIMULATION = "C4-SIMULACIÓN"


# ── Type Aliases ──────────────────────────────────────────────

AmbiguityScore = float  # 0.0 (crystal clear) → 1.0 (total ambiguity)
DriftScore = float  # 0.0 (on track) → 1.0 (fully drifted)
SimilarityScore = float  # 0.0 (no match) → 1.0 (identical)
ComplexityScore = float  # 0.0 (trivial) → 1.0 (frontier)
SemanticScore = float  # 0.0 (fail) → 1.0 (perfect)
