"""
Ouroboros Evaluator — Triple Gate Pipeline.
Stage 1: Mechanical ($0) — deterministic checks.
Stage 2: Semantic (heuristic local) — C5-REAL, no LLM.
Stage 3: Consensus (conditional) — multi-evaluator trigger.
Law Ω9: All scoring is deterministic math. No theater.
"""
from __future__ import annotations

from dataclasses import dataclass

from .types import (
    EvalStage,
    Generation,
    EVAL_PASS_SCORE,
    DRIFT_THRESHOLD,
)
from .seed import Seed


# ── Consensus Triggers (6 conditions from Q00/ouroboros) ──────────

CONSENSUS_TRIGGERS = frozenset({
    "seed_modification",
    "ontology_evolution",
    "goal_reinterpretation",
    "high_drift",             # drift > 0.3
    "high_uncertainty",       # stage2 score uncertainty > 0.3
    "lateral_adoption",       # persona rotation occurred
})


@dataclass(frozen=True)
class EvalResult:
    """Frozen evaluation outcome."""
    stage: EvalStage
    score: float
    drift: float
    passed: bool
    triggers_consensus: bool = False
    reason: str = ""


class Evaluator:
    """
    3-stage evaluation pipeline.
    Swarm L2 Centurion: EvaluatorAgent wraps this engine.
    """

    def evaluate(
        self,
        generation: Generation,
        seed: Seed,
        output: str,
        lateral_adopted: bool = False,
    ) -> EvalResult:
        """Run progressive evaluation. Cheap first, expensive last."""

        # ── Stage 1: Mechanical ($0) ─────────────────────────
        mech = self._mechanical(output, seed)
        if not mech.passed:
            return mech

        # ── Stage 2: Semantic (heuristic) ────────────────────
        sem = self._semantic(output, seed, generation)
        if not sem.passed:
            return sem

        # ── Stage 3: Consensus (conditional) ─────────────────
        triggers = self._check_consensus_triggers(
            generation, seed, sem, lateral_adopted
        )
        if triggers:
            return EvalResult(
                stage=EvalStage.CONSENSUS,
                score=sem.score,
                drift=sem.drift,
                passed=sem.passed,
                triggers_consensus=True,
                reason=f"Consensus triggered: {', '.join(triggers)}",
            )

        return sem

    # ── Stage 1 ───────────────────────────────────────────────

    def _mechanical(self, output: str, seed: Seed) -> EvalResult:
        """$0 checks: non-empty, structure, hash."""
        if not output or not output.strip():
            return EvalResult(
                stage=EvalStage.MECHANICAL,
                score=0.0,
                drift=1.0,
                passed=False,
                reason="Empty output",
            )

        # Verify output contains references to goal keywords
        goal_words = set(seed.goal.lower().split())
        output_words = set(output.lower().split())
        overlap = len(goal_words & output_words)

        if overlap == 0:
            return EvalResult(
                stage=EvalStage.MECHANICAL,
                score=0.1,
                drift=1.0,
                passed=False,
                reason="Output has zero goal keyword overlap",
            )

        return EvalResult(
            stage=EvalStage.MECHANICAL,
            score=0.5,
            drift=0.5,
            passed=True,
            reason="Mechanical checks passed",
        )

    # ── Stage 2 ───────────────────────────────────────────────

    def _semantic(
        self, output: str, seed: Seed, generation: Generation
    ) -> EvalResult:
        """
        Heuristic scoring (C5-REAL, $0):
        - Goal alignment: keyword coverage
        - Constraint compliance: constraint terms present
        - Success criteria: criteria terms present
        - Drift: weighted composite
        """
        # Goal alignment (0.50 weight)
        goal_words = set(seed.goal.lower().split())
        output_words = set(output.lower().split())
        goal_score = (
            len(goal_words & output_words) / max(len(goal_words), 1)
        )

        # Constraint compliance (0.30 weight)
        constraint_score = 1.0
        if seed.constraints:
            hits = sum(
                1 for c in seed.constraints
                if any(w in output.lower() for w in c.lower().split())
            )
            constraint_score = hits / len(seed.constraints)

        # Success criteria (0.20 weight)
        criteria_score = 1.0
        if seed.success_criteria:
            hits = sum(
                1 for s in seed.success_criteria
                if any(w in output.lower() for w in s.lower().split())
            )
            criteria_score = hits / len(seed.success_criteria)

        # Composite
        score = (
            0.50 * goal_score
            + 0.30 * constraint_score
            + 0.20 * criteria_score
        )

        # Drift
        drift = (
            0.50 * (1.0 - goal_score)
            + 0.30 * (1.0 - constraint_score)
            + 0.20 * (1.0 - criteria_score)
        )

        passed = score >= EVAL_PASS_SCORE and drift <= DRIFT_THRESHOLD

        return EvalResult(
            stage=EvalStage.SEMANTIC,
            score=round(score, 4),
            drift=round(drift, 4),
            passed=passed,
            reason=f"Semantic: goal={goal_score:.2f} constraint={constraint_score:.2f} criteria={criteria_score:.2f}",
        )

    # ── Consensus Trigger Check ───────────────────────────────

    def _check_consensus_triggers(
        self,
        generation: Generation,
        seed: Seed,
        sem_result: EvalResult,
        lateral_adopted: bool,
    ) -> list[str]:
        """Return list of active triggers. Empty = no consensus needed."""
        triggers: list[str] = []

        if generation.seed_hash and generation.seed_hash != seed.hash:
            triggers.append("seed_modification")

        if sem_result.drift > DRIFT_THRESHOLD:
            triggers.append("high_drift")

        uncertainty = 1.0 - sem_result.score
        if uncertainty > 0.3:
            triggers.append("high_uncertainty")

        if lateral_adopted:
            triggers.append("lateral_adoption")

        return triggers
