import time
import hmac
import hashlib
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class BypassToken:
    identity: str
    scope: str
    ttl: float
    nonce: str
    reason: str
    signature: str

@dataclass
class NativeRequest:
    tool_name: str
    args: Dict[str, Any]
    exergy_cost: float = 0.1
    project_id: str = "cortex-sovereign"

class MCPNativeBridge:
    """
    Sovereign Native Bridge (v2.2).
    The universal choke point for all tool and command executions.
    Synchronized with Audio-Rate Control Plane.
    """
    def __init__(self, master_key: str):
        self.master_key = master_key
        # READ_ONLY surface always allowed for forensic context
        self.allowlist = {"read_resource", "view_file", "list_dir", "get_file_contents", "read_url_content"}
        self.used_nonces = set()

    def validate_scoped_override(self, token: BypassToken, request: NativeRequest) -> bool:
        """Verify HVA-signed bypass token for emergency recovery."""
        if time.time() > token.ttl:
            return False
            
        if token.nonce in self.used_nonces:
            return False
            
        if token.scope != "*" and token.scope not in request.tool_name:
            return False
            
        msg = f"{token.identity}|{token.scope}|{token.ttl}|{token.nonce}|{token.reason}"
        expected = hmac.new(self.master_key.encode(), msg.encode(), hashlib.sha256).hexdigest()
        
        if token.signature == expected:
            self.used_nonces.add(token.nonce)
            return True
            
        return False

    def authorize_native_action(self, 
                                request: NativeRequest, 
                                governor_snapshot: Dict[str, Any], 
                                override: Optional[BypassToken] = None) -> Dict[str, Any]:
        """
        Enforcement logic for v2.2 Modes.
        """
        mode = governor_snapshot.get("mode", "RED")
        governor_snapshot.get("u", 1.0)
        
        # 1. Global Bypass (Recovery Mode)
        if override and self.validate_scoped_override(override, request):
            return {"authorized": True, "reason": "BYPASS_TOKEN_VALIDATED", "mode": mode}

        # 2. RED Mode (EVASION_CRITICAL): Hard Lockdown
        if mode == "RED":
            if request.tool_name in self.allowlist:
                return {"authorized": True, "reason": "READ_ONLY_ACCESS_ALLOWED", "mode": mode}
            return {"authorized": False, "reason": "EVASION_CRITICAL_LOCKdown", "mode": mode}

        # 3. YELLOW Mode (MASTERING_PRESSURE): Restricted Exergy
        if mode == "YELLOW":
            # Block destructive or low-exergy terminal actions
            if "run_command" in request.tool_name or "delete" in request.tool_name:
                 return {"authorized": False, "reason": "MASTERING_PRESSURE_BLOCK", "mode": mode}
            
            # Budget-based enforcement
            EXERGY_CAP = 0.4
            if request.exergy_cost > EXERGY_CAP:
                return {"authorized": False, "reason": "Y_EXERGY_CAP_EXCEEDED", "mode": mode}
            
            return {"authorized": True, "reason": "YELLOW_BUDGET_APPROVED", "mode": mode}

        # 4. GREEN Mode (NOMINAL_MASTER): Standard Operating Procedure
        return {"authorized": True, "reason": "NOMINAL_ACCESS_GRANTED", "mode": mode}

# Global Instance
bridge = MCPNativeBridge(master_key="SOVEREIGN_MASTER_2026")
