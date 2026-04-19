"""
Ouroboros Seed — Immutable Specification.
"The Seed never changes; the path adapts."
Law Ω9: Ambiguity score is deterministic math, not LLM theater.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .types import AMBIGUITY_GATE, hash_content, Ok, Err, Result


@dataclass(frozen=True)
class Seed:
    """
    Frozen specification crystallized from interview responses.
    Once created, NEVER mutated. Evolution creates new Seeds.
    """
    goal: str
    constraints: tuple[str, ...] = ()
    success_criteria: tuple[str, ...] = ()
    context: str = ""
    ambiguity_score: float = 1.0

    @property
    def hash(self) -> str:
        """SHA-256 identity across generations."""
        content = f"{self.goal}|{'|'.join(self.constraints)}|{'|'.join(self.success_criteria)}"
        return hash_content(content)

    @property
    def is_clear(self) -> bool:
        """Gate: ambiguity ≤ 0.2"""
        return self.ambiguity_score <= AMBIGUITY_GATE


def compute_ambiguity(
    goal: str,
    constraints: tuple[str, ...],
    success_criteria: tuple[str, ...],
) -> float:
    """
    Ambiguity = 1 - Σ(clarity_i × weight_i)
    
    Weights (Q00/ouroboros):
      Goal:       0.40
      Constraint: 0.30
      Success:    0.30
    
    Clarity heuristic (C5-REAL, no LLM):
      - Length ≥ 20 chars → 0.3 base
      - Contains measurable terms (numbers, comparisons) → +0.3
      - Specificity (unique words / total words) → +0.4 × ratio
    """
    def _clarity(text: str) -> float:
        if not text.strip():
            return 0.0
        score = 0.0
        # Length baseline
        if len(text) >= 20:
            score += 0.3
        elif len(text) >= 10:
            score += 0.15
        # Measurability: contains numbers or comparison operators
        measurable_chars = set("0123456789<>=≥≤%$")
        if any(c in measurable_chars for c in text):
            score += 0.3
        # Specificity: unique word ratio
        words = text.lower().split()
        if words:
            unique_ratio = len(set(words)) / len(words)
            score += 0.4 * unique_ratio
        return min(score, 1.0)

    goal_clarity = _clarity(goal)

    constraint_clarity = 0.0
    if constraints:
        constraint_clarity = sum(_clarity(c) for c in constraints) / len(constraints)

    success_clarity = 0.0
    if success_criteria:
        success_clarity = sum(_clarity(s) for s in success_criteria) / len(success_criteria)

    weighted = (
        0.40 * goal_clarity
        + 0.30 * constraint_clarity
        + 0.30 * success_clarity
    )

    return round(1.0 - weighted, 4)


def crystallize(
    goal: str,
    constraints: tuple[str, ...] = (),
    success_criteria: tuple[str, ...] = (),
    context: str = "",
) -> Result[Seed, str]:
    """
    Factory: interview responses → immutable Seed.
    Returns Err if ambiguity gate fails.
    """
    score = compute_ambiguity(goal, constraints, success_criteria)
    seed = Seed(
        goal=goal,
        constraints=constraints,
        success_criteria=success_criteria,
        context=context,
        ambiguity_score=score,
    )

    if not seed.is_clear:
        return Err(
            f"Ambiguity gate FAILED: {score:.4f} > {AMBIGUITY_GATE}. "
            f"Refine goal/constraints/criteria before proceeding."
        )

    return Ok(seed)
