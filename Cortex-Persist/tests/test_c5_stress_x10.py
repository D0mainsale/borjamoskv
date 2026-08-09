import asyncio
import time
import pytest
from cortex.sovereign.memoria import AlmacenMemoria

# Mute logger for load test
import logging
logging.getLogger().setLevel(logging.CRITICAL)

async def worker(memoria: AlmacenMemoria, i: int):
    # Escribir hecho y medir latencia individual
    t0 = time.perf_counter()
    memoria.archivar_hecho(
        dominio=f"STRESS_TEST_X10_{i}",
        contenido=f"Payload_Data_Entropy_{i*0.14}",
        exergia=0.9
    )
    t1 = time.perf_counter()
    return (t1 - t0) * 1000 # returns ms

@pytest.mark.asyncio
async def test_c5_stress_latency_x10():
    """
    Law Ω2: Latency under x10 stress must not exceed 12ms (95th percentile).
    Tests the Direct-Silicon JIT FFI layer for binary VSA-SDM writing.
    """
    import tempfile
    db_path = tempfile.mktemp(suffix=".db", prefix="cortex_stress_")
    memoria = AlmacenMemoria(db_path) # Measure JIT WAL writing overhead and GIL with actual file indexing
    
    TOTAL_OPERATIONS = 1000 # Simulating x10 SANS-Agent load spike
    
    t0 = time.perf_counter()
    
    # Launch concurrent writes
    tasks = [worker(memoria, i) for i in range(TOTAL_OPERATIONS)]
    latencies = await asyncio.gather(*tasks)
    
    t1 = time.perf_counter()
    
    total_time_ms = (t1 - t0) * 1000
    
    latencies.sort()
    p95 = latencies[int(TOTAL_OPERATIONS * 0.95)]
    p99 = latencies[int(TOTAL_OPERATIONS * 0.99)]
    avg = sum(latencies) / len(latencies)
    
    print(f"\n[C5-REAL] Stress Test x10 Results:")
    print(f"Total Operations: {TOTAL_OPERATIONS}")
    print(f"Total Time: {total_time_ms:.2f}ms")
    print(f"Avg Latency: {avg:.2f}ms")
    print(f"P95 Latency: {p95:.2f}ms")
    print(f"P99 Latency: {p99:.2f}ms")
    
    # Claim Verification (Roadmap Phase 2)
    assert p95 < 12.0, f"THERMODYNAMIC COLLAPSE: P95 latency is {p95:.2f}ms, exceeds 12.0ms limit."
    
if __name__ == "__main__":
    asyncio.run(test_c5_stress_latency_x10())
