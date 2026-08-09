import sys
import time

# Add root to path
# scratch scripts run from repo root: python -m scratch.verify_audio_v2_2

from cortex.agentic.agent_stability_governor import AgentStabilityGovernor, SovereignSignalSample

def test_audio_governor():
    gov = AgentStabilityGovernor()
    gov.DWELL_RED_MIN = 2.0
    print("◈ Testing Audio Governor v2.2...")
    
    # 1. NOMINAL -> YELLOW (True Peak Spike)
    print("\n--- Phase 1: Peak Spike ---")
    sample = SovereignSignalSample(ts=time.time(), dt=1.0, exergy=0.4, entropy=1.15, risk=10.0, impact=-14.0)
    pulse = gov.tick(sample)
    print(f"Mode: {pulse['mode']}, Rule: {pulse['rule']}, Policy: {pulse['policy']['threshold']}dB")
    
    # 2. YELLOW -> RED (Critical Overs)
    print("\n--- Phase 2: Critical Overs (Circuit Breaker) ---")
    sample = SovereignSignalSample(ts=time.time(), dt=1.0, exergy=0.6, entropy=1.3, risk=4.0, impact=-8.0)
    pulse = gov.tick(sample)
    print(f"Mode: {pulse['mode']}, Rule: {pulse['rule']}, Policy: {pulse['policy']['ceiling']}dB (Safety Active)")
    
    # 3. RED -> YELLOW Recovery
    print("\n--- Phase 3: Cooldown Recovery ---")
    time.sleep(2.1)
    sample = SovereignSignalSample(ts=time.time(), dt=1.0, exergy=0.1, entropy=0.2, risk=15.0, impact=-24.0)
    # Run multiple ticks to allow PID and Dwell to surface
    for _ in range(5):
        pulse = gov.tick(sample)
    print(f"Final Mode: {pulse['mode']}, Rule: {pulse['rule']}")

    print("\n◈ Audio Verification Complete.")

if __name__ == "__main__":
    test_audio_governor()
