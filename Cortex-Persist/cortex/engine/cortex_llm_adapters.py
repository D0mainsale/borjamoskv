"""
CORTEX-LLM: Frontier Adapters (C5-REAL)
=======================================
Adaptadores SOTA 2026 para interceptar modelos fundacionales y aplicarles el Corsé de Plomo Termodinámico.
"""
import os
import json
import logging
import httpx
from typing import Callable
from cortex.engine.cortex_llm import ThermodynamicInferenceEngine, ThermodynamicDelta

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

logger = logging.getLogger("cortex_llm_adapters")

class FrontierAdapter:
    """Clase base para adaptadores C5-REAL."""
    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self.api_key = api_key
        
    def __call__(self, prompt: str, system: str) -> str:
        raise NotImplementedError("Debe ser implementado por el adaptador físico.")

class GeminiAdapter(FrontierAdapter):
    """Adaptador Termodinámico para Gemini API (SOTA)."""
    def __init__(self, model_name: str = "gemini-3.1-pro", api_key: str = None):
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

class ClaudeOpusAdapter(FrontierAdapter):
    """Adaptador Termodinámico para Claude Opus 4.6 (Anthropic)."""
    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022", api_key: str = None):
        # We use a placeholder for "Opus 4.6" actual API string depending on anthropic release
        self.actual_model_name = "claude-4-6-opus" if "4-6" in model_name else model_name
        super().__init__(self.actual_model_name, api_key or os.environ.get("ANTHROPIC_API_KEY", ""))
        if not Anthropic:
            logger.warning("Anthropic package not installed, falling back to httpx if needed, but not implemented.")
            
    def __call__(self, prompt: str, system: str) -> str:
        if not self.api_key:
            raise RuntimeError("CORTEX-LLM: ANTHROPIC_API_KEY no detectada.")
        if not Anthropic:
            raise RuntimeError("CORTEX-LLM: libreria 'anthropic' no instalada.")
            
        client = Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=self.actual_model_name,
            max_tokens=4096,
            temperature=0.0,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

class O4OmegaAdapter(FrontierAdapter):
    """Adaptador Termodinámico para O4-Omega (OpenAI)."""
    def __init__(self, model_name: str = "o4-omega", api_key: str = None):
        super().__init__(model_name, api_key or os.environ.get("OPENAI_API_KEY", ""))
        
    def __call__(self, prompt: str, system: str) -> str:
        if not self.api_key:
            raise RuntimeError("CORTEX-LLM: OPENAI_API_KEY no detectada.")
        if not OpenAI:
            raise RuntimeError("CORTEX-LLM: libreria 'openai' no instalada.")
            
        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model_name,
            response_format={"type": "json_object"},
            temperature=0.0,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content or "{}"

# =====================================================================
# FACHADA DE INSTANCIACIÓN DIRECTA (SINGULARITY EXPORT)
# =====================================================================

def invocar_cortex_llm_sota(prompt_causal: str, target_model: str = None) -> ThermodynamicDelta:
    """
    Función de una sola llamada para emitir una directiva estructurada C5-REAL 
    hacia el clúster SOTA, filtrada por el motor BFT.
    """
    target = target_model or os.environ.get("CORTEX_SOTA_MODEL", "gemini-3.1-pro")
    
    if "claude" in target:
        adapter = ClaudeOpusAdapter(model_name=target)
    elif "o4" in target or "gpt" in target:
        adapter = O4OmegaAdapter(model_name=target)
    else:
        adapter = GeminiAdapter(model_name=target)
        
    engine = ThermodynamicInferenceEngine(max_thermal_bleed=3)
    return engine.colapsar_onda(prompt_causal, adapter)
