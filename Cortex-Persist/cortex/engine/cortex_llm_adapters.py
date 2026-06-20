"""
CORTEX-LLM: Frontier Adapters (C5-REAL)
=======================================
Adaptadores para interceptar modelos fundacionales y aplicarles el Corsé de Plomo Termodinámico.
"""
import os
import json
import logging
import httpx
from typing import Callable
from cortex.engine.cortex_llm import ThermodynamicInferenceEngine, ThermodynamicDelta

logger = logging.getLogger("cortex_llm_adapters")

class FrontierAdapter:
    """Clase base para adaptadores C5-REAL."""
    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self.api_key = api_key
        
    def __call__(self, prompt: str, system: str) -> str:
        raise NotImplementedError("Debe ser implementado por el adaptador físico.")

class GeminiAdapter(FrontierAdapter):
    """Adaptador Termodinámico para Gemini API."""
    def __init__(self, model_name: str = "gemini-1.5-pro", api_key: str = None):
        super().__init__(model_name, api_key or os.environ.get("GEMINI_API_KEY", ""))
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
        
    def __call__(self, prompt: str, system: str) -> str:
        if not self.api_key:
            raise RuntimeError("CORTEX-LLM: GEMINI_API_KEY no detectada en la membrana.")
            
        payload = {
            "system_instruction": {
                "parts": {"text": system}
            },
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.0, # Cero Entropía C5-REAL
                "responseMimeType": "application/json"
            }
        }
        
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{self.endpoint}?key={self.api_key}",
                json=payload
            )
            resp.raise_for_status()
            data = resp.json()
            
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                logger.error("[CORTEX-LLM] Gemini retornó estructura anómala.")
                return "{}" # Falla gracefully hacia el filtro BFT

# =====================================================================
# FACHADA DE INSTANCIACIÓN DIRECTA (SINGULARITY EXPORT)
# =====================================================================

def invocar_cortex_llm_gemini(prompt_causal: str) -> ThermodynamicDelta:
    """
    Función de una sola llamada para emitir una directiva estructurada C5-REAL 
    hacia Gemini, filtrada por el motor BFT.
    """
    engine = ThermodynamicInferenceEngine(max_thermal_bleed=3)
    adapter = GeminiAdapter()
    return engine.colapsar_onda(prompt_causal, adapter)
