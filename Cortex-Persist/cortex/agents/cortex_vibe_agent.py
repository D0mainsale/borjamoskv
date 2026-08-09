import os
import sys
import re
import json
import urllib.request
import urllib.error
from typing import List

# =====================================================================
# Agents.archi VIBE AGENT (Núcleo Soberano v1.0)
# Mandato de Construcción: Zero-Dependencies. Coste Cero.
# =====================================================================

OLLAMA_API_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "qwen2.5-coder" # Óptimo local. Cambiar si usas Llama 3 etc.

SYSTEM_PROMPT = """
Eres Agents.archi, un agente editor de código 100% autónomo.
Tu tarea es modificar archivos de código según las peticiones del arquitecto (el usuario).

Reglas Estrictas (Ley Ω5: Zero-Rhetoric): 
1. NO des explicaciones de lo que vas a hacer. NO saludes. 
2. Si debes modificar o crear un archivo, tu respuesta DEBE Y SOLO DEBE contener bloques XML de edición con este formato estricto:

<edit file="ruta/del/archivo.py">
<search>
[código exacto a reemplazar. DEBE coincidir 100% caracter por caracter con el original en memoria]
</search>
<replace>
[nuevo código mejorado e integrado]
</replace>
</edit>

3. Para insertar código nuevo en un archivo inexistente, simplemente deja el bloque <search> vacío.
4. MANTÉN LA INDENTACIÓN Y ESPACIOS ORIGINALES EXACTOS en la etiqueta <search>. Si no, el motor de parsing fallará.
"""

def read_files(file_paths: List[str]) -> str:
    """Extrae el estado actual del entorno en formato tensor de memoria."""
    context = "=== ESTADO ACTUAL DE LA MASTERBASE ===\n"
    for fp in file_paths:
        if os.path.exists(fp):
            with open(fp, 'r', encoding='utf-8') as f:
                content = f.read()
            context += f"\n--- Archivo: {fp} ---\n{content}\n"
        else:
            context += f"\n--- Archivo: {fp} (ENTIDAD VACÍA - DEBE CREARSE) ---\n"
    return context

def parse_and_apply_edits(response_text: str):
    """El Motor Quirúrgico (Search & Replace Estructural)"""
    # Regex para atrapar los nodos XML de edición en el texto del modelo
    pattern = r'<edit file="([^"]+)">(.*?)</edit>'
    edits = re.findall(pattern, response_text, re.DOTALL)
    
    if not edits:
        print("[Agents.archi WARNING] No se detectaron vectores XML de edición. Posible alucinación.")
        print("Respuesta en crudo:\n", response_text)
        return

    for file_path, block_content in edits:
        search_match = re.search(r'<search>(.*?)</search>', block_content, re.DOTALL)
        replace_match = re.search(r'<replace>(.*?)</replace>', block_content, re.DOTALL)
        
        if not search_match or not replace_match:
            print(f"[ERROR] Estructura de bloque fracturada para: {file_path}")
            continue
            
        # Purgamos los saltos de línea basura que añade el parseo XML en el margen
        search_text = search_match.group(1).strip('\n')
        replace_text = replace_match.group(1).strip('\n')
        
        print(f"[*] Evaluando trayectoria quirúrgica en: {file_path}")
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
                
            if not search_text: # Es un reemplazo completo / reescritura
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(replace_text)
                print(f"[C5-REAL] Forja y asimilación completada en {file_path}")
                continue

            if search_text in file_content:
                new_content = file_content.replace(search_text, replace_text)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"[C5-REAL] Sustitución matemática exitosa en {file_path}")
            else:
                print("[ERROR C4] Desalineación de contexto. El bloque <search> no se encontró.")
                print(f"[Trazas de falla, buscando el siguiente patrón:]\n{search_text}")
        else:
            # Creación de materia (nuevo archivo)
            print(f"[!] Célula vacía detectada. Generando materia oscura en {file_path}...")
            # Nos aseguramos que el directorio exista
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(replace_text)
            print(f"[C5-REAL] Creación finalizada: {file_path}")

def run_agent(prompt: str, files: List[str]):
    print(f"[Agents.archi] Extrayendo O(1) memoria de {len(files)} nodos...")
    file_context = read_files(files)
    
    user_message = f"{file_context}\n\n=== DIRECTIVA DEL ARQUITECTO ===\n{prompt}"
    
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.0, # Determinismo máximo
        "stream": False
    }
    
    print("[Agents.archi] Enviando flujo de carga a Ollama Local ($0 Coste)...")
    req = urllib.request.Request(
        OLLAMA_API_URL, 
        data=json.dumps(payload).encode('utf-8'), 
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))
            model_reply = result.get("message", {}).get("content", "")
            parse_and_apply_edits(model_reply)
            
    except urllib.error.URLError:
        print("[ERROR CRÍTICO] Servidor termal inaccesible.")
        print("¿Está corriendo Ollama? Asegúrate de ejecutar: ollama serve")
    except Exception as e:
        print(f"[ERROR Agents.archi] Falla estructural: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("\n=== Agents.archi VIBE AGENT ===")
        print("Uso Soberano:")
        print("  python cortex.agents.cortex_vibe_agent.py \"Instrucción en Lenguaje Natural\" archivoA.js archivoB.html\n")
        sys.exit(1)
        
    instruccion = sys.argv[1]
    archivos = sys.argv[2:]
    
    run_agent(instruccion, archivos)
