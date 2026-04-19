"""
cortex.agentic.planner
======================
Sovereign Intelligence Layer — Layer Ω2
[BRIDGE] This module now acts as a bridge to cortex.sovereign.planificador_soberano.
"""

from typing import List, Dict, Any
from cortex.sovereign.planificador_soberano import PlanificadorSoberano

class CortexPlanner:
    """
    Sovereign Intelligence Module.
    [BRIDGE] Proxies calls to cortex.sovereign.PlanificadorSoberano.
    """

    def __init__(self, model_name: str = "gemini-2.0-flash"):
        self._sovereign = PlanificadorSoberano(nombre_modelo=model_name)

    async def generate_plan(self, prompt: str, history: List[Dict[str, str]] = None) -> Any:
        """
        Execute reasoning cycle via the sovereign core.
        """
        return await self._sovereign.generar_plan(prompt, historial=history)
