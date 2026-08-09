import requests
import sqlite3
import os

API_HOST = "http://localhost:8001"
AGENT_ID = "borjamoskv-omega"

def test_synthesis_persistence():
    print("🚀 [AUDIT] Starting Headless Synthesis Test...")
    
    # 0. Bootstrap Key
    admin_secret = os.getenv("CORTEX_MASTER_KEY", "DEMO_KEY_VULNERABLE_2026")
    try:
        auth_resp = requests.post(
            f"{API_HOST}/v1/admin/keys",
            json={"admin_secret": admin_secret, "role": "ADMIN", "label": "AUDIT_TEST"}
        )
        token = auth_resp.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Auth Bootstrapped.")
    except Exception as e:
        print(f"❌ Auth Bootstrap Failed: {e}")
        return

    # 1. Trigger Directive
    payload = {
        "prompt": "AUDIT_TEST: Create a temporary file 'audit_proof.txt' in 'audit_test/' directory."
    }
    
    try:
        response = requests.post(
            f"{API_HOST}/v1/archi/directive",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ API Call Failed: {response.status_code} - {response.text}")
            return
            
        data = response.json()
        fact_id = data.get("fact_id")
        print(f"✅ Directive Processed. Fact ID: {fact_id}")
        
        # 2. Verify in DB
        DB_PATH = "server/data/persist.db"
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("SELECT fact_id, project, subject, predicate FROM facts WHERE fact_id = ?", (fact_id,))
        row = c.fetchone()
        
        if row:
            print(f"✅ Ledger Entry Verified: {row}")
        else:
            print(f"❌ Fact not found in database: {fact_id}")
            
        conn.close()
        
    except Exception as e:
        print(f"💥 Audit Script Error: {e}")

if __name__ == "__main__":
    test_synthesis_persistence()
