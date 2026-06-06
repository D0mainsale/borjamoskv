"""
cortex.sovereign.planificador
==============================
Capa de Inteligencia Soberana — Capa Ω2

Interfaz con Modelos de Razonamiento Frontera (Gemini 2.0).
Traduce intención en lenguaje natural a planes de ejecución estructurados.

Confianza: C5-Estático
"""

import os
try:
    from google import genai
    from google.genai import types as tipos_genai
    _GENAI_DISPONIBLE = True
except ImportError:
    _GENAI_DISPONIBLE = False
from typing import List, Dict, Any


class Planificador:
    """
    Módulo de Inteligencia Soberana.
    Encapsula la interacción con Gemini 2.0 con instrucciones de sistema especializadas.
    Inicialización perezosa: el modelo solo se instancia en la primera llamada a generar_plan().
    """

    def __init__(self, nombre_modelo: str = "gemini-2.0-flash"):
        self.nombre_modelo = nombre_modelo
        self._cliente = None  # perezoso

    def _obtener_cliente(self):
        if self._cliente is not None:
            return self._cliente
        if not _GENAI_DISPONIBLE:
            raise ImportError("◈ CATÁSTROFE: paquete google-genai no instalado. Ejecutar: pip install google-genai")
        clave_api = os.getenv("GOOGLE_API_KEY")
        if not clave_api:
            raise ValueError("◈ CATÁSTROFE: GOOGLE_API_KEY no encontrada en el entorno.")
        self._cliente = genai.Client(api_key=clave_api)
        return self._cliente

    def _instruccion_sistema(self) -> str:
        """Instrucción del sistema — en el idioma del pensamiento."""
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

    async def generar_plan(self, indicacion: str, historial: List[Dict[str, str]] = None) -> Any:
        """
        Genera un plan de ejecución a partir de una indicación en lenguaje natural.
        'indicación' > 'prompt' — porque indica dirección, no solo solicita.
        """
        cliente = self._obtener_cliente()
        # Construir lista de contenidos desde historial
        contenidos = []
        for msg in (historial or []):
            rol = "user" if msg["role"] == "user" else "model"
            contenidos.append(tipos_genai.Content(role=rol, parts=[tipos_genai.Part(text=msg["content"])]))
        # Añadir la indicación actual
        contenidos.append(tipos_genai.Content(role="user", parts=[tipos_genai.Part(text=indicacion)]))

        respuesta = await cliente.aio.models.generate_content(
            model=self.nombre_modelo,
            contents=contenidos,
            config=tipos_genai.GenerateContentConfig(
                system_instruction=self._instruccion_sistema(),
            ),
        )
        return respuesta.text

    # ── Aliases EN (Puente) ──────────────────────────────────────────────────
    async def generate_plan(self, prompt: str, history=None) -> Any:
        return await self.generar_plan(prompt, history)

    def _get_system_prompt(self) -> str:
        return self._instruccion_sistema()

    def _get_client(self):
        return self._obtener_cliente()


if __name__ == "__main__":
    planificador = Planificador()
    # asyncio.run(planificador.generar_plan("Analizar estado actual del enjambre"))
