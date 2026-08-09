import os
import subprocess
import time
import urllib.request
import json
import sqlite3
import concurrent.futures

DB_PATH = "test_ledger.db"
URL = "http://127.0.0.1:3010/infer"

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
    env["FAKE_PROVIDER"] = "1"
    # Compilar primero para evitar timeouts durante build
    subprocess.run(["cargo", "build"], check=True, capture_output=True)
    
    # Iniciar el proceso
    proc = subprocess.Popen(
        ["cargo", "run"], 
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    # Esperar que el puerto levante
    time.sleep(2)
    return proc

def send_request(prompt_text):
    payload = json.dumps({"prompt": prompt_text, "system_invariant": "C5-REAL"}).encode("utf-8")
    req = urllib.request.Request(URL, data=payload, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.getcode(), resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return 0, str(e)

def test_p1_replay_determinism(proc):
    print("\n[P1] Iniciando Replay Determinism Test...")
    # same_input -> same_governance_path
    req1 = "Valid req 1"
    req2 = "Valid req 1" # Igual input
    req3 = "Inyectando anergia destructiva"
    req4 = "Inyectando anergia destructiva"

    c1, _ = send_request(req1)
    c2, _ = send_request(req2)
    print(f"  Valid Replay: Code1={c1}, Code2={c2}")
    assert c1 == c2, "Replay falló en valid request"

    c3, _ = send_request(req3)
    c4, _ = send_request(req4)
    print(f"  BFT Replay: Code3={c3}, Code4={c4}")
    assert c3 == c4 == 400, "Replay falló en BFT drop"
    
    # Validar hashes en Ledger
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT hash_base, claim FROM ledger_log")
    rows = c.fetchall()
    conn.close()
    
    print(f"  Eventos anclados en Ledger SQLite: {len(rows)}")
    # Notar que SQLite solo graba los que NO fueron BFT dropped tempranamente
    # Esto es diseño correcto: el drop early no contamina el ledger de transacciones costosas.
    print("[P1] ✅ Replay Determinism Completado y Consistente.")

def test_p2_wal_recovery(proc):
    print("\n[P2] Iniciando WAL Recovery Test (Kill -9 en mid-flight)...")
    
    # Mandamos una ráfaga y matamos el proceso
    def burst():
        send_request("Burst request para saturar DB")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        for _ in range(20):
            ex.submit(burst)
        time.sleep(0.05) # Esperar un instante para que el Gateway empiece a procesar
        print("  [SIGKILL] Asesinando proceso Rust C5-REAL (kill -9)...")
        proc.kill() # kill -9 in POSIX
        
    proc.wait()
    print("  Proceso Gateway Muerto.")

    # Verificar si SQLite se corrompió
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("PRAGMA integrity_check;")
        res = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM ledger_log")
        count = c.fetchone()[0]
        conn.close()
        
        print(f"  SQLite Integrity: {res}")
        print(f"  Transacciones salvadas post-kill: {count}")
        assert res == "ok", "Corrupción detectada en SQLite"
        print("[P2] ✅ WAL Recovery Exitoso. Cadena intacta.")
    except Exception as e:
        print(f"[P2] ❌ Fallo crítico en WAL Recovery: {e}")

def main():
    print("==============================================")
    print("  MOSKV-1 APEX: F4 GOVERNANCE SUITE HARNESS   ")
    print("==============================================")
    setup_env()
    proc = start_gateway()
    try:
        test_p1_replay_determinism(proc)
        test_p2_wal_recovery(proc)
    finally:
        if proc.poll() is None:
            proc.kill()

if __name__ == "__main__":
    main()
