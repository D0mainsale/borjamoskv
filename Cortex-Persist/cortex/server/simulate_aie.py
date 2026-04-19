import json
import time
import hmac
import hashlib
from datetime import datetime, timedelta

SOVEREIGN_FORENSIC_LEDGER = "/Users/borjafernandezangulo/borjamoskv/Cortex-Persist/forensic_ledger.jsonl"
SOVEREIGN_SALT = "CORTEX_DEFAULT_ENTROPY_2026"
SOVEREIGN_PEPPER = b"INDUSTRIAL_NOIR_SECRET_2026"

def hmac_id(uid):
    combined = f"{uid}{SOVEREIGN_SALT}".encode()
    return hmac.new(SOVEREIGN_PEPPER, combined, hashlib.sha256).hexdigest()[:16]

def generate_entry(uid, timestamp, sig_class, ctype, path="/api/v1/signal"):
    return {
        "ts": timestamp,
        "dt": datetime.fromtimestamp(timestamp).isoformat(),
        "h_sid": hmac_id(uid),
        "class": sig_class,
        "m_ip": "1.2.3.x",
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "ctype": ctype,
        "path": path
    }

# Clear previous simulation data (optional, but good for clean test)
# with open(SOVEREIGN_FORENSIC_LEDGER, "w") as f: pass

entries = []
now = time.time()

# 1. HVA Receptor: High Exergy (Multiple days, multiple types)
for d in range(5):
    ts = now - (d * 86400)
    entries.append(generate_entry("high_exergy_user", ts, "human_likely", "theory"))
    entries.append(generate_entry("high_exergy_user", ts + 100, "human_likely", "music"))

# 2. Consistent Reader: Mid Exergy
for d in range(3):
    ts = now - (d * 86400)
    entries.append(generate_entry("consistent_user", ts, "human_likely", "satire"))

# 3. Machine Noise: Low Exergy (Penalty)
for i in range(10):
    entries.append(generate_entry("bot_user", now, "machine_likely", "theory"))

# 4. Privacy Proxy: Apple MPP
for i in range(5):
    entries.append(generate_entry("mpp_user", now, "privacy_proxy", "theory"))

with open(SOVEREIGN_FORENSIC_LEDGER, "a") as f:
    for e in entries:
        f.write(json.dumps(e) + "\n")

print(f"◈ AIE_SIM: {len(entries)} signals injected into ledger.")
print(f"◈ HVA_ID (Target): {hmac_id('high_exergy_user')}")
