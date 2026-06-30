import os
import subprocess
import time
import urllib.request
import json
import concurrent.futures
import threading
import sys

URL = "http://127.0.0.1:3010/infer"
LOG_FILE = "telemetry.log"
RUN_HOURS = 12

def get_process_metrics(pid):
    # RSS in KB
    try:
        rss = subprocess.check_output(f"ps -o rss= -p {pid}", shell=False).decode().strip()
        fd_count = subprocess.check_output(f"lsof -p {pid} | wc -l", shell=False).decode().strip()
        return rss, fd_count
    except Exception:
        return "0", "0"

def stress_worker():
    payload = json.dumps({"prompt": "Long duration memory probe", "system_invariant": "C5-REAL"}).encode("utf-8")
    req = urllib.request.Request(URL, data=payload, headers={'Content-Type': 'application/json'})
    while getattr(threading.current_thread(), "do_run", True):
        try:
            with urllib.request.urlopen(req, timeout=5) as _:
                pass
        except Exception:
            pass

def main():
    print("==============================================")
    print("  MOSKV-1 APEX: F4 P3/P4 EXHAUSTION HARNESS   ")
    print(f"  Duration: {RUN_HOURS} hours")
    print("==============================================")
    
    # 1. Levantar Gateway
    env = os.environ.copy()
    env["DATABASE_URL"] = "exhaustion_ledger.db"
    env["FAKE_PROVIDER"] = "1"
    
    subprocess.run(["cargo", "build", "--release"], check=True, capture_output=True)
    
    proc = subprocess.Popen(
        ["cargo", "run", "--release"], 
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    pid = proc.pid
    print(f"[*] Gateway en Execution (PID: {pid})")
    time.sleep(2)
    
    # 2. Levantar P4: Worker Exhaustion pool
    # Concurrencia sostenida de 20 workers atacando el pool SQLite
    threads = []
    print("[*] Levantando Enjambre P4 (Worker Exhaustion)...")
    for _ in range(20):
        t = threading.Thread(target=stress_worker)
        t.do_run = True
        t.start()
        threads.append(t)
    
    # 3. Telemetry Loop (P3)
    start_time = time.time()
    end_time = start_time + (RUN_HOURS * 3600)
    
    print("[*] Iniciando Telemetry Loop P3. Logs volcados en telemetry.log")
    with open(LOG_FILE, "w") as f:
        f.write("timestamp,elapsed_s,rss_kb,fd_count\n")
    
    try:
        while time.time() < end_time:
            time.sleep(10)
            if proc.poll() is not None:
                print("❌ FATAL: El Gateway colapsó termodinámicamente.")
                break
                
            rss, fd = get_process_metrics(pid)
            elapsed = int(time.time() - start_time)
            log_line = f"{int(time.time())},{elapsed},{rss},{fd}\n"
            
            with open(LOG_FILE, "a") as f:
                f.write(log_line)
                
    except KeyboardInterrupt:
        print("\n[*] Harness abortado manualmente por el Operador.")
        
    finally:
        # Kill workers
        for t in threads:
            t.do_run = False
        # Kill Gateway
        if proc.poll() is None:
            proc.kill()
        print("[*] Limpieza termodinámica completada.")

if __name__ == "__main__":
    main()
