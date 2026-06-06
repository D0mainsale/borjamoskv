"""
cortex.sovereign.ganchos
========================
Bus de Eventos de Ciclo de Vida Determinista.
Ley Ω6: Los manejadores son funciones puras. 5s de timeout. Sin llamadas LLM.
Ley Ω9: C5-REAL. Cada emisión es una transición de estado verificada.

Tipos de Gancho:
  inicio_sesion       — El daemon arranca
  pre_uso_herramienta — Antes de cualquier llamada a herramienta (puede ABORTAR)
  post_uso_herramienta — Después de que la herramienta responde
  pre_evaluacion      — Antes de la puerta evaluadora
  post_evaluacion     — Después del veredicto del evaluador
  fin_sesion          — La sesión cierra

"Ganchos = hooks, pero con la carga semántica de 'agarrar' el flujo."
"""
from __future__ import annotations

import signal
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Callable, Optional


# ── Tipos ──────────────────────────────────────────────────────────

TIPOS_GANCHO_VALIDOS = frozenset({
    "inicio_sesion",
    "pre_uso_herramienta",
    "post_uso_herramienta",
    "pre_evaluacion",
    "post_evaluacion",
    "fin_sesion",
    # EN aliases for backward compat
    "session_start",
    "pre_tool_use",
    "post_tool_use",
    "pre_eval",
    "post_eval",
    "session_end",
})

# Mapa EN → ES
_MAPA_TIPO_ES = {
    "session_start": "inicio_sesion",
    "pre_tool_use": "pre_uso_herramienta",
    "post_tool_use": "post_uso_herramienta",
    "pre_eval": "pre_evaluacion",
    "post_eval": "post_evaluacion",
    "session_end": "fin_sesion",
}

TIMEOUT_MANEJADOR_SEGUNDOS = 5


class AccionGancho(Enum):
    """Acción terminal devuelta por un manejador de gancho."""
    CONTINUAR   = auto()   # Proceder normalmente
    ABORTAR     = auto()   # Vetar la operación
    REINTENTAR  = auto()   # Solicitar re-ejecución
    TRANSFORMAR = auto()   # Modificar carga y continuar

# Mapa para compatibilidad
_ACCION_A_EN = {
    AccionGancho.CONTINUAR: "CONTINUE",
    AccionGancho.ABORTAR: "ABORT",
    AccionGancho.REINTENTAR: "RETRY",
    AccionGancho.TRANSFORMAR: "TRANSFORM",
}


@dataclass(frozen=True)
class EventoGancho:
    """Evento inmutable emitido a los manejadores de gancho."""
    tipo: str
    carga: dict
    id_sesion: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    marca_temporal: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # EN property bridges
    @property
    def type(self) -> str:
        return self.tipo

    @property
    def payload(self) -> dict:
        return self.carga

    @property
    def session_id(self) -> str:
        return self.id_sesion

    @property
    def timestamp(self) -> str:
        return self.marca_temporal


@dataclass(frozen=True)
class ResultadoGancho:
    """Resultado agregado tras todos los manejadores para un evento."""
    accion: AccionGancho
    evento: EventoGancho
    carga_modificada: Optional[dict] = None
    razon_aborto: Optional[str] = None
    conteo_manejadores: int = 0
    errores: tuple[str, ...] = ()

    # EN property bridges
    @property
    def action(self):
        return self.accion

    @property
    def event(self):
        return self.evento

    @property
    def modified_payload(self):
        return self.carga_modificada

    @property
    def abort_reason(self):
        return self.razon_aborto

    @property
    def handler_count(self):
        return self.conteo_manejadores

    @property
    def errors(self):
        return self.errores


# ── Ayudante de timeout ───────────────────────────────────────────

class _TimeoutManejador(Exception):
    pass


def _manejador_timeout(signum, frame):
    raise _TimeoutManejador("Manejador excedió el timeout")


# ── Registro ──────────────────────────────────────────────────────

class RegistroGanchos:
    """
    Registro FIFO de manejadores de gancho.
    Manejadores: (EventoGancho) -> Optional[ResultadoGancho]
    Si cualquier manejador devuelve ABORTAR, la cadena se detiene inmediatamente.
    Si cualquier manejador devuelve REINTENTAR, el resultado es REINTENTAR.
    """

    def __init__(self):
        # Soporta tanto ES como EN event types
        self._manejadores: dict[str, list[tuple[str, Callable]]] = {
            t: [] for t in TIPOS_GANCHO_VALIDOS
        }

    def _normalizar_tipo(self, tipo_evento: str) -> str:
        """Normaliza un tipo EN a su equivalente ES si existe."""
        return _MAPA_TIPO_ES.get(tipo_evento, tipo_evento)

    def al(
        self,
        tipo_evento: str,
        manejador: Callable[[EventoGancho], Optional[ResultadoGancho]],
        nombre: Optional[str] = None,
    ) -> str:
        """
        Registra un manejador para el tipo de evento dado.
        Devuelve ID del manejador para eliminación posterior.

        al("pre_uso_herramienta", mi_guardian) — castellano nativo.
        """
        normalizado = self._normalizar_tipo(tipo_evento)
        if normalizado not in TIPOS_GANCHO_VALIDOS and tipo_evento not in TIPOS_GANCHO_VALIDOS:
            raise ValueError(
                f"Tipo de gancho inválido '{tipo_evento}'. "
                f"Válidos: {sorted(TIPOS_GANCHO_VALIDOS)}"
            )
        clave = normalizado if normalizado in self._manejadores else tipo_evento
        id_manejador = nombre or uuid.uuid4().hex[:8]
        self._manejadores[clave].append((id_manejador, manejador))
        return id_manejador

    def quitar(self, tipo_evento: str, id_manejador: str) -> bool:
        """Elimina un manejador por ID. Devuelve True si se encontró."""
        normalizado = self._normalizar_tipo(tipo_evento)
        clave = normalizado if normalizado in self._manejadores else tipo_evento
        if clave not in self._manejadores:
            return False
        antes = len(self._manejadores[clave])
        self._manejadores[clave] = [
            (hid, fn) for hid, fn in self._manejadores[clave]
            if hid != id_manejador
        ]
        return len(self._manejadores[clave]) < antes

    def limpiar(self, tipo_evento: Optional[str] = None) -> None:
        """Limpia todos los manejadores, o los de un tipo específico."""
        if tipo_evento:
            normalizado = self._normalizar_tipo(tipo_evento)
            clave = normalizado if normalizado in self._manejadores else tipo_evento
            if clave in self._manejadores:
                self._manejadores[clave] = []
        else:
            for t in self._manejadores:
                self._manejadores[t] = []

    def emitir(self, evento: EventoGancho) -> ResultadoGancho:
        """
        Emite evento a todos los manejadores registrados (orden FIFO).
        Devuelve resultado agregado.

        Semántica de cadena:
          - ABORTAR de cualquier manejador → parada inmediata
          - REINTENTAR → continuar cadena, devolver REINTENTAR
          - TRANSFORMAR → fusionar carga_modificada hacia adelante
          - CONTINUAR → sin efecto
        """
        tipo = self._normalizar_tipo(evento.tipo)
        if tipo not in TIPOS_GANCHO_VALIDOS and evento.tipo not in TIPOS_GANCHO_VALIDOS:
            raise ValueError(f"No se puede emitir tipo de gancho inválido '{evento.tipo}'")

        clave = tipo if tipo in self._manejadores else evento.tipo
        manejadores = self._manejadores.get(clave, [])
        if not manejadores:
            return ResultadoGancho(
                accion=AccionGancho.CONTINUAR,
                evento=evento,
                conteo_manejadores=0,
            )

        accion_final = AccionGancho.CONTINUAR
        carga_fusionada = dict(evento.carga)
        lista_errores: list[str] = []

        for id_manejador, funcion_manejador in manejadores:
            try:
                resultado = self._llamar_con_timeout(funcion_manejador, evento)
            except _TimeoutManejador:
                lista_errores.append(
                    f"Manejador '{id_manejador}' excedió timeout ({TIMEOUT_MANEJADOR_SEGUNDOS}s)"
                )
                continue
            except Exception as exc:
                lista_errores.append(f"Manejador '{id_manejador}' lanzó: {exc}")
                continue

            if resultado is None:
                continue

            # ABORTAR anula todo
            if resultado.accion == AccionGancho.ABORTAR:
                return ResultadoGancho(
                    accion=AccionGancho.ABORTAR,
                    evento=evento,
                    razon_aborto=resultado.razon_aborto or f"Abortado por '{id_manejador}'",
                    conteo_manejadores=manejadores.index((id_manejador, funcion_manejador)) + 1,
                    errores=tuple(lista_errores),
                )

            # REINTENTAR escala
            if resultado.accion == AccionGancho.REINTENTAR:
                accion_final = AccionGancho.REINTENTAR

            # TRANSFORMAR fusiona carga
            if resultado.accion == AccionGancho.TRANSFORMAR and resultado.carga_modificada:
                carga_fusionada.update(resultado.carga_modificada)

        return ResultadoGancho(
            accion=accion_final,
            evento=evento,
            carga_modificada=carga_fusionada if carga_fusionada != evento.carga else None,
            conteo_manejadores=len(manejadores),
            errores=tuple(lista_errores),
        )

    def _llamar_con_timeout(
        self,
        manejador: Callable,
        evento: EventoGancho,
    ) -> Optional[ResultadoGancho]:
        """Llama al manejador con timeout SIGALRM (solo Unix)."""
        manejador_anterior = signal.signal(signal.SIGALRM, _manejador_timeout)
        signal.alarm(TIMEOUT_MANEJADOR_SEGUNDOS)
        try:
            return manejador(evento)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, manejador_anterior)

    @property
    def conteo_manejadores(self) -> int:
        """Total de manejadores registrados en todos los tipos."""
        return sum(len(h) for h in self._manejadores.values())

    def describir(self) -> dict[str, int]:
        """Devuelve conteos de manejadores por tipo de evento."""
        return {t: len(h) for t, h in self._manejadores.items()}

    # ── Aliases EN (Puente) ──────────────────────────────────────────────────
    def on(self, event_type, handler, name=None):
        return self.al(event_type, handler, name)

    def off(self, event_type, handler_id):
        return self.quitar(event_type, handler_id)

    def clear(self, event_type=None):
        return self.limpiar(event_type)

    def emit(self, event):
        return self.emitir(event)

    @property
    def handler_count(self):
        return self.conteo_manejadores

    def describe(self):
        return self.describir()


# ── Registro Global (Patrón Singleton) ────────────────────────────

_registro_global: Optional[RegistroGanchos] = None


def obtener_registro() -> RegistroGanchos:
    """Obtiene o crea el registro global de ganchos."""
    global _registro_global
    if _registro_global is None:
        _registro_global = RegistroGanchos()
    return _registro_global


# EN alias
get_registry = obtener_registro


# ── Decoradores ───────────────────────────────────────────────────

def ejecucion_herramienta_con_ganchos(nombre_herramienta: str):
    """
    Decorador para envolver una ejecución de herramienta con ganchos pre/post.
    Ley Ω6: Los manejadores son deterministas y cronometrados.
    Ley Ω9: Transiciones de estado verificadas.
    """
    def decorador(func: Callable):
        from functools import wraps

        @wraps(func)
        def envoltorio(*args, **kwargs):
            registro = obtener_registro()
            id_sesion = kwargs.get("id_sesion", kwargs.get("session_id", "sesion_desconocida"))

            # 1. Gancho Pre-herramienta
            evento_pre = EventoGancho(
                tipo="pre_uso_herramienta",
                carga={"herramienta": nombre_herramienta, "args": args, "kwargs": kwargs},
                id_sesion=id_sesion,
            )
            resultado_pre = registro.emitir(evento_pre)

            if resultado_pre.accion == AccionGancho.ABORTAR:
                return {
                    "estado": "ABORTADO",
                    "razon": resultado_pre.razon_aborto or "Vetado por gancho",
                    "status": "ABORTED",
                    "reason": resultado_pre.razon_aborto or "Vetoed by hook",
                }

            # Fusionar carga transformada si es necesario
            kwargs_efectivos = kwargs
            if resultado_pre.carga_modificada:
                kwargs_efectivos = {**kwargs, **resultado_pre.carga_modificada}

            # 2. Ejecución
            try:
                resultado = func(*args, **kwargs_efectivos)
            except Exception as e:
                resultado = {"estado": "ERROR", "error": str(e), "status": "ERROR"}

            # 3. Gancho Post-herramienta
            evento_post = EventoGancho(
                tipo="post_uso_herramienta",
                carga={"herramienta": nombre_herramienta, "resultado": resultado},
                id_sesion=id_sesion,
            )
            registro.emitir(evento_post)

            return resultado

        return envoltorio
    return decorador


# EN alias
hooked_tool_execution = ejecucion_herramienta_con_ganchos
