import sys
import time
import subprocess

# Configuración de paths para que Python encuentre los módulos
CORTEX_ROOT = "/Users/borjafernandezangulo/borjamoskv/Cortex-Persist"
sys.path.append(CORTEX_ROOT)

from cortex.sovereign import guard_and_commit_sync

def test_persist_flow():
    print("◈ INICIANDO TEST DE PERSISTENCIA C5-REAL")
    
    # 1. Iniciar el servidor persistente en segundo plano (puerto 8001)
    print("◈ Lanzando CORTEX Persist Server (api.py) en puerto 8001...")
    persist_proc = subprocess.Popen(
        [sys.executable, "cortex/server/api.py"],
        cwd=CORTEX_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(3) # Esperar a que FastAPI arranque
    
    try:
        # 2. Ejecutar un ciclo de custodia y sellado síncrono
        print("◈ Ejecutando guard_and_commit_sync...")
        resultado = guard_and_commit_sync(
            subject="test:forensic",
            predicate="verified_by",
            object_val="antigravity_v1",
            source="herramienta"
        )
        
        print(f"◈ RESULTADO: {resultado.estado} | Hash: {resultado.huella}")
        
        if resultado.estado == "SELLADO":
            print("✅ TEST PASADO: Persistencia C5-REAL Activa.")
        else:
            print(f"❌ TEST FALLIDO: Estado {resultado.estado}. Revisa logs.")
            
    finally:
        print("◈ Cerrando servidores...")
        persist_proc.terminate()

if __name__ == "__main__":
    test_persist_flow()
