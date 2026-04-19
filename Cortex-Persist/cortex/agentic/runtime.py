"""
cortex.agentic.runtime
======================
Sovereign Orchestration Engine — Layer Ω1
[BRIDGE] This module acts as a bridge to cortex.sovereign.entorno_ejecucion.
"""

from typing import Dict, Any, Optional
from cortex.sovereign.entorno_ejecucion import (
    EntornoEjecucionSoberano
)


class CortexRuntime:
    """
    Sovereign Execution Runtime.
    [BRIDGE] Proxies to cortex.sovereign.EntornoEjecucionSoberano.
    """

    def __init__(self, session_id: Optional[str] = None):
        self._sovereign = EntornoEjecucionSoberano(id_sesion=session_id)

    @property
    def session_id(self):
        """Returns the unique session identifier."""
        return self._sovereign.id_sesion

    @property
    def status(self):
        """Returns the current execution state name."""
        return self._sovereign.estado.name

    @property
    def history(self):
        """Returns the execution step history."""
        return self._sovereign.historial

    async def execute_task(self, prompt: str) -> Dict[str, Any]:
        """
        Execute task via the sovereign core.
        """
        return await self._sovereign.ejecutar_tarea(prompt)
