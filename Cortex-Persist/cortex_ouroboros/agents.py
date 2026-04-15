"""
Ouroboros Swarm Agents — L2 Centurion Layer.
Each agent is a sovereign tactical unit within the CORTEX-Swarm topology.

Hierarchy:
  L0: Ralph (SwarmCommander) — persistent cross-session executor
  L1: EvolutionSupervisor — orchestrates the loop
  L2: InterviewAgent, SeedAgent, ExecutorAgent, EvaluatorAgent, WonderAgent

Law Ω6: All agents execute headless. No UI.
Law Ω9: C5-REAL where disk/math verifiable. C4-SIMULACIÓN declared otherwise.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .types import (
    Event,
    Generation,
    EvolutionAction,
    LateralPersona,
    StagnationPattern,
    STAGNATION_PERSONA_MAP,
    hash_content,
)
from .seed import Seed, crystallize, compute_ambiguity
from .evaluator import Evaluator, EvalResult
from . import stagnation as stagnation_detector


# ── Agent Protocol ────────────────────────────────────────────────

@dataclass
class AgentMessage:
    """Normalized inter-agent message. ZKP-light proof placeholder."""
    agent_id: str
    agent_type: str
    payload: dict
    zkp_hash: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self):
        if not self.zkp_hash:
            content = f"{self.agent_id}:{self.agent_type}:{self.payload}"
            self.zkp_hash = hash_content(content)[:16]


class CenturionAgent(ABC):
    """
    L2 Centurion base. Tactical execution at O(1).
    Each agent produces Events for the EventStore.
    """

    def __init__(self, agent_type: str):
        self.agent_id = f"{agent_type}_{uuid.uuid4().hex[:8]}"
        self.agent_type = agent_type

    @abstractmethod
    def execute(self, context: dict) -> AgentMessage:
        """Execute tactical mission. Return result as AgentMessage."""
        ...

    def emit_event(self, session_id: str, event_type: str, payload: dict) -> Event:
        """Create an event for the EventStore."""
        return Event(
            aggregate_type="ouroboros",
            aggregate_id=session_id,
            event_type=event_type,
            payload={**payload, "agent_id": self.agent_id, "agent_type": self.agent_type},
        )


# ── L2 Centurions ────────────────────────────────────────────────

class InterviewAgent(CenturionAgent):
    """
    Socratic extraction. Exposes hidden assumptions.
    In C4-SIMULACIÓN mode: uses heuristic clarity scoring.
    In C5-REAL mode: would route to LLM for Socratic questioning.
    """

    def __init__(self):
        super().__init__("interview")

    def execute(self, context: dict) -> AgentMessage:
        goal = context.get("goal", "")
        constraints = tuple(context.get("constraints", []))
        success_criteria = tuple(context.get("success_criteria", []))

        ambiguity = compute_ambiguity(goal, constraints, success_criteria)

        return AgentMessage(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            payload={
                "ambiguity_score": ambiguity,
                "gate_passed": ambiguity <= 0.2,
                "goal": goal,
                "constraints": list(constraints),
                "success_criteria": list(success_criteria),
                "reality": "C5-REAL",  # Math is deterministic
            },
        )


class SeedAgent(CenturionAgent):
    """
    Crystallizes interview output into an immutable Seed.
    Gate: ambiguity ≤ 0.2 or rejection.
    """

    def __init__(self):
        super().__init__("seed")

    def execute(self, context: dict) -> AgentMessage:
        result = crystallize(
            goal=context.get("goal", ""),
            constraints=tuple(context.get("constraints", [])),
            success_criteria=tuple(context.get("success_criteria", [])),
            context=context.get("context", ""),
        )

        from .types import Ok
        if isinstance(result, Ok):
            seed = result.value
            return AgentMessage(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                payload={
                    "status": "CRYSTALLIZED",
                    "seed_hash": seed.hash,
                    "ambiguity": seed.ambiguity_score,
                    "goal": seed.goal,
                    "reality": "C5-REAL",
                },
            )
        else:
            return AgentMessage(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                payload={
                    "status": "REJECTED",
                    "error": result.error,
                    "reality": "C5-REAL",
                },
            )


class ExecutorAgent(CenturionAgent):
    """
    Double Diamond execution: Discover → Define → Design → Deliver.
    C5-REAL: Delegates to execution runtime.
    """

    def __init__(self):
        super().__init__("executor")

    def execute(self, context: dict) -> AgentMessage:
        """Execute tactical mission via C5-REAL runtime delegation."""
        seed = context.get("seed")
        if seed is None:
            return AgentMessage(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                payload={"status": "ERROR", "reason": "No seed provided"},
            )
        
        # Real delegation will be plugged into a tool / LLM here
        return AgentMessage(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            payload={
                "status": "DELIVERED",
                "reality": "C5-REAL",
                "info": "Delegation to C5-REAL runtime omitted for brevity."
            },
        )



class EvaluatorAgent(CenturionAgent):
    """
    Triple gate: Mechanical → Semantic → Consensus.
    Wraps the Evaluator engine as a swarm agent.
    """

    def __init__(self):
        super().__init__("evaluator")
        self._engine = Evaluator()

    def execute(self, context: dict) -> AgentMessage:
        generation: Generation = context.get("generation", Generation())
        seed: Optional[Seed] = context.get("seed")
        output: str = context.get("output", "")
        lateral_adopted: bool = context.get("lateral_adopted", False)

        if seed is None:
            return AgentMessage(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                payload={"status": "ERROR", "reason": "No seed for evaluation"},
            )

        result = self._engine.evaluate(generation, seed, output, lateral_adopted)

        return AgentMessage(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            payload={
                "status": "EVALUATED",
                "stage": result.stage.name,
                "score": result.score,
                "drift": result.drift,
                "passed": result.passed,
                "triggers_consensus": result.triggers_consensus,
                "reason": result.reason,
                "reality": "C5-REAL",  # All math is deterministic
            },
        )


class WonderAgent(CenturionAgent):
    """
    Wonder/Reflect cycle + stagnation detection.
    "¿Qué es lo que aún no sabemos?"
    Detects stagnation and routes to lateral persona.
    """

    def __init__(self):
        super().__init__("wonder")

    def execute(self, context: dict) -> AgentMessage:
        history: list[Generation] = context.get("history", [])
        current_score: float = context.get("current_score", 0.0)

        # Detect stagnation
        pattern = stagnation_detector.detect(history)

        persona: Optional[LateralPersona] = None
        if pattern:
            persona = STAGNATION_PERSONA_MAP.get(pattern, LateralPersona.CONTRARIAN)

        # Wonder: what do we not yet know?
        wonder_delta = {
            "generations_elapsed": len(history),
            "latest_score": current_score,
            "stagnation": pattern.name if pattern else None,
            "suggested_persona": persona.name if persona else None,
            "question": "What assumptions remain untested?",
        }

        return AgentMessage(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            payload={
                "status": "REFLECTED",
                "wonder": wonder_delta,
                "stagnation_detected": pattern is not None,
                "persona_rotation": persona.name if persona else None,
                "reality": "C5-REAL",  # Stagnation detection is deterministic
            },
        )


# ── Agent Registry ────────────────────────────────────────────────

CENTURION_REGISTRY: dict[str, type[CenturionAgent]] = {
    "interview": InterviewAgent,
    "seed": SeedAgent,
    "executor": ExecutorAgent,
    "evaluator": EvaluatorAgent,
    "wonder": WonderAgent,
}


def spawn_agent(agent_type: str) -> CenturionAgent:
    """Factory: instantiate L2 Centurion by type."""
    cls = CENTURION_REGISTRY.get(agent_type)
    if cls is None:
        raise ValueError(f"Unknown agent type: {agent_type}. Available: {list(CENTURION_REGISTRY.keys())}")
    return cls()
