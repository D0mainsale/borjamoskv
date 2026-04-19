import hmac
import hashlib
import os

SOVEREIGN_SALT = "CORTEX_DEFAULT_ENTROPY_2026"
SOVEREIGN_PEPPER = b"INDUSTRIAL_NOIR_SECRET_2026"

def hmac_subscriber_id(uid: str) -> str:
    combined = f"{uid}{SOVEREIGN_SALT}".encode()
    h = hmac.new(SOVEREIGN_PEPPER, combined, hashlib.sha256)
    return h.hexdigest()[:16]

def mask_ip(ip: str) -> str:
    if "." in ip:
        parts = ip.split(".")
        return ".".join(parts[:3]) + ".x"
    if ":" in ip:
        parts = ip.split(":")
        return ":".join(parts[:3]) + "::x"
    return "unknown"

# Test Cases
test_id = "subscriber_01"
h1 = hmac_subscriber_id(test_id)
h2 = hmac_subscriber_id(test_id)

print(f"HMAC Consistency: {h1 == h2} | Hash: {h1}")
print(f"IPv4 Masking: {mask_ip('192.168.1.100')} -> Expected: 192.168.1.x")
print(f"IPv6 Masking: {mask_ip('2001:0db8:85a3:0000:0000:8a2e:0370:7334')} -> Expected: 2001:0db8:85a3::x")
