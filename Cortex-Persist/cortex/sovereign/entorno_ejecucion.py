"""
cortex.sovereign.entorno_ejecucion
=================================
Motor de Orquestación Soberana — Nivel Ω1

Gobierna el ciclo de vida multi-paso de una Ejecución Agéntica CORTEX.
Implementa el patrón de ejecución con monitoreo estricto de estado.

Confianza: C5-Static
"""

from __future__ import annotations

import time
import uuid
import json
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

# Importaciones del Núcleo Soberano
from cortex.agentic.tool_registry import ToolRegistry
from cortex.agentic.persist_membrane import PersistMembrane, FactProposal
from .planificador_soberano import PlanificadorSoberano
from .sustrato_memoria import AlmacenMemoria


# ─── Estados de Ejecución ────────────────────────────────────────────────────

class EstadoEjecucion(Enum):
    """Enumeración de estados para la máquina de ejecución."""
    INICIALIZANDO = auto()
    PLANIFICANDO = auto()
    EJECUTANDO = auto()
    REFLEXIONANDO = auto()
    ESPERA_APP = auto()
    COMPLETANDO = auto()
    EXITO = auto()
    FALLIDO = auto()


@dataclass
class PasoEjecucion:
    """Representa un único hito en el historial de ejecución."""
    nombre: str
    estado: EstadoEjecucion
    marca_tiempo: float = field(default_factory=time.time)
    metadatos: Dict[str, Any] = field(default_factory=dict)


# ─── Núcleo del Entorno ──────────────────────────────────────────────────────

class EntornoEjecucionSoberano:
    """
    Entorno de Ejecución Soberano.
    Coordina entre el Planificador (Razonamiento), el Registro de
    Herramientas (Acción) y la Memoria (Estado).
    """

    def __init__(self, id_sesion: Optional[str] = None):
        self.id_sesion = id_sesion or str(uuid.uuid4())
        self.estado = EstadoEjecucion.INICIALIZANDO
        self.historial: List[PasoEjecucion] = []

        # Componentes del Núcleo
        self.planificador = PlanificadorSoberano()
        self.herramientas = ToolRegistry()
        self.memoria = AlmacenMemoria()
        self.membrana = PersistMembrane()  # Ω-PERSIST: membrana de escritura

        self._registrar_paso("INICIALIZANDO", EstadoEjecucion.INICIALIZANDO)

    def _registrar_paso(
        self,
        nombre: str,
        estado: EstadoEjecucion,
        meta: Optional[Dict[str, Any]] = None
    ):
        paso = PasoEjecucion(nombre=nombre, estado=estado, metadatos=meta or {})
        self.historial.append(paso)
        self.estado = estado

        # Persistir el estado de la ejecución en la memoria soberana
        self.memoria.registrar_ejecucion(
            self.id_sesion,
            estado.name,
            [
                {
                    "name": p.nombre,
                    "status": p.estado.name,
                    "meta": p.metadatos
                } for p in self.historial
            ]
        )
        print(f"◈ [RUNTIME] {self.id_sesion[:8]} | {nombre} -> {estado.name}")

    async def ejecutar_tarea(self, peticion: str) -> Dict[str, Any]:
        """
        Punto de entrada principal para una ejecución agéntica soberana.
        """
        try:
            # Añadir mensaje del usuario a la memoria
            self.memoria.agregar_mensaje(self.id_sesion, "usuario", peticion)

            # 1. Recuperar contexto sellado de CORTEX Persist
            contexto_persist = await self.membrana.search_context(
                query=peticion, limit=5
            )
            pista_contexto = ""
            if contexto_persist:
                pista_contexto = (
                    "\n\n[CONTEXTO_PERSIST]\n" +
                    json.dumps(contexto_persist, ensure_ascii=False)
                )

            # 2. Planificación
            self._registrar_paso(
                "PLANIFICANDO",
                EstadoEjecucion.PLANIFICANDO,
                {"longitud_peticion": len(peticion)}
            )
            historial = self.memoria.obtener_historial(self.id_sesion)
            # Re-mapear historial para interop con planificador
            historial_interop = [
                {"role": m["role"], "content": m["content"]} for m in historial
            ]

            respuesta_plan = await self.planificador.generar_plan(
                peticion + pista_contexto,
                historial=historial_interop
            )

            # 3. Guardián — Verificación de confianza
            propuesta = FactProposal(
                subject=f"session:{self.id_sesion}",
                predicate="plan_generated",
                object_val={
                    "prompt": peticion[:200],
                    "response_len": len(respuesta_plan)
                },
                source="llm",
                session_id=self.id_sesion,
            )
            guardian = await self.membrana.guard_write(propuesta)
            if not guardian.passed:
                self._registrar_paso(
                    "BLOQUEO_GUARDIAN",
                    EstadoEjecucion.FALLIDO,
                    {"razones": guardian.reasons}
                )
                return {
                    "session_id": self.id_sesion,
                    "status": "blocked",
                    "reasons": guardian.reasons
                }

            # 4. Comprometer el plan como un hecho sellado
            compromiso = await self.membrana.commit_fact(
                propuesta, {"response": respuesta_plan[:500]}
            )
            self._registrar_paso(
                "PERSIST_COMPROMETIDO",
                EstadoEjecucion.REFLEXIONANDO,
                {
                    "fact_id": compromiso.fact_id,
                    "persist_status": compromiso.status
                }
            )

            # 5. Añadir respuesta de IA a la memoria local
            self.memoria.agregar_mensaje(
                self.id_sesion,
                "asistente",
                respuesta_plan
            )

            # 6. Éxito y verificación post-acción
            self._registrar_paso(
                "EXITO",
                EstadoEjecucion.EXITO,
                {"longitud_respuesta": len(respuesta_plan)}
            )
            verificacion = await self.membrana.verify_fact(compromiso.fact_id)

            return {
                "session_id": self.id_sesion,
                "status": "success",
                "response": respuesta_plan,
                "steps": len(self.historial),
                "persist": {
                    "fact_id":  compromiso.fact_id,
                    "hash":     compromiso.hash,
                    "verified": verificacion.get("verified", False),
                    "mode":     compromiso.status,
                },
            }

        except Exception as e:
            self._registrar_paso(
                "ERROR",
                EstadoEjecucion.FALLIDO,
                {"error": str(e)}
            )
            try:
                # Intento de registro de error en el sustrato persistente
                prop_error = FactProposal(
                    subject=f"session:{self.id_sesion}",
                    predicate="execution_error",
                    object_val={"error": str(e)[:300]},
                    source="llm",
                    session_id=self.id_sesion,
                )
                await self.membrana.commit_fact(prop_error)
            except Exception:
                pass
            return {
                "session_id": self.id_sesion,
                "status": "error",
                "error": str(e)
            }


if __name__ == "__main__":
    # Prueba de humo (Requiere GOOGLE_API_KEY)
    # import asyncio
    # ent = EntornoEjecucionSoberano()
    # asyncio.run(ent.ejecutar_tarea("Auditar exergía del sistema"))
    pass
