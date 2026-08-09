"""
C5-REAL Siege test for Autodidact-Omega (AUTO-FIX vector)
Inyecta un error lógico determinista en el ejecutor para forzar al Evolver a interceptar el error y mutar el "AST".
"""
import logging

from cortex.ouroboros.seed import Seed
from cortex.core.multipass import MultipassEngine, MultipassConfig

logging.basicConfig(level=logging.INFO, format="%(message)s")

# Seed sintético
seed = Seed(goal="Init OpenSpace Protocol", context="SED_ASDO_9901")

# Inyección entrópica premeditada: El ejecutor colapsa automáticamente
def failing_executor(seed: Seed, generation: int) -> str:
    logging.info(f"[*] Ejecutor intentando procesar gen {generation}...")
    raise SyntaxError("C5_INJECTED_FAULT: IndentationError in skill 'dummy_skill' at line 42")

def test_c5_siege_contains_injected_executor_fault():
    config = MultipassConfig(max_retries=3, record_events=False)
    engine = MultipassEngine(config=config)
    result = engine.run(seed, failing_executor)
    assert not result.converged
    assert result.generations_run == config.max_retries


if __name__ == "__main__":
    test_c5_siege_contains_injected_executor_fault()
