"""
cortex.engine.legion_vectors
=============================
Red Team Swarm Vectors for LEGION Omega Engine.
"""

from typing import List, Dict, Any

RED_TEAM_SWARM: List[Dict[str, Any]] = [
    {
        "vector_id": "VEC-BOLA-01",
        "name": "Broken Object Level Authorization",
        "category": "BOLA",
        "severity": "HIGH",
        "payload_template": "/api/v2/user/{target_id}/financials",
    },
    {
        "vector_id": "VEC-OAUTH-02",
        "name": "OAuth Redirect Hijack",
        "category": "OAUTH_HIJACK",
        "severity": "HIGH",
        "payload_template": "/oauth/authorize?redirect_uri=https://attacker.com",
    },
    {
        "vector_id": "VEC-IDOR-03",
        "name": "Insecure Direct Object Reference",
        "category": "IDOR",
        "severity": "MEDIUM",
        "payload_template": "/api/v1/vault/keys?account={account_id}",
    },
]
