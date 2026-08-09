import sys
import time

# Add root to path
# scratch scripts run from repo root: python -m scratch.verify_v2_1

from cortex.agentic.agent_stability_governor import AgentStabilityGovernor, SovereignSignalSample

def test_governor():
    gov = AgentStabilityGovernor()
    gov.DWELL_RED_MIN = 1.0
    gov.DWELL_YELLOW_MIN = 1.0
    print("◈ Testing Governor v2.1 Detailed Transitions...")
    
    # 1. Stress -> RED
    print("\n--- Stressing to RED ---")
    for _ in range(10):
        sample = SovereignSignalSample(ts=time.time(), dt=1.0, exergy=0.9, entropy=0.9, risk=0.9, impact=0.9)
        pulse = gov.tick(sample)
    print(f"Current Mode: {pulse['mode']}, u: {pulse['u']:.2f}")

    # 2. Recovery -> YELLOW
    print("\n--- Recovering to YELLOW ---")
    time.sleep(1.1)
    for i in range(15):
        sample = SovereignSignalSample(ts=time.time(), dt=1.0, exergy=0.01, entropy=0.01, risk=0.01, impact=0.01) # e ~ 0.01
        pulse = gov.tick(sample)
        if i % 3 == 0: print(f"Step {i+1}: u={pulse['u']:.2f}, mode={pulse['mode']}, rule={pulse['rule']}")
    
    print(f"Final Mode: {pulse['mode']}, u: {pulse['u']:.2f}")

if __name__ == "__main__":
    test_governor()
