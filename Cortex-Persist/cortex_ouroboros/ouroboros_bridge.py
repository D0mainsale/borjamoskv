"""
Ouroboros ↔ Swarm Bridge (P0).
Connects the Sovereign Nexus Mind (L0) to the Ouroboros 6-Phase Pipeline.
Law Ω1: Byzantine logic must survive hardware verification.
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from .types import (
    Generation, 
    Event, 
    Ok, 
    Err, 
    Result, 
    STAGNATION_PERSONA_MAP,
    LateralPersona
)
from .seed import crystallize, Seed
from .evaluator import Evaluator
from .stagnation import detect
from .event_store import EventStore


class OuroborosBridge:
    """
    Orchestration layer for a single Ouroboros lifecycle.
    Wraps the 6-phase pipeline for the Swarm.
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or uuid.uuid4().hex[:12]
        self.store = EventStore()
        self.evaluator = Evaluator()
        self.history: list[Generation] = []

    def initiate_interview(self, goal: str, constraints: list[str], criteria: list[str]) -> Result[Seed, str]:
        """
        Phase 0: Ambiguity Gate. Crystallize the Seed.
        """
        res = crystallize(
            goal=goal,
            constraints=tuple(constraints),
            success_criteria=tuple(criteria)
        )
        
        if isinstance(res, Ok):
            # Log the successful crystallization
            self.store.append(Event(
                aggregate_type="evolution",
                aggregate_id=self.session_id,
                event_type="evolution.seed.crystallized",
                payload={"goal": goal, "hash": res.value.hash}
            ))
            return res
        return res

    def process_generation_cycle(self, seed: Seed, output: str) -> Generation:
        """
        Phase 4 & 5: Evaluation, Stagnation, and Evolution Loop.
        1. Evaluate output against Seed.
        2. Detect stagnation in history.
        3. Rotate persona if needed.
        4. Append to event store.
        """
        # 1. Evaluate
        eval_res = self.evaluator.evaluate(
            generation=Generation(number=len(self.history)),
            seed=seed,
            output=output
        )

        # 2. Build Generation object
        gen = Generation(
            number=len(self.history) + 1,
            seed_hash=seed.hash,
            eval_score=eval_res.score,
            drift=eval_res.drift,
            output_hash=uuid.uuid4().hex[:8], # Mock hash for now
        )

        self.history.append(gen)

        # 3. Detect Stagnation
        pattern = detect(self.history)
        selected_persona = None
        if pattern:
            selected_persona = STAGNATION_PERSONA_MAP.get(pattern, LateralPersona.CONTRARIAN)
            object.__setattr__(gen, "persona", selected_persona)

        # 4. Persistence
        self.store.append(Event(
            aggregate_type="evolution",
            aggregate_id=self.session_id,
            event_type="evolution.generation.created",
            payload={
                "number": gen.number,
                "score": gen.eval_score,
                "drift": gen.drift,
                "persona": selected_persona.name if selected_persona else None,
                "stagnation": pattern.name if pattern else None
            }
        ))

        return gen
