import sys
import time

# Add root to path
sys.path.append("/Users/borjafernandezangulo/borjamoskv/Cortex-Persist")

from cortex.agentic.agent_stability_governor import AgentStabilityGovernor, AudioFeaturesSample

def test_audio_governor():
    gov = AgentStabilityGovernor()
    gov.DWELL_RED_MIN = 2.0
    print("◈ Testing Audio Governor v2.2...")
    
    # 1. NOMINAL -> YELLOW (True Peak Spike)
    print("\n--- Phase 1: Peak Spike ---")
    sample = AudioFeaturesSample(ts=time.time(), dt=1.0, rms=0.4, true_peak=1.15, crest_factor=10.0, lufs_short=-14.0, high_band_energy=0.2)
    pulse = gov.tick(sample)
    print(f"Mode: {pulse['mode']}, Rule: {pulse['rule']}, Policy: {pulse['policy']['threshold']}dB")
    
    # 2. YELLOW -> RED (Critical Overs)
    print("\n--- Phase 2: Critical Overs (Circuit Breaker) ---")
    sample = AudioFeaturesSample(ts=time.time(), dt=1.0, rms=0.6, true_peak=1.3, crest_factor=4.0, lufs_short=-8.0, high_band_energy=0.5, overs_count=10)
    pulse = gov.tick(sample)
    print(f"Mode: {pulse['mode']}, Rule: {pulse['rule']}, Policy: {pulse['policy']['ceiling']}dB (Safety Active)")
    
    # 3. RED -> YELLOW Recovery
    print("\n--- Phase 3: Cooldown Recovery ---")
    time.sleep(2.1)
    sample = AudioFeaturesSample(ts=time.time(), dt=1.0, rms=0.1, true_peak=0.2, crest_factor=15.0, lufs_short=-24.0, high_band_energy=0.0)
    # Run multiple ticks to allow PID and Dwell to surface
    for _ in range(5):
        pulse = gov.tick(sample)
    print(f"Final Mode: {pulse['mode']}, Rule: {pulse['rule']}")

    print("\n◈ Audio Verification Complete.")

if __name__ == "__main__":
    test_audio_governor()
