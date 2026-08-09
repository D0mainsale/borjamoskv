"""
cortex.sovereign.motor
======================
Motor de Orquestación Soberana — Capa Ω1

Gobierna el ciclo de vida multi-paso de una Ejecución Agéntica CORTEX.
Implementa el patrón de ejecución de 8 pasos con monitorización estricta de estado.

Motor = lo que mueve. No un "runtime" abstracto.

Confianza: C5-Estático
"""

from __future__ import annotations

import time
import uuid
import json
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from .planificador import Planificador
from .forja import Forja
from .memoria import AlmacenMemoria
from .membrana import MembranaPersistencia, PropuestaHecho

# ─── Estados de Ejecución ─────────────────────────────────────────────────────

class EstadoEjecucion(Enum):
    INICIALIZANDO = auto()
    PLANIFICANDO  = auto()
    EJECUTANDO    = auto()
    REFLEXIONANDO = auto()
    ESPERANDO_APP = auto()
    COMPLETANDO   = auto()
    EXITO         = auto()
    FALLIDO       = auto()

# Mapa ES → EN para compatibilidad API
_MAPA_ESTADO_EN = {
    EstadoEjecucion.INICIALIZANDO: "INITIALIZING",
    EstadoEjecucion.PLANIFICANDO:  "PLANNING",
    EstadoEjecucion.EJECUTANDO:    "EXECUTING",
    EstadoEjecucion.REFLEXIONANDO: "REFLECTING",
    EstadoEjecucion.ESPERANDO_APP: "WAITING_APP",
    EstadoEjecucion.COMPLETANDO:   "COMPLETING",
    EstadoEjecucion.EXITO:         "SUCCESS",
    EstadoEjecucion.FALLIDO:       "FAILED",
}


@dataclass
class PasoEjecucion:
    nombre: str
    estado: EstadoEjecucion
    marca_temporal: float = field(default_factory=time.time)
    metadatos: Dict[str, Any] = field(default_factory=dict)


# ─── Motor Soberano ──────────────────────────────────────────────────────────

class MotorSoberano:
    """
    Motor de Ejecución Soberana.
    Coordina entre Planificador (Razonamiento), Forja (Acción), y Memoria (Estado).
    """

    def __init__(self, id_sesion: Optional[str] = None):
        self.id_sesion = id_sesion or str(uuid.uuid4())
        self.estado = EstadoEjecucion.INICIALIZANDO
        self.historial: List[PasoEjecucion] = []

        # Componentes nucleares
        self.planificador = Planificador()
        self.forja         = Forja()
        self.memoria       = AlmacenMemoria()
        self.membrana       = MembranaPersistencia()  # Ω-PERSIST: membrana ruta escritura

        self._registrar_paso("INICIALIZANDO", EstadoEjecucion.INICIALIZANDO)

    def _registrar_paso(self, nombre: str, estado: EstadoEjecucion, meta: Optional[Dict[str, Any]] = None):
        paso = PasoEjecucion(nombre=nombre, estado=estado, metadatos=meta or {})
        self.historial.append(paso)
        self.estado = estado

        # Sellar estado de ejecución en memoria
        self.memoria.sellar_ejecucion(
            self.id_sesion,
            estado.name,
            [{"nombre": p.nombre, "estado": p.estado.name, "meta": p.metadatos} for p in self.historial]
        )
        estado_en = _MAPA_ESTADO_EN.get(estado, estado.name)
        print(f"◈ [MOTOR] {self.id_sesion[:8]} | {nombre} -> {estado_en}")

    async def ejecutar_tarea(self, indicacion: str) -> Dict[str, Any]:
        """
        Punto de entrada primario para una ejecución agéntica soberana.
        indicación = lo que indica dirección al motor.
        """
        try:
            # Registrar mensaje del usuario en memoria
            self.memoria.registrar_mensaje(self.id_sesion, "user", indicacion)

            # 1. Recuperar contexto sellado vivo de CORTEX Persist antes de planificar
            contexto_persistencia = await self.membrana.buscar_contexto(
                consulta=indicacion, limite=5
            )
            pista_contexto = ""
            if contexto_persistencia:
                pista_contexto = "\n\n[CONTEXTO_PERSISTENCIA]\n" + json.dumps(contexto_persistencia, ensure_ascii=False)

            # 2. Planificación (con contexto fundamentado en persistencia)
            self._registrar_paso("PLANIFICANDO", EstadoEjecucion.PLANIFICANDO, {"longitud_indicacion": len(indicacion)})
            historial = self.memoria.obtener_historial(self.id_sesion)
            respuesta_plan = await self.planificador.generar_plan(indicacion + pista_contexto, historial=historial)

            # 3. Custodiar — verificación seca de confianza en la salida LLM antes de sellar
            propuesta = PropuestaHecho(
                sujeto=f"sesion:{self.id_sesion}",
                predicado="plan_generado",
                valor_objeto={"indicacion": indicacion[:200], "longitud_respuesta": len(respuesta_plan)},
                fuente="llm",
                id_sesion=self.id_sesion,
            )
            guardia = await self.membrana.custodiar_escritura(propuesta)
            if not guardia.aprobado:
                self._registrar_paso("GUARDIA_BLOQUEADA", EstadoEjecucion.FALLIDO, {"razones": guardia.razones})
                return {"id_sesion": self.id_sesion, "estado": "bloqueado", "razones": guardia.razones,
                        "session_id": self.id_sesion, "status": "blocked", "reasons": guardia.razones}

            # 4. Sellar el plan como hecho tamper-evident
            sellado = await self.membrana.sellar_hecho(propuesta, {"respuesta": respuesta_plan[:500]})
            self._registrar_paso("PERSISTENCIA_SELLADA", EstadoEjecucion.REFLEXIONANDO, {
                "id_hecho": sellado.id_hecho, "estado_persistencia": sellado.estado
            })

            # 5. Añadir respuesta IA a memoria local
            self.memoria.registrar_mensaje(self.id_sesion, "assistant", respuesta_plan)

            # 6. Reflexionar / Éxito + verificación post-acción
            self._registrar_paso("ÉXITO", EstadoEjecucion.EXITO, {"longitud_respuesta": len(respuesta_plan)})
            verificacion = await self.membrana.verificar_hecho(sellado.id_hecho)

            return {
                # Respuesta soberana (ES)
                "id_sesion": self.id_sesion,
                "estado": "exito",
                "respuesta": respuesta_plan,
                "pasos": len(self.historial),
                "persistencia": {
                    "id_hecho": sellado.id_hecho,
                    "huella": sellado.huella,
                    "verificado": verificacion.get("verified", False),
                    "modo": sellado.estado,
                },
                # API compatibility (EN)
                "session_id": self.id_sesion,
                "status": "success",
                "response": respuesta_plan,
                "steps": len(self.historial),
                "persist": {
                    "fact_id": sellado.id_hecho,
                    "hash": sellado.huella,
                    "verified": verificacion.get("verified", False),
                    "mode": sellado.status,
                },
            }

        except Exception as e:
            self._registrar_paso("ERROR", EstadoEjecucion.FALLIDO, {"error": str(e)})
            try:
                propuesta_fallo = PropuestaHecho(
                    sujeto=f"sesion:{self.id_sesion}",
                    predicado="error_ejecucion",
                    valor_objeto={"error": str(e)[:300]},
                    fuente="llm",
                    id_sesion=self.id_sesion,
                )
                await self.membrana.sellar_hecho(propuesta_fallo)
            except Exception:
                pass  # fallo de membrana jamás suprime el error original
            return {
                "id_sesion": self.id_sesion, "estado": "error", "error": str(e),
                "session_id": self.id_sesion, "status": "error",
            }

    # ── Aliases EN (Puente) ──────────────────────────────────────────────────
    async def execute_task(self, prompt: str) -> Dict[str, Any]:
        return await self.ejecutar_tarea(prompt)

    @property
    def session_id(self) -> str:
        return self.id_sesion

    @session_id.setter
    def session_id(self, value: str):
        self.id_sesion = value

    @property
    def status(self):
        return self.estado

    @status.setter
    def status(self, value):
        self.estado = value

    @property
    def history(self):
        return self.historial

    # Bridge component access with EN names
    @property
    def planner(self):
        return self.planificador

    @property
    def tools(self):
        return self.forja

    @property
    def memory(self):
        return self.memoria

    @property
    def membrane(self):
        return self.membrana


if __name__ == "__main__":
    motor = MotorSoberano()
    # asyncio.run(motor.ejecutar_tarea("Auditar exergía del sistema"))
