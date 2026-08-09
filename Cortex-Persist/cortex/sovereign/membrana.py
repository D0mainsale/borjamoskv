"""
cortex.sovereign.membrana
=========================
CORTEX Persist — Membrana de Verificación para la Ruta de Escritura
Capa Ω-PERSIST (entre Forja/Motor y el Libro Mayor)

ARQUITECTURA:
  MotorSoberano.ejecutar_tarea()
    └─> MembranaPersistencia.custodiar_escritura()   ← verificación seca
    └─> Forja.ejecutar()
    └─> MembranaPersistencia.sellar_hecho()          ← persistencia sellada
    └─> MembranaPersistencia.verificar_hecho()       ← auditoría post-acción

Superficie HTTP (local-first, SQLite+WAL):
  POST /v1/trust/guard  → Verificación seca del esquema
  POST /v1/facts        → Sellar un hecho individual
  POST /v1/facts/batch  → Sellado masivo
  POST /v1/facts/search → Recuperar contexto vivo
  GET  /v1/facts/{id}/verify → Comprobación de integridad
  GET  /v1/projects/{project}/export → Exportación de evidencia
  POST /v1/facts/{id}/taint  → Contaminación causal

Confianza: C5-Estático (modo local-first endurecido)
"""

from __future__ import annotations

import os
import time
import json
import hashlib
import logging
from typing import Any, Dict, Optional, List, Literal
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger("membrana_persistencia")

# ── Configuración (extraída del entorno, defaults para desarrollo local) ──────

URL_BASE_PERSIST = os.getenv("CORTEX_PERSIST_URL", "http://localhost:8001")
TOKEN_PERSIST    = os.getenv("CORTEX_PERSIST_TOKEN", "")
PROYECTO_PERSIST = os.getenv("CORTEX_PERSIST_PROJECT", "cortex-sovereign")
TIMEOUT_PERSIST  = float(os.getenv("CORTEX_PERSIST_TIMEOUT", "3.0"))

# Rol: AGENTE puede escribir, OBSERVADOR solo lectura, ADMIN para arranque
ROL_PERSIST      = os.getenv("CORTEX_PERSIST_ROLE", "AGENTE")


# ── SHA-256 para cadena de fallback local ─────────────────────────────────────

def _sha256(carga: Dict[str, Any]) -> str:
    canonico = json.dumps(carga, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonico.encode()).hexdigest()


# ── Estructuras de datos ──────────────────────────────────────────────────────

@dataclass
class PropuestaHecho:
    """
    Una escritura propuesta. NO es estado aún.
    Cada salida LLM, resultado de herramienta o respuesta API externa empieza aquí.
    """
    sujeto:      str                                        # p.ej. "deploy:ai-ml"
    predicado:   str                                        # p.ej. "ejecutado_por"
    valor_objeto: Any                                       # valor, puede ser dict
    fuente:      Literal["llm", "herramienta", "api", "humano"]
    confianza:   float = 1.0                                # [0.0 – 1.0]
    id_sesion:   Optional[str] = None
    metadatos:   Dict[str, Any] = field(default_factory=dict)

    def a_carga(self) -> Dict[str, Any]:
        """Serializa la propuesta para transmisión HTTP."""
        return {
            "project":    PROYECTO_PERSIST,
            "subject":    self.sujeto,
            "predicate":  self.predicado,
            "object":     self.valor_objeto,
            "source":     self.fuente,
            "confidence": self.confianza,
            "session_id": self.id_sesion,
            "metadata":   self.metadatos,
            "proposed_at": time.time(),
        }

    # EN alias
    def to_payload(self) -> Dict[str, Any]:
        return self.a_carga()


@dataclass
class ResultadoGuardia:
    """Resultado de la custodia de escritura."""
    aprobado: bool
    estado: str          # "APROBADO" | "BLOQUEADO" | "AVISO" | "FUERA_DE_LINEA"
    razones: List[str] = field(default_factory=list)
    id_hecho: Optional[str] = None

    @property
    def passed(self) -> bool:
        return self.aprobado

    @property
    def status(self) -> str:
        _mapa = {"APROBADO": "PASS", "BLOQUEADO": "BLOCK", "AVISO": "WARN", "FUERA_DE_LINEA": "OFFLINE"}
        return _mapa.get(self.estado, self.estado)

    @property
    def reasons(self) -> List[str]:
        return self.razones

    @property
    def fact_id(self) -> Optional[str]:
        return self.id_hecho


@dataclass
class ResultadoSellado:
    """Resultado del sellado de un hecho."""
    exito: bool
    id_hecho: Optional[str]
    huella: Optional[str]
    estado: str   # "SELLADO" | "FALLBACK" | "FALLIDO"

    @property
    def success(self) -> bool:
        return self.exito

    @property
    def fact_id(self) -> Optional[str]:
        return self.id_hecho

    @property
    def hash(self) -> Optional[str]:
        return self.huella

    @property
    def status(self) -> str:
        _mapa = {"SELLADO": "COMMITTED", "FALLBACK": "FALLBACK", "FALLIDO": "FAILED"}
        return _mapa.get(self.estado, self.estado)


# ── MembranaPersistencia ──────────────────────────────────────────────────────

class MembranaPersistencia:
    """
    Membrana de verificación para la ruta de escritura CORTEX.

    Patrón de uso (dentro de MotorSoberano.ejecutar_tarea):

        membrana = MembranaPersistencia()

        # 1. Custodiar antes de cualquier mutación
        guardia = await membrana.custodiar_escritura(propuesta)
        if not guardia.aprobado:
            raise RuntimeError(f"PERSISTENCIA_BLOQUEADA: {guardia.razones}")

        # 2. Ejecutar herramienta / acción
        resultado = herramienta.ejecutar(...)

        # 3. Sellar resultado como hecho
        sellado = await membrana.sellar_hecho(propuesta, resultado)

        # 4. Verificación post-acción
        await membrana.verificar_hecho(sellado.id_hecho)
    """

    def __init__(self):
        cabeceras = {"Content-Type": "application/json"}
        if TOKEN_PERSIST:
            cabeceras["Authorization"] = f"Bearer {TOKEN_PERSIST}"
        self._cliente = httpx.AsyncClient(
            base_url=URL_BASE_PERSIST,
            headers=cabeceras,
            timeout=TIMEOUT_PERSIST,
        )
        self._en_linea: Optional[bool] = None

    # ── 1. Custodiar (verificación seca, idempotente) ─────────────────────────

    async def custodiar_escritura(self, propuesta: PropuestaHecho) -> ResultadoGuardia:
        """
        POST /v1/trust/guard
        No destructiva. Comprueba esquema, política y reglas de admisión.
        Llamar ANTES de cualquier ejecución de herramienta.
        Falla ABIERTA (devuelve AVISO) si CORTEX Persist está fuera de línea.
        """
        carga = {**propuesta.a_carga(), "dry_run": True}
        try:
            r = await self._cliente.post("/v1/trust/guard", json=carga)
            self._en_linea = True
            cuerpo = r.json()
            if r.status_code == 200 and cuerpo.get("admitted", False):
                return ResultadoGuardia(aprobado=True, estado="APROBADO", razones=cuerpo.get("notes", []))
            else:
                return ResultadoGuardia(aprobado=False, estado="BLOQUEADO", razones=cuerpo.get("violations", ["GUARDIA_RECHAZADA"]))
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            self._en_linea = False
            logger.warning(f"◈ MEMBRANA_PERSISTENCIA: Custodia fuera de línea — fallo abierto. [{e}]")
            return ResultadoGuardia(aprobado=True, estado="FUERA_DE_LINEA", razones=["persistencia_inalcanzable"])

    # ── 2. Sellar (escritura sellada) ─────────────────────────────────────────

    async def sellar_hecho(
        self,
        propuesta: PropuestaHecho,
        resultado: Optional[Any] = None,
    ) -> ResultadoSellado:
        """
        POST /v1/facts
        Sella la propuesta (con resultado opcional) como hecho a prueba de manipulación.
        Usa fallback local SHA-256 si CORTEX Persist está fuera de línea.
        """
        carga = propuesta.a_carga()
        if resultado is not None:
            carga["result"] = resultado if isinstance(resultado, dict) else {"value": str(resultado)}

        try:
            r = await self._cliente.post("/v1/facts", json=carga)
            self._en_linea = True
            if r.status_code in (200, 201):
                cuerpo = r.json()
                return ResultadoSellado(
                    exito=True,
                    id_hecho=cuerpo.get("fact_id"),
                    huella=cuerpo.get("hash"),
                    estado="SELLADO",
                )
            else:
                logger.error(f"◈ MEMBRANA_PERSISTENCIA: Sellado rechazado [{r.status_code}]: {r.text}")
                return ResultadoSellado(exito=False, id_hecho=None, huella=None, estado="FALLIDO")
        except (httpx.ConnectError, httpx.TimeoutException):
            self._en_linea = False
            huella_local = _sha256(carga)
            _escribir_fallback_local(carga, huella_local)
            return ResultadoSellado(exito=True, id_hecho=None, huella=huella_local, estado="FALLBACK")

    # ── 3. Sellado masivo ─────────────────────────────────────────────────────

    async def sellar_lote(self, propuestas: List[PropuestaHecho]) -> List[ResultadoSellado]:
        """POST /v1/facts/batch — sellado masivo."""
        items = [p.a_carga() for p in propuestas]
        try:
            r = await self._cliente.post("/v1/facts/batch", json={"facts": items, "project": PROYECTO_PERSIST})
            self._en_linea = True
            resultados = r.json().get("results", [])
            return [
                ResultadoSellado(
                    exito=item.get("success", False),
                    id_hecho=item.get("fact_id"),
                    huella=item.get("hash"),
                    estado="SELLADO" if item.get("success") else "FALLIDO",
                )
                for item in resultados
            ]
        except (httpx.ConnectError, httpx.TimeoutException):
            return [await self.sellar_hecho(p) for p in propuestas]

    # ── 4. Búsqueda (recuperación de contexto vivo) ───────────────────────────

    async def buscar_contexto(
        self,
        consulta: str,
        desde: Optional[float] = None,
        limite: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        POST /v1/facts/search
        Recupera contexto vivo y auditable para el planificador.
        Usa 'desde' (timestamp unix) para consultas temporales.
        """
        carga: Dict[str, Any] = {
            "project": PROYECTO_PERSIST,
            "query":   consulta,
            "limit":   limite,
        }
        if desde is not None:
            carga["as_of"] = desde
        try:
            r = await self._cliente.post("/v1/facts/search", json=carga)
            self._en_linea = True
            return r.json().get("facts", [])
        except (httpx.ConnectError, httpx.TimeoutException):
            logger.warning("◈ MEMBRANA_PERSISTENCIA: Búsqueda fuera de línea — contexto vacío.")
            return []

    # ── 5. Verificar (auditoría post-acción) ──────────────────────────────────

    async def verificar_hecho(self, id_hecho: Optional[str]) -> Dict[str, Any]:
        """
        GET /v1/facts/{id_hecho}/verify
        Confirma integridad de cadena hash tras una acción crítica.
        Llamar después de cada mutación P0.
        """
        if not id_hecho:
            return {"verified": False, "reason": "sin_id_hecho"}
        try:
            r = await self._cliente.get(f"/v1/facts/{id_hecho}/verify")
            self._en_linea = True
            return r.json()
        except (httpx.ConnectError, httpx.TimeoutException):
            return {"verified": False, "reason": "persistencia_fuera_de_linea"}

    # ── 6. Historial + Contaminación (forense) ────────────────────────────────

    async def contaminar_hecho(self, id_hecho: str, razon: str) -> Dict[str, Any]:
        """
        POST /v1/facts/{id_hecho}/taint
        Marca un hecho como comprometido y propaga contaminación causalmente.
        Usar cuando un resultado de herramienta se descubre incorrecto o malicioso.
        """
        try:
            r = await self._cliente.post(
                f"/v1/facts/{id_hecho}/taint",
                json={"reason": razon, "project": PROYECTO_PERSIST},
            )
            self._en_linea = True
            return r.json()
        except (httpx.ConnectError, httpx.TimeoutException):
            return {"contaminado": False, "razon": "persistencia_fuera_de_linea"}

    async def obtener_historial(self, sujeto: str) -> List[Dict[str, Any]]:
        """GET /v1/facts/{sujeto}/history — linaje causal para forense."""
        try:
            r = await self._cliente.get(f"/v1/facts/{sujeto}/history", params={"project": PROYECTO_PERSIST})
            return r.json().get("history", [])
        except (httpx.ConnectError, httpx.TimeoutException):
            return []

    # ── 7. Exportar (paquete de evidencia) ────────────────────────────────────

    async def exportar_proyecto(self) -> Dict[str, Any]:
        """
        GET /v1/projects/{project}/export
        Exportación completa: log de auditoría, cadena hash, prueba Merkle.
        """
        try:
            r = await self._cliente.get(f"/v1/projects/{PROYECTO_PERSIST}/export")
            self._en_linea = True
            return r.json()
        except (httpx.ConnectError, httpx.TimeoutException):
            return {"exportado": False, "razon": "persistencia_fuera_de_linea"}

    async def cerrar(self):
        await self._cliente.aclose()

    # ── Aliases EN (Puente) ──────────────────────────────────────────────────
    async def guard_write(self, proposal):
        return await self.custodiar_escritura(proposal)

    async def commit_fact(self, proposal, result=None):
        return await self.sellar_hecho(proposal, result)

    async def commit_batch(self, proposals):
        return await self.sellar_lote(proposals)

    async def search_context(self, query: str, as_of=None, limit: int = 10):
        return await self.buscar_contexto(query, as_of, limit)

    async def verify_fact(self, fact_id):
        return await self.verificar_hecho(fact_id)

    async def taint_fact(self, fact_id: str, reason: str):
        return await self.contaminar_hecho(fact_id, reason)

    async def get_history(self, subject: str):
        return await self.obtener_historial(subject)

    async def export_project(self):
        return await self.exportar_proyecto()

    async def aclose(self):
        return await self.cerrar()


# ── Escritor fallback local ───────────────────────────────────────────────────

def _escribir_fallback_local(carga: Dict[str, Any], huella_local: str):
    """
    Escribe en libro_mayor_enjambre.jsonl como fallback con huella SHA-256.
    Preserva auditabilidad cuando CORTEX Persist está inalcanzable.
    """
    directorio_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta_libro = os.path.join(directorio_base, "cortex/data/swarm_ledger.jsonl")
    entrada = {
        "marca_temporal": time.strftime("%Y-%m-%d %H:%M:%S"),
        "modo_persistencia": "FALLBACK_LOCAL",
        "huella": huella_local,
        "carga": carga,
    }
    with open(ruta_libro, "a") as f:
        f.write(json.dumps(entrada) + "\n")
    logger.info(f"◈ MEMBRANA_PERSISTENCIA: Fallback local escrito [{huella_local[:12]}]")


# ── Envoltorio síncrono (para llamadores no-async) ───────────────────────────

def custodiar_y_sellar_sync(
    sujeto: str,
    predicado: str,
    valor_objeto: Any,
    fuente: Literal["llm", "herramienta", "api", "humano"] = "herramienta",
    resultado: Optional[Any] = None,
    id_sesion: Optional[str] = None,
    metadatos: Optional[Dict[str, Any]] = None,
) -> ResultadoSellado:
    """
    Envoltorio síncrono para uso dentro de controladores no-async.
    Ejecuta el ciclo custodiar → sellar en un bucle de eventos aislado.
    """
    import asyncio

    propuesta = PropuestaHecho(
        sujeto=sujeto,
        predicado=predicado,
        valor_objeto=valor_objeto,
        fuente=fuente,
        id_sesion=id_sesion,
        metadatos=metadatos or {},
    )

    async def _ejecutar():
        membrana = MembranaPersistencia()
        try:
            guardia = await membrana.custodiar_escritura(propuesta)
            if not guardia.aprobado:
                logger.warning(f"◈ PERSISTENCIA: GUARDIA_BLOQUEADA [{guardia.razones}]")
                return ResultadoSellado(exito=False, id_hecho=None, huella=None, estado=f"BLOQUEADO:{guardia.razones}")
            sellado = await membrana.sellar_hecho(propuesta, resultado)
            logger.info(f"◈ PERSISTENCIA: SELLADO [{sellado.id_hecho or sellado.huella[:12]}] estado={sellado.estado}")
            return sellado
        finally:
            await membrana.cerrar()

    return asyncio.run(_ejecutar())


# EN alias
guard_and_commit_sync = custodiar_y_sellar_sync
