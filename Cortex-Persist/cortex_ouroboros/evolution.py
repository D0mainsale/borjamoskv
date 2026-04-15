"""
Ouroboros Evolution Engine — The Serpent.
L1 Supervisor: orchestrates the Centurion swarm through the evolutionary loop.

    Interview → Seed → Execute → Evaluate
        ^                           |
        +---- Evolutionary Loop ----+

Convergence: ontology_similarity ≥ 0.95
Max generations: 30
Law Ω3: Each cycle evolves, never repeats.
"""
from __future__ import annotations

import uuid
from dataclasses import replace
from typing import Optional

from .types import (
    Event,
    Generation,
    EvolutionAction,
    LateralPersona,
    CONVERGENCE_THRESHOLD,
    MAX_GENERATIONS,
    hash_content,
)
from .seed import Seed
from .event_store import EventStore
from .agents import (
    InterviewAgent,
    SeedAgent,
    ExecutorAgent,
    EvaluatorAgent,
    WonderAgent,
    AgentMessage,
)


class EvolutionSupervisor:
    """
    L1 Supervisor: Orchestrates the Ouroboros loop.
    Delegates to L2 Centurions (agents) for each phase.
    Emits events to EventStore for persistence and replay.
    """

    def __init__(self, event_store: EventStore, session_id: Optional[str] = None):
        self.event_store = event_store
        self.session_id = session_id or uuid.uuid4().hex[:16]

        # L2 Centurions — spawned once, reused per cycle
        self._interviewer = InterviewAgent()
        self._seeder = SeedAgent()
        self._executor = ExecutorAgent()
        self._evaluator = EvaluatorAgent()
        self._wonderer = WonderAgent()

    def evolve_step(
        self,
        lineage: list[Generation],
        seed: Optional[Seed] = None,
        goal: str = "",
        constraints: tuple[str, ...] = (),
        success_criteria: tuple[str, ...] = (),
        context: str = "",
    ) -> tuple[Generation, EvolutionAction]:
        """
        One step of the Ouroboros.
        If seed is None and goal is provided, runs Interview → Seed first.
        Returns (new_generation, action).
        """
        gen_number = len(lineage) + 1

        # ── Hard cap ──────────────────────────────────────────
        if gen_number > MAX_GENERATIONS:
            gen = Generation(
                number=gen_number,
                action=EvolutionAction.ABORTED,
            )
            self._emit("evolution.generation.aborted", gen, "Max generations reached")
            return gen, EvolutionAction.ABORTED

        # ── Phase 0: Interview + Seed (first generation only) ─
        if seed is None:
            interview_msg = self._interviewer.execute({
                "goal": goal,
                "constraints": list(constraints),
                "success_criteria": list(success_criteria),
            })

            if not interview_msg.payload.get("gate_passed"):
                gen = Generation(
                    number=gen_number,
                    action=EvolutionAction.ABORTED,
                )
                self._emit("evolution.interview.failed", gen, 
                           f"Ambiguity: {interview_msg.payload.get('ambiguity_score')}")
                return gen, EvolutionAction.ABORTED

            seed_msg = self._seeder.execute({
                "goal": goal,
                "constraints": list(constraints),
                "success_criteria": list(success_criteria),
                "context": context,
            })

            if seed_msg.payload.get("status") != "CRYSTALLIZED":
                gen = Generation(
                    number=gen_number,
                    action=EvolutionAction.ABORTED,
                )
                self._emit("evolution.seed.rejected", gen, seed_msg.payload.get("error", ""))
                return gen, EvolutionAction.ABORTED

            seed = Seed(
                goal=goal,
                constraints=constraints,
                success_criteria=success_criteria,
                context=context,
                ambiguity_score=interview_msg.payload["ambiguity_score"],
            )
            self._emit_raw("evolution.seed.crystallized", {
                "seed_hash": seed.hash,
                "ambiguity": seed.ambiguity_score,
            })

        # ── Wonder phase: check stagnation before execution ───
        persona: Optional[LateralPersona] = None
        if lineage:
            wonder_msg = self._wonderer.execute({
                "history": lineage,
                "current_score": lineage[-1].eval_score if lineage else 0.0,
            })

            if wonder_msg.payload.get("stagnation_detected"):
                stag_pattern = wonder_msg.payload.get("persona_rotation")
                if stag_pattern:
                    persona = LateralPersona[stag_pattern]
                    self._emit_raw("evolution.stagnation.detected", {
                        "pattern": wonder_msg.payload["wonder"]["stagnation"],
                        "persona": stag_pattern,
                        "generation": gen_number,
                    })

        # ── Phase 2: Execute (Double Diamond) ─────────────────
        exec_msg = self._executor.execute({
            "seed": seed,
            "generation_number": gen_number,
            "persona": persona,
        })

        output = exec_msg.payload.get("output", "")
        output_hash = exec_msg.payload.get("output_hash", "")

        # ── Phase 4: Evaluate (Triple Gate) ───────────────────
        current_gen = Generation(
            number=gen_number,
            seed_hash=seed.hash,
            output_hash=output_hash,
        )

        eval_msg = self._evaluator.execute({
            "generation": current_gen,
            "seed": seed,
            "output": output,
            "lateral_adopted": persona is not None,
        })

        eval_score = eval_msg.payload.get("score", 0.0)
        drift = eval_msg.payload.get("drift", 1.0)
        passed = eval_msg.payload.get("passed", False)

        # ── Convergence check ─────────────────────────────────
        ontology_sim = self._compute_ontology_similarity(lineage, current_gen, eval_score)

        if ontology_sim >= CONVERGENCE_THRESHOLD and passed:
            action = EvolutionAction.CONVERGED
        elif not passed and persona is not None:
            # Already tried lateral thinking and still failing
            action = EvolutionAction.STAGNATED
        else:
            action = EvolutionAction.CONTINUE

        # ── Build final generation ────────────────────────────
        final_gen = Generation(
            id=current_gen.id,
            number=gen_number,
            seed_hash=seed.hash,
            eval_score=eval_score,
            drift=drift,
            ontology_similarity=ontology_sim,
            output_hash=output_hash,
            action=action,
            persona=persona,
        )

        self._emit("evolution.generation.created", final_gen, eval_msg.payload.get("reason", ""))

        return final_gen, action

    # ── Ontology Similarity ───────────────────────────────────

    def _compute_ontology_similarity(
        self,
        lineage: list[Generation],
        current: Generation,
        score: float,
    ) -> float:
        """
        Similarity = 0.50 × name_overlap + 0.30 × type_match + 0.20 × exact_match.
        Adapted for CORTEX: uses seed_hash stability and score progression.
        """
        if not lineage:
            return score  # First generation: score IS the similarity

        prev = lineage[-1]

        # Name overlap → seed hash stability
        name_overlap = 1.0 if current.seed_hash == prev.seed_hash else 0.0

        # Type match → output hash comparison (structural similarity)
        type_match = 0.0
        if prev.output_hash and current.output_hash:
            # Compare hash prefixes for partial similarity
            common = sum(
                1 for a, b in zip(prev.output_hash[:16], current.output_hash[:16])
                if a == b
            )
            type_match = common / 16.0

        # Exact match → score convergence
        exact_match = max(0.0, 1.0 - abs(score - prev.eval_score) * 5)

        similarity = 0.50 * name_overlap + 0.30 * type_match + 0.20 * exact_match

        return round(min(similarity, 1.0), 4)

    # ── Event Emission ────────────────────────────────────────

    def _emit(self, event_type: str, gen: Generation, reason: str = "") -> None:
        event = Event(
            aggregate_type="ouroboros",
            aggregate_id=self.session_id,
            event_type=event_type,
            payload={
                "id": gen.id,
                "number": gen.number,
                "seed_hash": gen.seed_hash,
                "eval_score": gen.eval_score,
                "drift": gen.drift,
                "ontology_similarity": gen.ontology_similarity,
                "output_hash": gen.output_hash,
                "action": gen.action.name,
                "persona": gen.persona.name if gen.persona else None,
                "reason": reason,
            },
        )
        self.event_store.append(event)

    def _emit_raw(self, event_type: str, payload: dict) -> None:
        event = Event(
            aggregate_type="ouroboros",
            aggregate_id=self.session_id,
            event_type=event_type,
            payload=payload,
        )
        self.event_store.append(event)
