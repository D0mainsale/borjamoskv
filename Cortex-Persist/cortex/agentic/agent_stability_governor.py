"""
cortex.agentic.agent_stability_governor
=======================================
Agents.archi Strategic Governor (v3.0).
[BRIDGE] This module acts as a bridge to cortex.sovereign.gobernador_estabilidad.
"""

from typing import Dict, Any
from cortex.sovereign.gobernador_estabilidad import (
    GobernadorEstabilidadAgente,
    MuestraSeñalSoberana
)


class SovereignSignalSample:
    """Specialized telemetry for Strategic Control (v3.0)."""

    def __init__(
        self, ts: float, dt: float, exergy: float, entropy: float,
        risk: float, impact: float, sample_id: str = "s0p_pulse"
    ):
        self._sovereign = MuestraSeñalSoberana(
            ts=ts, dt=dt, exergia=exergy, entropia=entropy,
            riesgo=risk, impacto=impact, id_muestra=sample_id
        )

    @property
    def ts(self):
        """Returns the sample timestamp."""
        return self._sovereign.ts

    @property
    def dt(self):
        """Returns the delta time between samples."""
        return self._sovereign.dt

    @property
    def exergy(self):
        """Returns the quality of useful work signal."""
        return self._sovereign.exergia

    @property
    def entropy(self):
        """Returns the data noise/chaos signal."""
        return self._sovereign.entropia

    @property
    def risk(self):
        """Returns the probability of detection or failure."""
        return self._sovereign.riesgo

    @property
    def impact(self):
        """Returns the strategic alcance signal."""
        return self._sovereign.impacto

    @property
    def sample_id(self):
        """Returns the unique sample identifier."""
        return self._sovereign.id_muestra


class AgentStabilityGovernor:
    """
    Agents.archi Strategic Governor (v3.0).
    [BRIDGE] Proxies calls to cortex.sovereign.GobernadorEstabilidadAgente.
    """

    def __init__(self):
        self._sovereign = GobernadorEstabilidadAgente()

    def tick(self, sample: SovereignSignalSample) -> Dict[str, Any]:
        """Governor iteration via the sovereign core."""
        return self._sovereign.procesar(sample._sovereign)
