import sys

# ∴ CONTEXT: Mythos Bridge v1.0
# Une el descubrimiento OSINT con la ejecución del Fuzzer BOLA.

def run_bridge(domain, target_url, auth_token, tenant_header="X-Tenant-ID"):
    print(f"∴ INITIALIZING MYTHOS BRIDGE FOR: {domain}")
    
    # 1. Ejecutar OSINT para obtener candidatos
    print("∴ PHASE 1: DISCOVERY")
    try:
        # Importamos la lógica de tenant_osint si es posible, o ejecutamos como subprocess
        from tenant_osint_v1 import run_osint
        candidates = run_osint(domain)
    except ImportError:
        print("Error: tenant_osint_v1.py no encontrado en el path.")
        return

    if not candidates:
        print("∴ No se encontraron candidatos. Abortando strike.")
        return

    # 2. Ejecutar Fuzzer BOLA
    print("\n∴ PHASE 2: BOLA STRIKE")
    try:
        from bola_fuzzer_v1 import scan_bola
        headers = {
            "Authorization": f"Bearer {auth_token}",
            tenant_header: "DUMMY_INIT_VAL" # Se sobreescribirá en el fuzzer
        }
        scan_bola(target_url, headers, candidates, header_key=tenant_header)
    except ImportError:
        print("Error: bola_fuzzer_v1.py no encontrado en el path.")
        return

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 mythos_bridge_v1.py <domain> <target_api_url> <auth_token>")
        sys.exit(1)
        
    DOMAIN = sys.argv[1]
    API_URL = sys.argv[2]
    TOKEN = sys.argv[3]
    
    run_bridge(DOMAIN, API_URL, TOKEN)
