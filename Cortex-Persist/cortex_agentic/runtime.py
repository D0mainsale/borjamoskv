"""
cortex_agentic.runtime
======================
Sovereign Orchestration Engine — Layer Ω1

Governs the multi-step lifecycle of a CORTEX Agentic Run.
Implements the 8-step execution pattern with strict state monitoring.

Confidence: C5-Static
"""

from __future__ import annotations

import time
import uuid
import json
import asyncio
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from .planner import CortexPlanner
from .tool_registry import ToolRegistry
from .memory import MemoryStore
from .persist_membrane import PersistMembrane, FactProposal

# ─── Execution States ─────────────────────────────────────────────────────────

class RunStatus(Enum):
    INITIALIZING = auto()
    PLANNING     = auto()
    EXECUTING    = auto()
    REFLECTING   = auto()
    WAITING_APP  = auto()
    COMPLETING   = auto()
    SUCCESS      = auto()
    FAILED       = auto()

@dataclass
class RunStep:
    name: str
    status: RunStatus
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

# ─── Runtime Core ─────────────────────────────────────────────────────────────

class CortexRuntime:
    """
    Sovereign Execution Runtime.
    Coordinates between Planner (Reasoning), ToolRegistry (Action), and Memory (State).
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.status = RunStatus.INITIALIZING
        self.history: List[RunStep] = []
        
        # Core components
        self.planner  = CortexPlanner()
        self.tools    = ToolRegistry()
        self.memory   = MemoryStore()
        self.membrane = PersistMembrane()  # Ω-PERSIST: write-path membrane
        
        self._add_step("INITIALIZING", RunStatus.INITIALIZING)

    def _add_step(self, name: str, status: RunStatus, meta: Optional[Dict[str, Any]] = None):
        step = RunStep(name=name, status=status, metadata=meta or {})
        self.history.append(step)
        self.status = status
        
        # Persist run state in memory
        self.memory.record_run(
            self.session_id, 
            status.name, 
            [{"name": s.name, "status": s.status.name, "meta": s.metadata} for s in self.history]
        )
        print(f"◈ [RUNTIME] {self.session_id[:8]} | {name} -> {status.name}")

    async def execute_task(self, prompt: str) -> Dict[str, Any]:
        """
        Primary entry point for a sovereign agentic run.
        """
        try:
            # Add user message to memory
            self.memory.add_message(self.session_id, "user", prompt)

            # 1. Retrieve live sealed context from CORTEX Persist before planning
            persist_context = await self.membrane.search_context(
                query=prompt, limit=5
            )
            context_hint = ""
            if persist_context:
                context_hint = "\n\n[PERSIST_CONTEXT]\n" + json.dumps(persist_context, ensure_ascii=False)

            # 2. Planning (with persist-grounded context)
            self._add_step("PLANNING", RunStatus.PLANNING, {"prompt_len": len(prompt)})
            history = self.memory.get_history(self.session_id)
            plan_response = await self.planner.generate_plan(prompt + context_hint, history=history)

            # 3. Guard — dry-run trust check on the LLM output before sealing
            proposal = FactProposal(
                subject=f"session:{self.session_id}",
                predicate="plan_generated",
                object_val={"prompt": prompt[:200], "response_len": len(plan_response)},
                source="llm",
                session_id=self.session_id,
            )
            guard = await self.membrane.guard_write(proposal)
            if not guard.passed:
                self._add_step("GUARD_BLOCK", RunStatus.FAILED, {"reasons": guard.reasons})
                return {"session_id": self.session_id, "status": "blocked", "reasons": guard.reasons}

            # 4. Commit the plan as a sealed fact
            commit = await self.membrane.commit_fact(proposal, {"response": plan_response[:500]})
            self._add_step("PERSIST_COMMITTED", RunStatus.REFLECTING, {
                "fact_id": commit.fact_id, "persist_status": commit.status
            })

            # 5. Add AI response to local memory
            self.memory.add_message(self.session_id, "assistant", plan_response)

            # 6. Reflect / Success + post-action verify
            self._add_step("SUCCESS", RunStatus.SUCCESS, {"response_len": len(plan_response)})
            verify = await self.membrane.verify_fact(commit.fact_id)

            return {
                "session_id": self.session_id,
                "status": "success",
                "response": plan_response,
                "steps": len(self.history),
                "persist": {
                    "fact_id":  commit.fact_id,
                    "hash":     commit.hash,
                    "verified": verify.get("verified", False),
                    "mode":     commit.status,
                },
            }

        except Exception as e:
            self._add_step("ERROR", RunStatus.FAILED, {"error": str(e)})
            # Commit the failure itself — a lie recorded cryptographically is still a lie, but it's auditable
            try:
                fail_proposal = FactProposal(
                    subject=f"session:{self.session_id}",
                    predicate="execution_error",
                    object_val={"error": str(e)[:300]},
                    source="llm",
                    session_id=self.session_id,
                )
                await self.membrane.commit_fact(fail_proposal)
            except Exception:
                pass  # membrane failure must never suppress the original error
            return {
                "session_id": self.session_id,
                "status": "error",
                "error": str(e)
            }

if __name__ == "__main__":
    # Smoke test (requires GOOGLE_API_KEY)
    import asyncio
    rt = CortexRuntime()
    # asyncio.run(rt.execute_task("Audit system exergy"))
