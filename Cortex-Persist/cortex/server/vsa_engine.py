import random
import time
import os
import hashlib
from typing import List, Dict, Any, Optional


class SovereignHypervector:
    """
    Law Ω0: Direct-Silicon Hypervector Emulation.
    Dimension: 10,000 bits.
    """
    DIM = 10000

    def __init__(self, data: Optional[List[int]] = None):
        if data is not None:
            self.data = data
        else:
            # Neutral identity for XOR binding is all zeros,
            # but for bundling we use random binary vectors.
            bits = [random.randint(0, 1) for _ in range(self.DIM)]
            self.data = bits

    @classmethod
    def from_seed(cls, seed_str: str):
        """Deterministic seed-based generation for consistent IDs"""
        state = random.getstate()
        random.seed(seed_str)
        vec = [random.randint(0, 1) for _ in range(cls.DIM)]
        random.setstate(state)  # Restore global state
        return cls(vec)

    def bind(self, other: 'SovereignHypervector') -> 'SovereignHypervector':
        """XOR Binding: v1 ^ v2. Reversible and distance-preserving."""
        new_data = [self.data[i] ^ other.data[i] for i in range(self.DIM)]
        return SovereignHypervector(new_data)

    def bundle(
        self, others: List['SovereignHypervector']
    ) -> 'SovereignHypervector':
        """Majority Vote Bundling: Superposition of state."""
        new_data = []
        all_vecs = [self.data] + [o.data for o in others]
        num_vecs = len(all_vecs)

        for i in range(self.DIM):
            count = sum(vec[i] for vec in all_vecs)
            # Threshold: 1 if count > half, else 0 (with random tie-break)
            if count > num_vecs / 2:
                new_data.append(1)
            elif count < num_vecs / 2:
                new_data.append(0)
            else:
                new_data.append(random.randint(0, 1))

        return SovereignHypervector(new_data)

    def hamming_distance(self, other: 'SovereignHypervector') -> float:
        """Hamming distance: 0.0 to 1.0 (binary VSA)"""
        diff = sum(self.data[i] ^ other.data[i] for i in range(self.DIM))
        return diff / self.DIM


class MemoryConsolidator:
    """
    Law Ω1: Epistemic Breaker (Memory Substrate).
    Consolidates transient agent logs into a crystallized VSA state.
    """
    def __init__(self, storage_path: str = "sovereign_memory.bin"):
        self.storage_path = storage_path
        self.state_tensor = SovereignHypervector()  # Initial state
        self.fact_count = 0
        h_val = hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]
        self.tensor_id = f"0x{h_val.upper()}"
        self.load()

    def load(self):
        """Restore hyperdimensional state from disk if available"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "rb") as f:
                    p_bytes = f.read()
                    val = int.from_bytes(p_bytes, 'big')
                    b_str = bin(val)[2:].zfill(SovereignHypervector.DIM)
                    # Convert back to list of ints
                    v_dim = SovereignHypervector.DIM
                    self.state_tensor.data = [int(b) for b in b_str[-v_dim:]]

                    # Regenerate ID
                    bits = "".join(map(str, self.state_tensor.data)).encode()
                    h_val = hashlib.sha256(bits).hexdigest()[:8]
                    self.tensor_id = f"0x{h_val.upper()}"
                    print(f"◈ VSA_CORE: State restored. ID={self.tensor_id}")
            except Exception as e:
                print(f"◈ VSA_CORE_ERROR: Fail to load state: {e}")

    def crystallize_facts(self, facts: List[Dict[str, Any]]) -> str:
        """Algebraic Collapse: Binds each fact and bundles into main state."""
        if not facts:
            return self.tensor_id

        fact_vectors = []
        for fact in facts:
            # Bind (Key ^ Value)
            k_seed = f"KEY_{fact.get('dominio', 'GENERIC')}"
            v_seed = f"VAL_{fact.get('contenido', '')}"
            key_vec = SovereignHypervector.from_seed(k_seed)
            val_vec = SovereignHypervector.from_seed(v_seed)
            fact_vectors.append(key_vec.bind(val_vec))

        # Superpose all new facts into the current state
        self.state_tensor = self.state_tensor.bundle(fact_vectors)
        self.fact_count += len(facts)

        # New Tensor ID
        bits = "".join(map(str, self.state_tensor.data)).encode()
        h_val = hashlib.sha256(bits).hexdigest()[:8]
        self.tensor_id = f"0x{h_val.upper()}"
        self.save()
        return self.tensor_id

    def save(self):
        """Binary persistence of the hyperdimensional state"""
        with open(self.storage_path, "wb") as f:
            # Flatten to bytes for O(1) I/O
            packed = int("".join(map(str, self.state_tensor.data)), 2)
            f_bytes = (SovereignHypervector.DIM + 7) // 8
            f.write(packed.to_bytes(f_bytes, 'big'))

    def data_as_bytes(self):
        return "".join(map(str, self.state_tensor.data)).encode()


if __name__ == "__main__":
    # Test suite for VSA Engine
    print("◈ VSA_CORE: Inciando Autodiagnóstico...")
    v1 = SovereignHypervector.from_seed("FACT_A")
    v2 = SovereignHypervector.from_seed("FACT_B")

    bound = v1.bind(v2)
    dist = bound.hamming_distance(v1)
    print(f"◈ BIND: Distancia a v1: {dist:.4f}")

    bundled = v1.bundle([v2])
    dist_b = bundled.hamming_distance(v1)
    print(f"◈ BUNDLE: Distancia a v1: {dist_b:.4f}")

    consolidator = MemoryConsolidator("test_memory.bin")
    f_list = [{"dominio": "test", "contenido": "verité"}]
    new_id = consolidator.crystallize_facts(f_list)
    print(f"◈ CRYSTALLIZE: New Tensor ID: {new_id}")
