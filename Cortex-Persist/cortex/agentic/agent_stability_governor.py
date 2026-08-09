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


class TelemetrySample(SovereignSignalSample):
    """Telemetry sample adapter for Governor v2.1 (r, h, d, p format)."""

    def __init__(
        self,
        ts: float,
        dt: float,
        r: float = 0.0,
        h: float = 0.0,
        d: float = 0.0,
        p: float = 0.0,
        sample_id: str = "telemetry_pulse",
    ):
        self.r = r
        self.h = h
        self.d = d
        self.p = p
        super().__init__(
            ts=ts,
            dt=dt,
            exergy=max(0.0, 1.0 - d),
            entropy=h,
            risk=r,
            impact=p,
            sample_id=sample_id,
        )


class AudioFeaturesSample(SovereignSignalSample):
    """Audio DSP telemetry sample adapter for Audio Governor v2.2."""

    def __init__(
        self,
        ts: float,
        dt: float,
        rms: float = 0.0,
        true_peak: float = 0.0,
        crest_factor: float = 0.0,
        lufs_short: float = -24.0,
        high_band_energy: float = 0.0,
        overs_count: int = 0,
        sample_id: str = "audio_pulse",
    ):
        self.rms = rms
        self.true_peak = true_peak
        self.crest_factor = crest_factor
        self.lufs_short = lufs_short
        self.high_band_energy = high_band_energy
        self.overs_count = overs_count

        risk = min(1.0, max(0.0, (true_peak - 1.0) * 2.0) + (overs_count * 0.05))
        entropy = min(1.0, high_band_energy + (1.0 if true_peak > 1.0 else 0.0))
        exergy = max(0.0, 1.0 - risk)
        impact = min(1.0, max(0.0, (lufs_short + 24.0) / 24.0))

        super().__init__(
            ts=ts,
            dt=dt,
            exergy=exergy,
            entropy=entropy,
            risk=risk,
            impact=impact,
            sample_id=sample_id,
        )


class AgentStabilityGovernor:
    """
    Agents.archi Strategic Governor (v3.0).
    [BRIDGE] Proxies calls to cortex.sovereign.GobernadorEstabilidadAgente.
    """

    def __init__(self):
        self._sovereign = GobernadorEstabilidadAgente()

    @property
    def DWELL_RED_MIN(self) -> float:
        return self._sovereign.PERMANENCIA_ROJO_MIN

    @DWELL_RED_MIN.setter
    def DWELL_RED_MIN(self, value: float):
        self._sovereign.PERMANENCIA_ROJO_MIN = value

    @property
    def DWELL_YELLOW_MIN(self) -> float:
        return self._sovereign.PERMANENCIA_AMARILLO_MIN

    @DWELL_YELLOW_MIN.setter
    def DWELL_YELLOW_MIN(self, value: float):
        self._sovereign.PERMANENCIA_AMARILLO_MIN = value

    def tick(self, sample: SovereignSignalSample) -> Dict[str, Any]:
        """Governor iteration via the sovereign core."""
        res = self._sovereign.procesar(sample._sovereign)
        # Augment policy dictionary with audio threshold/ceiling keys expected by v2.2 callers
        mode = res.get("mode", "VERDE")
        policy = res.get("policy", {})
        if mode == "ROJO":
            policy.setdefault("ceiling", -6.0)
            policy.setdefault("threshold", -12.0)
        elif mode == "AMARILLO":
            policy.setdefault("threshold", -3.0)
            policy.setdefault("ceiling", -1.0)
        else:
            policy.setdefault("threshold", 0.0)
            policy.setdefault("ceiling", 0.0)
        return res

