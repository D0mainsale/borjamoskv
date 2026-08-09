"""
Regression tests for existence-gap remediation across Cortex-Persist modules.
Verifies that all reexported symbols, adapters, and native engines resolve cleanly.
"""

import pytest
import time
from cortex.sovereign import guard_and_commit_sync, custodiar_y_sellar_sync
from cortex.sovereign.cronos import DemonioCronos
from cortex.server.main import run_server
from cortex.engine.legion import LegionOmegaEngine, SiegeResult
from cortex.engine.legion_vectors import RED_TEAM_SWARM
from cortex.agentic.agent_stability_governor import (
    AgentStabilityGovernor,
    TelemetrySample,
    AudioFeaturesSample,
)


def test_sovereign_security_control_symbol_reexported_from_package_init():
    assert callable(guard_and_commit_sync)
    assert guard_and_commit_sync is custodiar_y_sellar_sync


def test_cronos_demon_initializes_with_qualified_memory_import():
    cronos = DemonioCronos()
    assert cronos.memoria is not None
    assert cronos.running is True


def test_legion_omega_engine_executes_siege_cycle_natively():
    engine = LegionOmegaEngine(max_cycles=2)
    context = {
        "target_url": "https://api.v2.stellar.network/v1",
        "vector_priority": ["BOLA"],
    }
    
    import asyncio
    result = asyncio.run(engine.forge("Test intent", context))
    
    assert isinstance(result, SiegeResult)
    assert result.success is True
    assert result.cycles == 2
    assert len(result.vulnerabilities) > 0


def test_telemetry_sample_adapter_calculates_governor_exergy_and_risk():
    sample = TelemetrySample(ts=time.time(), dt=1.0, r=0.9, h=0.2, d=0.1, p=0.5)
    assert sample.risk == 0.9
    assert sample.entropy == 0.2
    assert sample.exergy == pytest.approx(0.9)
    assert sample.impact == 0.5


def test_audio_features_sample_adapter_triggers_audio_governor_policy():
    gov = AgentStabilityGovernor()
    gov.DWELL_RED_MIN = 0.1
    
    sample = AudioFeaturesSample(
        ts=time.time(),
        dt=1.0,
        rms=0.4,
        true_peak=1.2,
        crest_factor=8.0,
        lufs_short=-14.0,
        high_band_energy=0.3,
        overs_count=5,
    )
    
    pulse = gov.tick(sample)
    assert pulse["mode"] == "ROJO"
    assert "policy" in pulse
    assert "ceiling" in pulse["policy"]
    assert "threshold" in pulse["policy"]
