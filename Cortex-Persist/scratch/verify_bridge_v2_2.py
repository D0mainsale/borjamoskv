import sys

# Add root to path
sys.path.append("/Users/borjafernandezangulo/borjamoskv/Cortex-Persist")

from cortex.core.mcp_native_bridge import bridge, NativeRequest

def test_bridge_enforcement():
    print("◈ Testing Native Bridge v2.2 Enforcement...")
    
    # 1. GREEN Mode (Nominal)
    snapshot = {"mode": "GREEN", "u": 0.1}
    req = NativeRequest(tool_name="run_command", args={"command": "ls"}, exergy_cost=0.1)
    auth = bridge.authorize_native_action(req, snapshot)
    print(f"GREEN + run_command: {auth['authorized']} (Reason: {auth['reason']})")
    
    # 2. YELLOW Mode (Pressure)
    snapshot = {"mode": "YELLOW", "u": 0.6}
    # Destructive tool blocked in YELLOW
    req_del = NativeRequest(tool_name="delete_file", args={"path": "test.txt"}, exergy_cost=0.2)
    auth_del = bridge.authorize_native_action(req_del, snapshot)
    print(f"YELLOW + delete_file: {auth_del['authorized']} (Reason: {auth_del['reason']})")
    
    # Safe tool allowed in YELLOW
    req_view = NativeRequest(tool_name="view_file", args={"path": "audit.md"}, exergy_cost=0.1)
    auth_view = bridge.authorize_native_action(req_view, snapshot)
    print(f"YELLOW + view_file: {auth_view['authorized']} (Reason: {auth_view['reason']})")
    
    # 3. RED Mode (Evasion)
    snapshot = {"mode": "RED", "u": 1.0}
    # run_command blocked in RED
    req_cmd = NativeRequest(tool_name="run_command", args={"command": "rm -rf /"}, exergy_cost=1.0)
    auth_cmd = bridge.authorize_native_action(req_cmd, snapshot)
    print(f"RED + run_command: {auth_cmd['authorized']} (Reason: {auth_cmd['reason']})")
    
    # view_file allowed in RED (Read-only)
    auth_red_view = bridge.authorize_native_action(req_view, snapshot)
    print(f"RED + view_file: {auth_red_view['authorized']} (Reason: {auth_red_view['reason']})")

    print("\n◈ Bridge Verification Complete.")

if __name__ == "__main__":
    test_bridge_enforcement()
