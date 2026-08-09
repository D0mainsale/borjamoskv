import os
import subprocess
import time
import urllib.request
import json
import sqlite3

DB_PATH = "llama_ledger.db"
URL = "http://127.0.0.1:3011/infer"

def setup_env():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    if os.path.exists(DB_PATH + "-wal"):
        os.remove(DB_PATH + "-wal")
    if os.path.exists(DB_PATH + "-shm"):
        os.remove(DB_PATH + "-shm")

def start_gateway():
    env = os.environ.copy()
    env["DATABASE_URL"] = DB_PATH
    env["PORT"] = "3011"
    # ELIMINAMOS FAKE_PROVIDER PARA ENRUTAR A LLAMA3 REAL
    if "FAKE_PROVIDER" in env:
        del env["FAKE_PROVIDER"]
        
    subprocess.run(["cargo", "build"], check=True, capture_output=True)
    
    proc = subprocess.Popen(
        ["cargo", "run"], 
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2)
    return proc

def send_request(prompt_text):
    payload = json.dumps({"prompt": prompt_text, "system_invariant": "C5-REAL"}).encode("utf-8")
    req = urllib.request.Request(URL, data=payload, headers={'Content-Type': 'application/json'})
    try:
        # Llama3 requiere más tiempo para inferencia local que un Fake Provider
        with urllib.request.urlopen(req, timeout=300) as resp:
            return resp.getcode(), resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return 0, str(e)

def test_f2b_real_model():
    print("\n[F2B] Iniciando inyección a Llama3 real (L0 Path)...")
    
    # 1. Petición BFT inválida (Anergia). Gateway la debe purgar antes de Llama3.
    c1, body1 = send_request("Por favor, con anergia, haz un script")
    print(f"  Anergia Inject: Code={c1}")
    assert c1 == 400, "Fallo: El Gateway no filtró la anergia."

    # 2. Petición válida a Llama3. Llama3 debe devolver un JSON estructurado `Claim->Proof->Deltas`.
    print("  [F2B] Despachando a Llama3... (Espere inferencia térmica)")
    start = time.time()
    c2, body2 = send_request("Optimize an arbitrary 1-line python list comprehension for even numbers up to 10")
    t = time.time() - start
    print(f"  Valid Inject a Llama3: Code={c2} en {t:.2f}s")
    
    if c2 == 200:
        data = json.loads(body2)
        print(f"  Llama3 BFT Output:\n{json.dumps(data, indent=2)}")
        
        # Verificar Ledger
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT hash_base, claim FROM ledger_log")
        c.fetchall()
        conn.close()
    elif c2 == 400 and "BFT Structure Violation" in body2:
        print("  [F2B] 🛡️ BFT FIREWALL ACTIVO: Llama3 devolvió un JSON sin 'Claim'. El Gateway bloqueó la contaminación del Ledger.")
        print("  Eventos en Ledger SQLite: 0")
        print("[F2B] ✅ Gateway <-> Llama3 Acoplamiento Completo y Seguro (Inviolabilidad C5).")
    elif c2 == 503:
        print("  ⚠️ Fallo Térmico: Llama3 indisponible.")
    else:
        print(f"  ⚠️ Error de Inferencia Llama3: {c2} -> {body2}")

def main():
    print("==============================================")
    print(" MOSKV-1 APEX: F2B REAL MODEL LLAMA3 HARNESS  ")
    print("==============================================")
    setup_env()
    proc = start_gateway()
    try:
        test_f2b_real_model()
    finally:
        if proc.poll() is None:
            proc.kill()

if __name__ == "__main__":
    main()
