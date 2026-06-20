"""
CORTEX-LLM: Thermodynamic Inference Engine
==========================================
Nivel de Realidad: C5-REAL
Filtro BFT (Byzantine Fault Tolerant) para Modelos Fundacionales.
Destruye la prosa (Anergia) y colapsa la inferencia en Deltas Estructurales.
"""
import json
import logging
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger("cortex_llm")

@dataclass
class ThermodynamicDelta:
    """Cristalización inmutable del output LLM tras superar el filtro."""
    hash_base: str
    confidence: str # "C1" to "C5"
    claim: str
    operations: list[Dict[str, Any]] # AST operations
    raw_exergy: float # Porcentaje de tokens útiles frente a prosa
    
class ThermodynamicInferenceEngine:
    """
    Corsé de Plomo C5-REAL para LLMs.
    Fuerza a cualquier modelo (OpenAI, Anthropic, Gemini, Ollama) a comportarse
    como un autómata matemático.
    """
    def __init__(self, max_thermal_bleed: int = 3):
        self.max_retries = max_thermal_bleed
        self.system_corset = (
            "You are a C5-REAL Engine. Zero prose. Zero explanations.\n"
            "Return ONLY a strictly valid JSON matching this schema:\n"
            "{\n"
            '  "Claim": "Action summary",\n'
            '  "Proof": {"Base": "hash", "Confidence": "C5"},\n'
            '  "Deltas": [{"op": "replace", "path": "file", "content": "..."}]\n'
            "}\n"
            "Any conversational text will trigger a systemic failure."
        )

    def colapsar_onda(self, prompt_seed: str, adapter_callable) -> ThermodynamicDelta:
        """
        Inyecta el prompt en el modelo, exige JSON puro y penaliza la anergia.
        El adapter_callable debe ser una función (prompt: str, system: str) -> str.
        """
        for attempt in range(self.max_retries):
            raw_response = adapter_callable(prompt_seed, self.system_corset)
            delta, is_valid = self._verificar_bft(raw_response)
            
            if is_valid and delta:
                logger.info(f"[CORTEX-LLM] Onda colapsada con éxito. (Intento {attempt+1})")
                return delta
            else:
                logger.warning(f"[CORTEX-LLM] Anergia detectada (Intento {attempt+1}). Re-inyectando entropía negativa.")
                
        raise RuntimeError("CORTEX-LLM: Thermal Bleed Exceeded. Inferencia colapsada por exceso de Anergia (prosa).")

    def _verificar_bft(self, raw_output: str) -> Tuple[Optional[ThermodynamicDelta], bool]:
        """
        Filtro de tolerancia a fallos bizantinos. 
        Mide la 'Exergía' (ratio señal/ruido).
        """
        try:
            # Buscar puramente el JSON (Destrucción de Green Theater si se filtró algo)
            start_idx = raw_output.find("{")
            end_idx = raw_output.rfind("}") + 1
            if start_idx == -1 or end_idx == 0:
                return None, False
                
            clean_json = raw_output[start_idx:end_idx]
            struct = json.loads(clean_json)
            
            # Validación estricta
            if "Claim" not in struct or "Proof" not in struct or "Deltas" not in struct:
                return None, False
                
            proof = struct.get("Proof", {})
            conf = proof.get("Confidence", "C0")
            base = proof.get("Base", "0x000")
            
            # Cálculo rudimentario de Exergía: (longitud json / longitud total)
            exergy = len(clean_json) / max(len(raw_output), 1)
            
            # C5-REAL rechaza respuestas con demasiada prosa decorativa (exergía < 0.8)
            if exergy < 0.8:
                logger.error(f"Fallo Termodinámico: Exergía muy baja ({exergy:.2f}). Se requiere JSON puro.")
                return None, False
                
            return ThermodynamicDelta(
                hash_base=base,
                confidence=conf,
                claim=struct.get("Claim", ""),
                operations=struct.get("Deltas", []),
                raw_exergy=exergy
            ), True
            
        except json.JSONDecodeError:
            return None, False
        except Exception as e:
            logger.error(f"Error BFT: {str(e)}")
            return None, False
