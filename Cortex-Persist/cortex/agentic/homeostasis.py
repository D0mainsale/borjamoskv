"""
cortex.agentic.homeostasis
==========================
Sovereign PID-based Dimensionality Governor (DDG).
[BRIDGE] This module now acts as a bridge to cortex.sovereign.gobernador_homeostasis.
"""

from typing import Dict, Any
from cortex.sovereign.gobernador_homeostasis import GobernadorDimensional

class DimensionalityGovernor:
    """
    Sovereign Controller for Agentic Homeostasis.
    [BRIDGE] Proxies calls to cortex.sovereign.GobernadorDimensional.
    """
    def __init__(self, kp=0.8, ki=0.05, kd=0.3):
        self._sovereign = GobernadorDimensional(kp=kp, ki=ki, kd=kd)

    def tick(self, measured_entropy: float, dt: float = 1.0) -> Dict[str, Any]:
        """
        Execute one controller cycle via the sovereign core.
        """
        return self._sovereign.procesar(measured_entropy, dt)

    def set_target(self, target: float):
        self._sovereign.definir_objetivo(target)

    def update_params(self, kp: float = None, ki: float = None, kd: float = None):
        self._sovereign.actualizar_parametros(kp=kp, ki=ki, kd=kd)
