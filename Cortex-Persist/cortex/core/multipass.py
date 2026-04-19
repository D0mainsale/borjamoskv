"""
Ouroboros Multipass Loop — Autonomous Execute → Verify → Retry.
Zero human intervention between iterations.

Law Ω2: O(n) on generation count, not O(n²).
Law Ω9: C5-REAL. Every iteration is EventStore-persisted.

Loop invariant:
  for each generation:
    hooks.emit(pre_tool_use)
    output = executor(seed, generation)
    hooks.emit(post_tool_use)
    result = evaluator.evaluate(...)
    if result.passed → CONVERGED
    if stagnation → rotate persona → if still stuck → ABORT
    else → continue
"""
from __future__ import annotations

import itertools
import uuid
import ctypes
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional, Protocol

# ── C5-REAL Flight Recorder FFI Bindings ─────────────────────────────
_JIT_LIB = None
try:
    _dylib_path = os.path.join(os.path.dirname(__file__), "cortex_jit/target/release/libcortex_jit.dylib")
    if os.path.exists(_dylib_path):
        _JIT_LIB = ctypes.CDLL(_dylib_path)
        _JIT_LIB.flight_recorder_append_rust.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        _JIT_LIB.flight_recorder_append_rust.restype = ctypes.c_bool
    else:
        _so_path = os.path.join(os.path.dirname(__file__), "cortex_jit/target/release/libcortex_jit.so")
        if os.path.exists(_so_path):
            _JIT_LIB = ctypes.CDLL(_so_path)
            _JIT_LIB.flight_recorder_append_rust.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
            _JIT_LIB.flight_recorder_append_rust.restype = ctypes.c_bool
except Exception:
    pass

def _append_flight_recorder(session_id: str, step: str, payload: str):
    if _JIT_LIB:
        _JIT_LIB.flight_recorder_append_rust(
            session_id.encode('utf-8'),
            step.encode('utf-8'),
            payload.encode('utf-8')
        )


from cortex.ouroboros.types import (
    Event,
    Generation,
    EvolutionAction,
    StagnationPattern,
    LateralPersona,
    STAGNATION_PERSONA_MAP,
    CONVERGENCE_THRESHOLD,
    MAX_GENERATIONS,
    hash_content,
)
from cortex.ouroboros.evaluator import Evaluator, EvalResult
from cortex.ouroboros.seed import Seed
from cortex.ouroboros import stagnation as stagnation_detector
from cortex.ouroboros.autodidact_evolver import EpistemicEvolver


# ── Hook Protocol (minimal interface) ──────────────────────────────

class HookEmitter(Protocol):
    """Minimal protocol for hook emission. Avoids circular import."""
    def emit(self, event) -> object: ...


class _NullHooks:
    """No-op hook emitter for when hooks aren't provided."""
    def emit(self, event) -> None:
        return None


# ── Hook event factory ─────────────────────────────────────────────

def _make_hook_event(event_type: str, payload: dict, session_id: str):
    """Create a hook event dict. Avoids importing HookEvent directly."""
    return type("HookEvent", (), {
        "type": event_type,
        "payload": payload,
        "session_id": session_id,
        "id": uuid.uuid4().hex[:12],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })()


# ── Executor Protocol ─────────────────────────────────────────────

class Executor(Protocol):
    """
    Pluggable executor interface.
    Takes a seed + generation context, returns output string.
    """
    def __call__(self, seed: Seed, generation_number: int) -> str: ...


# ── Result ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MultipassResult:
    """Terminal outcome of the multipass loop."""
    converged: bool
    generations_run: int
    final_score: float
    final_output: str
    action: EvolutionAction
    stagnation_pattern: Optional[StagnationPattern] = None
    persona_rotations: int = 0
    session_id: str = ""


# ── Configuration ──────────────────────────────────────────────────

@dataclass
class MultipassConfig:
    """Tunable loop parameters."""
    max_retries: int = MAX_GENERATIONS
    pass_threshold: float = CONVERGENCE_THRESHOLD
    max_persona_rotations: int = 2
    record_events: bool = True


# ── Runner ─────────────────────────────────────────────────────────

class MultipassEngine:
    """
    Autonomous retry engine.
    Integrates: Evaluator + Stagnation Detector + Hooks + EventStore.
    """

    def __init__(
        self,
        evaluator: Optional[Evaluator] = None,
        hooks: Optional[HookEmitter] = None,
        event_store=None,
        config: Optional[MultipassConfig] = None,
    ):
        self.evaluator = evaluator or Evaluator()
        self.hooks = hooks or _NullHooks()
        self.config = config or MultipassConfig()
        self.evolver = EpistemicEvolver()

    def run(
        self,
        seed: Seed,
        executor: Callable[[Seed, int], str],
    ) -> MultipassResult:
        """
        Execute the multipass loop.
        Returns when converged, stagnated, or max retries exhausted.
        """
        session_id = uuid.uuid4().hex[:16]
        history: list[Generation] = []
        persona_rotations = 0
        current_persona: Optional[LateralPersona] = None
        final_output = ""
        final_score = 0.0
        previous_output_hash = "GENESIS_BLOCK"

        for gen_num in range(self.config.max_retries):
            # ── Pre-execution hook ────────────────────────────
            pre_result = self.hooks.emit(_make_hook_event(
                "pre_tool_use",
                {
                    "tool_name": "multipass_executor",
                    "args": {"generation": gen_num, "seed_hash": seed.hash},
                    "session_id": session_id,
                },
                session_id,
            ))

            # Check for ABORT from hooks
            if hasattr(pre_result, "action") and hasattr(pre_result.action, "name"):
                if pre_result.action.name == "ABORT":
                    return MultipassResult(
                        converged=False,
                        generations_run=gen_num,
                        final_score=final_score,
                        final_output=final_output,
                        action=EvolutionAction.ABORTED,
                        session_id=session_id,
                    )

            # ── C5-REAL Flight Recorder Checkpoint ────────────
            _append_flight_recorder(session_id, "PRE_EXEC_SEED", seed.hash)

            # ── Execute ───────────────────────────────────────

            try:
                output = executor(seed, gen_num)
            except Exception as exc:
                output = f"EXECUTOR_ERROR: {exc}"
                
                # [OpenSpace: AUTO-FIX] Try to structurally mutate and repair the skill AST
                fix_applied = self.evolver.evaluate_and_mutate(seed.hash, str(exc))
                if not fix_applied:
                    # Could not apply fix or exceeded max recursion; output stays the error string
                    pass

            final_output = output
            
            # [Ω5/FlightRecorder] Chain of Decision hash. Linking previous iteration hash with the current operation.
            current_raw_hash = hash_content(output)
            output_hash = hash_content(f"{previous_output_hash}:{current_raw_hash}:{seed.hash}")
            previous_output_hash = output_hash

            # ── C5-REAL Flight Recorder Checkpoint ────────────
            _append_flight_recorder(session_id, "POST_EXEC_HASH", output_hash)

            # ── Post-execution hook ───────────────────────────
            self.hooks.emit(_make_hook_event(
                "post_tool_use",
                {
                    "tool_name": "multipass_executor",
                    "result_length": len(output),
                    "generation": gen_num,
                    "session_id": session_id,
                },
                session_id,
            ))

            # ── Evaluate ──────────────────────────────────────
            generation = Generation(
                number=gen_num,
                seed_hash=seed.hash,
                output_hash=output_hash,
                persona=current_persona,
            )

            # Pre-eval hook
            self.hooks.emit(_make_hook_event(
                "pre_eval",
                {"generation": gen_num, "seed_hash": seed.hash},
                session_id,
            ))

            eval_result = self.evaluator.evaluate(
                generation=generation,
                seed=seed,
                output=output,
                lateral_adopted=current_persona is not None,
            )

            final_score = eval_result.score

            # Update generation with eval results
            generation = Generation(
                id=generation.id,
                number=gen_num,
                seed_hash=seed.hash,
                eval_score=eval_result.score,
                drift=eval_result.drift,
                output_hash=output_hash,
                action=(
                    EvolutionAction.CONVERGED
                    if eval_result.passed
                    else EvolutionAction.CONTINUE
                ),
                persona=current_persona,
            )

            history.append(generation)

            # Post-eval hook
            self.hooks.emit(_make_hook_event(
                "post_eval",
                {
                    "generation": gen_num,
                    "score": eval_result.score,
                    "drift": eval_result.drift,
                    "passed": eval_result.passed,
                    "stage": eval_result.stage.name,
                },
                session_id,
            ))

            # ── Persist IPC (Falsation Engine Core) ───────────
            if self.config.record_events:
                self._record_generation(session_id, generation, eval_result)

            # ── Convergence check ─────────────────────────────
            if eval_result.passed:
                # [OpenSpace: AUTO-LEARN] If we struggled but eventually converged, crystallize the structural path.
                if persona_rotations > 0:
                    self.evolver.execute_post_mortem(session_id, history)
                
                return MultipassResult(
                    converged=True,
                    generations_run=gen_num + 1,
                    final_score=final_score,
                    final_output=final_output,
                    action=EvolutionAction.CONVERGED,
                    persona_rotations=persona_rotations,
                    session_id=session_id,
                )

            # ── Stagnation detection ──────────────────────────
            pattern = stagnation_detector.detect(history)

            if pattern is not None:
                # [Ω4] Rotate persona unconditionally (Infinite Ouroboros)
                current_persona = STAGNATION_PERSONA_MAP.get(
                    pattern, LateralPersona.CONTRARIAN
                )
                persona_rotations += 1

        # Max retries exhausted
        return MultipassResult(
            converged=False,
            generations_run=self.config.max_retries,
            final_score=final_score,
            final_output=final_output,
            action=EvolutionAction.ABORTED,
            persona_rotations=persona_rotations,
            session_id=session_id,
        )

    # ── EventStore Recording ──────────────────────────────────

    def _record_generation(
        self,
        session_id: str,
        generation: Generation,
        eval_result: EvalResult,
    ) -> None:
        """Dispara la firma al Nucleo de Seguridad Hardware (IPC/Subprocess) en lugar de un EventStore C4."""
        import sys
        import json
        payload = {
            "session_id": session_id,
            "id": generation.id,
            "number": generation.number,
            "seed_hash": generation.seed_hash,
            "output_hash": generation.output_hash,
            "action": generation.action.name,
        }
        # Mandato Ω5: By-pass del runtime de Python. Salida binaria standard para consumo de FFI/Rust.
        sys.stdout.write(f"CORTEX_FALSATION_PAYLOAD::{json.dumps(payload)}\n")
        sys.stdout.flush()
