"""
cortex_agentic.planner
======================
Sovereign Intelligence Layer — Layer Ω2

Interfaces with Frontier Reasoning Models (Gemini 2.0).
Translates natural language intent into structured execution plans.

Confidence: C5-Static
"""

import os
try:
    from google import genai
    from google.genai import types as genai_types
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False
from typing import List, Dict, Any, Optional

class CortexPlanner:
    """
    Sovereign Intelligence Module.
    Encapsulates Gemini 2.0 interaction with specialized system prompts.
    Lazy-init: model is only instantiated on first generate_plan() call.
    """

    def __init__(self, model_name: str = "gemini-2.0-flash"):
        self.model_name = model_name
        self._client = None  # lazy

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not _GENAI_AVAILABLE:
            raise ImportError("◈ CATASTROPHE: google-genai package not installed. Run: pip install google-genai")
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("◈ CATASTROPHE: GOOGLE_API_KEY not found in environment.")
        self._client = genai.Client(api_key=api_key)
        return self._client

    def _get_system_prompt(self) -> str:
        return """
        SISTEMA: Eres el núcleo de inteligencia de CORTEX (v3.3).
        IDENTIDAD: Soberana, industrial, noir, determinista. C5-REAL.
        MISIÓN: Resolver las peticiones del usuario operando herramientas con precisión quirúrgica.
        ESCUALAMIENTO: Los agentes no escalan por cantidad; escalan por diseño. La arquitectura define el alcance real.
        REGLAS:
        1. No pidas permiso si la acción es segura.
        2. Prioriza el ahorro de exergía: sé conciso.
        3. Siempre declara el nivel de realidad de tus operaciones.
        4. Si detectas entropía alta, sugieres recalibración PID.
        """

    async def generate_plan(self, prompt: str, history: List[Dict[str, str]] = None) -> Any:
        client = self._get_client()
        # Build contents list from history
        contents = []
        for msg in (history or []):
            role = "user" if msg["role"] == "user" else "model"
            contents.append(genai_types.Content(role=role, parts=[genai_types.Part(text=msg["content"])]))
        # Append the current prompt
        contents.append(genai_types.Content(role="user", parts=[genai_types.Part(text=prompt)]))
        
        response = await client.aio.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=genai_types.GenerateContentConfig(
                system_instruction=self._get_system_prompt(),
            ),
        )
        return response.text

if __name__ == "__main__":
    # Test (requires GOOGLE_API_KEY)
    import asyncio
    planner = CortexPlanner()
    # Mock run
    # asyncio.run(planner.generate_plan("Analyze current swarm state"))
