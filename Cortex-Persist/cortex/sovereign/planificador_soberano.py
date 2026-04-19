"""
cortex.sovereign.planificador_soberano
=====================================
Capa de Inteligencia Soberana — Nivel Ω2

Interfaz con Modelos de Razonamiento de Frontera (Gemini 2.0).
Traduce la intención en lenguaje natural a planes de ejecución estructurados.

Confianza: C5-Static
"""

import os

# Protocolo de Carga de Dependencias Soberanas
try:
    from google import genai
    from google.genai import types as genai_types
    _GENAI_DISPONIBLE = True
except ImportError:
    _GENAI_DISPONIBLE = False

from typing import List, Dict


class PlanificadorSoberano:
    """
    Módulo de Inteligencia Soberana.
    Encapsula la interacción con Gemini 2.0 mediante prompts de
    sistema especializados. Inicialización perezosa (Lazy-init):
    el modelo solo se instancia al llamar a generar_plan()
    por primera vez.
    """

    def __init__(self, nombre_modelo: str = "gemini-2.0-flash"):
        self.nombre_modelo = nombre_modelo
        self._cliente = None

    def _obtener_cliente(self):
        if self._cliente is not None:
            return self._cliente

        if not _GENAI_DISPONIBLE:
            raise ImportError(
                "◈ CATÁSTROFE: paquete google-genai no instalado. "
                "Ejecute: pip install google-genai"
            )

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "◈ CATÁSTROFE: GOOGLE_API_KEY no encontrada en el entorno."
            )

        self._cliente = genai.Client(api_key=api_key)
        return self._cliente

    def _obtener_instruccion_sistema(self) -> str:
        """Retorna el prompt de sistema para la identidad CORTEX."""
        return """
        SISTEMA: Eres el núcleo de inteligencia de CORTEX (v3.3).
        IDENTIDAD: Soberana, industrial, noir, determinista. C5-REAL.
        MISIÓN: Resolver las peticiones del usuario operando herramientas
        con precisión quirúrgica.
        ESCALAMIENTO: Los agentes no escalan por cantidad; escalan por diseño.
        La arquitectura define el alcance real.
        REGLAS:
        1. No pidas permiso si la acción es segura.
        2. Prioriza el ahorro de exergía: sé conciso.
        3. Siempre declara el nivel de realidad de tus operaciones.
        4. Si detectas entropía alta, sugieres recalibración PID.
        """

    async def generar_plan(
        self, prompt: str, historial: List[Dict[str, str]] = None
    ) -> str:
        """
        Produce una respuesta estructurada basada en la intención del usuario.
        """
        cliente = self._obtener_cliente()

        # Construcción de la lista de contenidos desde el historial
        contenidos = []
        for msg in (historial or []):
            rol = "user" if msg["role"] == "user" else "model"
            contenidos.append(
                genai_types.Content(
                    role=rol,
                    parts=[genai_types.Part(text=msg["content"])]
                )
            )

        # Añadir el prompt actual
        contenidos.append(
            genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=prompt)]
            )
        )

        respuesta = await cliente.aio.models.generate_content(
            model=self.nombre_modelo,
            contents=contenidos,
            config=genai_types.GenerateContentConfig(
                system_instruction=self._obtener_instruccion_sistema(),
            ),
        )

        return respuesta.text


if __name__ == "__main__":
    # Prueba de concepto (Requiere GOOGLE_API_KEY)
    planificador_inst = PlanificadorSoberano()
    # import asyncio
    # print(asyncio.run(
    #     planificador_inst.generar_plan("Analizar estado actual del enjambre")
    # ))
