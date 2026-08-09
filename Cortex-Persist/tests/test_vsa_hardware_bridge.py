import pytest
from cortex.core.vsa_hardware_bridge.bridge import HardwareBridge


def test_hardware_bridge_collapse_tensor_executes_bitwise_xor():
    bridge = HardwareBridge()
    vec_a = [0b1010, 0b1100]
    vec_b = [0b1100, 0b0101]

    result = bridge.collapse_tensor(vec_a, vec_b)

    assert result == [0b0110, 0b1001]


def test_hardware_bridge_bundle_tensors_executes_majority_voting():
    bridge = HardwareBridge()
    vec_a = [0b1111]
    vec_b = [0b1100]
    vec_c = [0b1010]

    result = bridge.bundle_tensors(vec_a, vec_b, vec_c)

    # Majority bitwise voting on (1111, 1100, 1010):
    # Bit 1: 1, 1, 1 -> 1
    # Bit 2: 1, 1, 0 -> 1
    # Bit 3: 1, 0, 1 -> 1
    # Bit 4: 1, 0, 0 -> 0
    # Result: 1110 = 0b1110 = 14
    assert result == [0b1110]


def test_mcp_collapse_handler_accepts_bundle_operation():
    bridge = HardwareBridge()
    payload = {
        "confidence": "C5",
        "operation": "bundle",
        "data": [[0b1111], [0b1100], [0b1010]]
    }

    res = bridge.mcp_collapse_handler(payload)

    assert res["status"] == "crystallized"
    assert res["state"] == "C5-Dynamic"


def test_mcp_collapse_handler_rejects_non_c5_confidence():
    bridge = HardwareBridge()
    payload = {
        "confidence": "C4",
        "operation": "bind",
        "data": [[1], [1]]
    }

    res = bridge.mcp_collapse_handler(payload)

    assert res["status"] == "rejected"


def test_hardware_bridge_bind_tensor_advanced_modes():
    bridge = HardwareBridge()
    vec_a = [1, 0, 1, 0]
    vec_b = [0, 1, 1, 0]

    # Mode: XOR
    res_xor = bridge.bind_tensor_advanced(vec_a, vec_b, mode="xor")
    assert res_xor["tensor_out"] == [1, 1, 0, 0]
    assert res_xor["popcount"] == 2
    assert res_xor["entropy_anomaly"] is False

    # Mode: PERM_XOR (Role-Filler Pi^1)
    res_perm = bridge.bind_tensor_advanced(vec_a, vec_b, mode="perm_xor", shift_amount=1)
    # Permuted vec_a shift 1: [0, 1, 0, 1] ^ [0, 1, 1, 0] = [0, 0, 1, 1]
    assert res_perm["tensor_out"] == [0, 0, 1, 1]
    assert res_perm["popcount"] == 2

