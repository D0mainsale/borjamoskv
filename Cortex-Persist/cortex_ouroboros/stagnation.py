"""
Ouroboros Stagnation Detector — 4-Pattern Taxonomy.
Stateless: operates on generation window only.
Law Ω2: Detection is O(n) on window, not O(n²) on full lineage.
"""
from __future__ import annotations

from typing import Optional

from .types import (
    Generation,
    StagnationPattern,
    STAGNATION_WINDOW,
    SPINNING_REPEAT_COUNT,
    OSCILLATION_CYCLE_COUNT,
    DRIFT_EPSILON,
    PROGRESS_EPSILON,
)


def detect(history: list[Generation]) -> Optional[StagnationPattern]:
    """
    Scan generation history for stagnation patterns.
    Returns first detected pattern or None.
    Priority: SPINNING > OSCILLATION > NO_DRIFT > DIMINISHING_RETURNS.
    """
    if len(history) < STAGNATION_WINDOW:
        return None

    window = history[-max(SPINNING_REPEAT_COUNT, STAGNATION_WINDOW * 2):]

    # ── SPINNING: same output hash repeated ≥3x ──────────────
    if len(window) >= SPINNING_REPEAT_COUNT:
        recent_hashes = [g.output_hash for g in window[-SPINNING_REPEAT_COUNT:]]
        if recent_hashes[0] and len(set(recent_hashes)) == 1:
            return StagnationPattern.SPINNING

    # ── OSCILLATION: A→B→A→B pattern ≥2 cycles ──────────────
    if len(window) >= OSCILLATION_CYCLE_COUNT * 2:
        tail = [g.output_hash for g in window[-(OSCILLATION_CYCLE_COUNT * 2):]]
        if tail[0] and tail[0] == tail[2] and tail[1] == tail[3] and tail[0] != tail[1]:
            return StagnationPattern.OSCILLATION

    # ── NO_DRIFT: drift delta < ε for ≥3 iterations ─────────
    if len(window) >= STAGNATION_WINDOW:
        drifts = [g.drift for g in window[-STAGNATION_WINDOW:]]
        deltas = [abs(drifts[i] - drifts[i - 1]) for i in range(1, len(drifts))]
        if all(d < DRIFT_EPSILON for d in deltas):
            return StagnationPattern.NO_DRIFT

    # ── DIMINISHING_RETURNS: progress rate < ε for ≥3 iter ──
    if len(window) >= STAGNATION_WINDOW:
        scores = [g.eval_score for g in window[-STAGNATION_WINDOW:]]
        rates = [scores[i] - scores[i - 1] for i in range(1, len(scores))]
        if all(abs(r) < PROGRESS_EPSILON for r in rates):
            return StagnationPattern.DIMINISHING_RETURNS

    return None
