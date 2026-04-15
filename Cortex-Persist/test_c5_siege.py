"""
C5-REAL Siege test for Autodidact-Omega (AUTO-FIX vector)
Inyecta un error lógico determinista en el ejecutor para forzar al Evolver a interceptar el error y mutar el "AST".
"""
import logging

from cortex_ouroboros.seed import Seed
from cortex_core.multipass import MultipassEngine, MultipassConfig

logging.basicConfig(level=logging.INFO, format="%(message)s")

# Seed sintético
seed = Seed(hash="SED_ASDO_9901", content="Init OpenSpace Protocol")

# Inyección entrópica premeditada: El ejecutor colapsa automáticamente
def failing_executor(seed: Seed, generation: int) -> str:
    logging.info(f"[*] Ejecutor intentando procesar gen {generation}...")
    raise SyntaxError("C5_INJECTED_FAULT: IndentationError in skill 'dummy_skill' at line 42")

def run_siege():
    # Loop ajustado a 3 intentos máximo
    config = MultipassConfig(max_retries=3, record_events=False) 
    engine = MultipassEngine(config=config)
    
    print("==================================================")
    print(" INICIANDO ASEDIO C5 (Vector AUTO-FIX OpenSpace)  ")
    print("==================================================")
    
    result = engine.run(seed, failing_executor)
    
    print("==================================================")
    print(f"Resultado Final:")
    print(f" - Fallo contenido (No crashea el loop general): {not result.converged}")
    print(f" - Iteraciones de sangrado térmico: {result.generations_run}/{config.max_retries}")
    print("==================================================")
    
if __name__ == "__main__":
    run_siege()
