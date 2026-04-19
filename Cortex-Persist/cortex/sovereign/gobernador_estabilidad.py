"""
cortex.sovereign.gobernador_estabilidad
======================================
Gobernador Estratégico de Estabilidad (v3.0).
Motor de decisión para la gobernanza soberana multi-dominio.

Implementa el control PID estratégico y la máquina de estados
de evasión/expansión.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class MuestraSeñalSoberana:
    """Telemetría especializada para el Control Estratégico (v3.0)."""
    ts: float
    dt: float
    # Señales estratégicas derivadas del sustrato VSA-SDM
    exergia: float         # [0.0, 1.0] Calidad del trabajo útil
    entropia: float        # [0.0, 1.0] Caos/Ruido en los datos
    riesgo: float          # [0.0, 1.0] Probabilidad de detección
    impacto: float         # [0.0, 1.0] Alcance estratégico proyectado

    id_muestra: str = "pulso_s0p"


@dataclass
class EstadoGobernador:
    """Contenedor de estado para el Gobernador."""
    modo: str = "VERDE"  # VERDE | AMARILLO | ROJO
    u: float = 0.0       # Intensidad de control
    integral_accumulator: float = 0.0  # Acumulador integral
    error_prev: float = 0.0  # Para la derivada
    marca_inicio_modo: float = field(default_factory=time.time)
    enganchado: bool = False
    ultima_regla: str = "INIT"


class GobernadorEstabilidadAgente:
    """
    Gobernador Estratégico de CORTEX (v3.0).
    Regula la política misional basada en la exergía y el riesgo sistémico.
    """

    def __init__(self):
        self.estado = EstadoGobernador()

        # Coeficientes PID (Tasa Estratégica)
        self.KP = 0.9
        self.KI = 0.02
        self.KD = 0.30
        self.I_MAX = 10.0

        # Umbrales de la Máquina de Estados (Exergía Estratégica)
        self.T_AMARILLO_SUBIDA = 0.60
        self.T_ROJO_SUBIDA = 0.90
        self.T_ROJO_BAJADA = 0.70  # Histéresis

        # Tiempos de Permanencia (Estabilidad)
        self.PERMANENCIA_AMARILLO_MIN = 15.0
        self.PERMANENCIA_ROJO_MIN = 60.0

        # Disparadores Críticos (Lógica de Evasión)
        self.RIESGO_MAX_TOLERADO = 0.95  # ROJO inmediato si se excede
        self.ENTROPIA_MAX_PERMITIDA = 0.85  # AMARILLO inmediato si se excede

    def calcular_error_exergia(self, s: MuestraSeñalSoberana) -> float:
        """
        Calcula una señal de error compuesta basada en señales estratégicas.
        Pesos:
        - 40%: Riesgo (Protección de seguridad)
        - 30%: Entropía (Pureza de la información)
        - 20%: Exergía (Calidad del rendimiento)
        - 10%: Impacto (Presión sobre el objetivo)
        """
        riesgo_err = s.riesgo
        entropia_err = s.entropia
        rendimiento_err = 1.0 - s.exergia

        # Error Compuesto (0.0 = Seguro, 1.0 = Crítico)
        e = (
            (0.4 * riesgo_err) +
            (0.3 * entropia_err) +
            (0.2 * rendimiento_err) +
            (0.1 * s.impacto)
        )
        return e

    def procesar(self, muestra: MuestraSeñalSoberana) -> Dict[str, Any]:
        """Iteración del Gobernador (Tasa Estratégica). Produce Politica."""
        s = self.estado
        ahora = muestra.ts
        dt = muestra.dt

        # 1. Señal de Error Compuesta
        e = self.calcular_error_exergia(muestra)

        # 2. Actualización PID
        s.integral_accumulator = max(
            -self.I_MAX,
            min(self.I_MAX, s.integral_accumulator + e * dt)
        )
        de = (e - s.error_prev) / dt if dt > 0 else 0
        s.error_prev = e

        u = max(0.0, min(
            1.0,
            self.KP * e + self.KI * s.integral_accumulator + self.KD * de
        ))
        s.u = u

        # 3. Lógica de Evasión (Disparadores de Hardware/Estrategia)
        regla = "KEEP_STATE"
        proximo_modo = s.modo

        # Disparadores de ROJO Inmediato (Circuit Breakers)
        if muestra.riesgo > self.RIESGO_MAX_TOLERADO:
            proximo_modo = "ROJO"
            regla = "EVASION_RIESGO_CRITICO"
        elif muestra.entropia > 0.95:
            proximo_modo = "ROJO"
            regla = "EVASION_PICO_ENTROPIA"

        # Transiciones Estándar con Histéresis y Permanencia
        if proximo_modo != "ROJO":
            tiempo_en_modo = ahora - s.marca_inicio_modo

            if s.modo == "VERDE":
                if u >= self.T_AMARILLO_SUBIDA:
                    proximo_modo = "AMARILLO"
                    regla = "PRESION_UMBRAL_SUBIDA"

            elif s.modo == "AMARILLO":
                if u >= self.T_ROJO_SUBIDA:
                    proximo_modo = "ROJO"
                    regla = "UMBRAL_EVASION_CRITICA"
                elif u < 0.35 and (
                    tiempo_en_modo >= self.PERMANENCIA_AMARILLO_MIN
                ):
                    proximo_modo = "VERDE"
                    regla = "RECUPERACION_ESTABILIDAD_ESTRATEGICA"

            elif s.modo == "ROJO":
                if (
                    u < self.T_ROJO_BAJADA and
                    tiempo_en_modo >= self.PERMANENCIA_ROJO_MIN
                ):
                    proximo_modo = "AMARILLO"
                    regla = "SALIDA_ENFRIAMIENTO_EVASION"

        # Aplicar Cambio de Modo
        if proximo_modo != s.modo:
            s.modo = proximo_modo
            s.marca_inicio_modo = ahora

        # 4. Generación de Política Estratégica
        politica = self._generar_politica(s.modo, u)

        return {
            "mode": s.modo,
            "u": u,
            "rule": regla,
            "policy": politica,
            "metrics": {
                "risk": muestra.riesgo,
                "exergy": muestra.exergia,
                "entropy": muestra.entropia,
                "impact": muestra.impacto,
                "e": e
            },
            "ts": ahora,
            "sample_id": muestra.id_muestra
        }

    def _generar_politica(self, modo: str, intensidad: float) -> Dict[str, Any]:
        """
        Genera parámetros de misión (Políticas) para el Enjambre Agéntico.
        """
        if modo == "ROJO":
            return {
                "engagement_mission": "evasion_lockdown",
                "research_density": 0.05,
                "tool_budget": 0.0,
                "human_approval": True,
                "signing_scope": "READ_ONLY"
            }
        if modo == "AMARILLO":
            return {
                "engagement_mission": "cautious_prototype",
                "research_density": 0.5 - (intensidad * 0.3),
                "tool_budget": 0.3,
                "human_approval": True,
                "signing_scope": "RESTRICTED"
            }
        # default VERDE
        return {
            "engagement_mission": "strategic_expansion",
            "research_density": 0.9,
            "tool_budget": 1.0,
            "human_approval": False,
            "signing_scope": "FULL_AGENTIC"
        }
