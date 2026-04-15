"""
Archived C4-SIMULACIÓN mock agents from cortex_ouroboros/agents.py
"""
import uuid
from typing import Optional

def hash_content(s: str) -> str:
    from hashlib import sha256
    return sha256(s.encode()).hexdigest()

class MockExecutorAgent:
    """
    Archived Double Diamond execution logic that generated synthetic strings.
    """
    def _execute_internal(self, context: dict) -> dict:
        seed = context.get("seed")
        generation_number: int = context.get("generation_number", 0)
        persona = context.get("persona")

        if seed is None:
            return {"status": "ERROR", "reason": "No seed provided"}

        # C4-SIMULACIÓN: synthetic output evolving with generation
        output_lines = [
            f"# Generation {generation_number} Output",
            f"## Goal: {seed.goal}",
        ]
        for i, c in enumerate(seed.constraints):
            output_lines.append(f"### Constraint {i+1}: {c}")
        for i, s in enumerate(seed.success_criteria):
            output_lines.append(f"### Criteria {i+1}: {s}")

        if persona:
            output_lines.append(f"## Lateral Approach: {persona.name}")

        output = "\n".join(output_lines)

        return {
            "status": "DELIVERED",
            "output": output,
            "output_hash": hash_content(output),
            "generation": generation_number,
            "persona": persona.name if persona else None,
            "reality": "C4-SIMULACIÓN",
        }
