import urllib.request
import urllib.error
import json
import concurrent.futures
import time

URL = "http://127.0.0.1:3010/infer"
TOTAL_REQUESTS = 200
CONCURRENCY = 50

def make_request(i):
    # Generar anergia en la mitad de las peticiones para testear BFT Drop.
    if i % 2 == 0:
        prompt = f"Genera un código base. ID={i}"
    else:
        prompt = f"Por favor, con un poco de anergia, genera esto. ID={i}"
        
    payload = json.dumps({
        "prompt": prompt,
        "system_invariant": "C5-REAL"
    }).encode("utf-8")
    
    req = urllib.request.Request(URL, data=payload, headers={'Content-Type': 'application/json'})
    
    try:
        start_t = time.time()
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode()
            status = response.getcode()
            elapsed = time.time() - start_t
            return (i, status, res_body, elapsed)
    except urllib.error.HTTPError as e:
        elapsed = time.time() - start_t
        return (i, e.code, e.read().decode(), elapsed)
    except urllib.error.URLError as e:
        elapsed = time.time() - start_t
        return (i, "CONNECTION_ERR", str(e.reason), elapsed)
    except Exception as e:
        return (i, "ERR", str(e), 0)

def main():
    print(f"[*] C5-REAL STRESS TEST INICIADO: {TOTAL_REQUESTS} reqs, max_workers={CONCURRENCY}")
    start_time = time.time()
    
    results = {"200": 0, "400": 0, "503": 0, "CONNECTION_ERR": 0, "OTHER": 0}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = {executor.submit(make_request, i): i for i in range(TOTAL_REQUESTS)}
        
        for future in concurrent.futures.as_completed(futures):
            idx, status, body, elapsed = future.result()
            
            if status == 200:
                results["200"] += 1
            elif status == 400:
                results["400"] += 1
            elif status == 503:
                results["503"] += 1
            elif status == "CONNECTION_ERR":
                results["CONNECTION_ERR"] += 1
            else:
                results["OTHER"] += 1
                
    total_time = time.time() - start_time
    print("\n===============================")
    print("   MOSKV-1 APEX STRESS REPORT  ")
    print("===============================")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Requests: {TOTAL_REQUESTS}")
    print(f"RPS: {TOTAL_REQUESTS / total_time:.2f}")
    print("\nDistribución BFT:")
    print(f"✅ Collapsed (200 OK): {results['200']}")
    print(f"🛑 BFT Dropped (400 Bad Req): {results['400']}")
    print(f"⚠️  L0 Thermal Fail (503): {results['503']}")
    print(f"❌ Connection Errs: {results['CONNECTION_ERR']}")
    print(f"❓ Other Errs: {results['OTHER']}")

if __name__ == "__main__":
    main()
