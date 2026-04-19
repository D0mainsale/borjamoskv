import subprocess
import re
import requests
import sys

# ∴ CONTEXT: Mythos OSINT Tenant Enumerator v1.0
# Extrae posibles Tenant-IDs de subdominios y configuraciones JS públicas.

def get_subdomains(domain):
    """
    Usa subfinder (vía shell) para obtener subdominios.
    """
    print(f"∴ RUNNING SUBFINDER ON: {domain}")
    try:
        result = subprocess.run(["subfinder", "-d", domain, "-silent"], capture_output=True, text=True)
        return result.stdout.splitlines()
    except FileNotFoundError:
        print("Error: 'subfinder' no encontrado. Ejecuta el bootstrapper primero.")
        return []

def extract_from_js(url):
    """
    Busca patrones de tenant_id en el HTML/JS de una URL.
    """
    patterns = [
        r'tenantId["\']:\s*["\']([^"\']+)["\']',
        r'orgId["\']:\s*["\']([^"\']+)["\']',
        r'workspace["\']:\s*["\']([^"\']+)["\']',
        r'api/v1/([^/]+)/dashboard'
    ]
    tenants = set()
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            for p in patterns:
                matches = re.findall(p, response.text)
                for m in matches:
                    tenants.add(m)
    except Exception:
        pass
    return tenants

def run_osint(domain):
    print(f"∴ STARTING OSINT FOR: {domain}")
    subdomains = get_subdomains(domain)
    all_tenants = set()
    
    # Extraer de subdominios (ej: org1.target.com -> org1)
    for sub in subdomains:
        prefix = sub.split('.')[0]
        if prefix != "www" and prefix != domain.split('.')[0]:
            all_tenants.add(prefix)
            
    # Extraer de fuentes JS (Muestreo de los primeros 5 subdominios)
    for sub in list(subdomains)[:5]:
        url = f"https://{sub}"
        print(f"∴ PARSING JS: {url}")
        all_tenants.update(extract_from_js(url))
        
    print(f"\n∴ DISCOVERED CANDIDATE TENANT-IDs: {len(all_tenants)}")
    for t in sorted(all_tenants):
        print(f"  - {t}")
    
    return list(all_tenants)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_domain = sys.argv[1]
    else:
        target_domain = "example.com" # Cambiar por el target real
    
    run_osint(target_domain)
