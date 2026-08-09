"""
cortex.sovereign.gobernador
===========================
Gobernador PID Soberano — Homeostasis Dimensional y Estabilidad Estratégica.
Implementa §16 Homeostasis Soberana (Sintetología Agéntica v3.2).

Fusión de dos controladores en un único Gobernador con juicio:
  - GobernadorDimensional: regula la dimensionalidad VSA-SDM
  - GobernadorEstabilidad: gobierno estratégico multidominio (VERDE/ÁMBAR/ROJO)

"Un componente llamado guardián implica custodia activa, vigilancia con juicio.
 Guard es más frío, más mecánico, más genérico."
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Any

# ── Estructuras de Estado ─────────────────────────────────────────────────────

@dataclass
class EstadoPID:
    """Estado interno del controlador PID."""
    kp: float = 0.8
    ki: float = 0.05
    kd: float = 0.3
    punto_ajuste: float = 50.0
    medida: float = 50.0
    error: float = 0.0
    integral: float = 0.0
    derivada: float = 0.0
    salida: float = 50.0
    ultimo_instante: float = field(default_factory=time.time)
    dimension_vsa: int = 10000
    presion_semantica: float = 0.0
    presion_termodinamica: float = 0.0
    esta_saturado: bool = False


@dataclass
class MuestraSeñalSoberana:
    """Telemetría especializada para Control Estratégico (v3.0)."""
    ts: float
    dt: float
    # Señales estratégicas derivadas del Substrato VSA-SDM
    exergia: float          # [0.0, 1.0] Calidad de trabajo útil
    entropia: float         # [0.0, 1.0] Caos/Ruido en flujos de datos
    riesgo: float           # [0.0, 1.0] Probabilidad de detección o fallo
    impacto: float          # [0.0, 1.0] Alcance estratégico proyectado

    # Metadatos
    id_muestra: str = "pulso_s0p"


@dataclass
class EstadoGobernador:
    modo: str = "VERDE"  # VERDE | ÁMBAR | ROJO
    u: float = 0.0       # Intensidad de control (0=explorar, 1=explotar/bloqueo)
    integral_acc: float = 0.0       # Acumulador integral
    error_previo: float = 0.0
    inicio_modo_ts: float = field(default_factory=time.time)
    bloqueado: bool = False
    ultima_regla: str = "INICIO"


# ── GobernadorDimensional ─────────────────────────────────────────────────────

class GobernadorDimensional:
    """
    Controlador Soberano para Homeostasis Agéntica.
    Regula la 'D' (Dimensionalidad) del substrato VSA-SDM.

    pulso() = un latido del sistema. No un "tick" mecánico.
    """

    def __init__(self, kp=0.8, ki=0.05, kd=0.3):
        self.estado = EstadoPID(kp=kp, ki=ki, kd=kd)
        self.i_max = 30.0  # ZENÓN-1 Límite anti-saturación
        self.error_anterior = 0.0

    def pulso(self, entropia_medida: float, dt: float = 1.0) -> Dict[str, Any]:
        """
        Ejecuta un ciclo del controlador.
        Devuelve el estado completo para difusión telemétrica.
        """
        e = self.estado
        e.medida = entropia_medida

        # 1. Cálculo de error
        error = e.punto_ajuste - entropia_medida
        e.error = error

        # 2. Términos PID
        # P: Proporcional (Reactividad)
        termino_p = e.kp * error

        # I: Integral (Hechos Fantasma / Historial)
        e.integral += error * dt
        # ZENÓN-1 Anti-saturación
        if e.integral > self.i_max:
            e.integral = self.i_max
        if e.integral < -self.i_max:
            e.integral = -self.i_max
        termino_i = e.ki * e.integral

        # D: Derivada (KAIROS-Ω / Tendencia)
        derivada = (error - self.error_anterior) / dt if dt > 0 else 0.0
        e.derivada = derivada
        termino_d = e.kd * derivada

        # 3. Cálculo de salida [0 - 100]
        salida = 50.0 + termino_p + termino_i + termino_d
        e.salida = max(0.0, min(100.0, salida))
        e.esta_saturado = (e.salida >= 100.0 or e.salida <= 0.0)

        # 4. Mapeados físicos (Sintético — idealmente alimentado desde el kernel VSA)
        e.dimension_vsa = int(10000 * (e.salida / 50.0))
        e.presion_semantica = abs(error) / 50.0
        e.presion_termodinamica = e.salida / 100.0

        self.error_anterior = error
        e.ultimo_instante = time.time()

        return {
            "dimension_vsa": e.dimension_vsa,
            "presion_semantica": e.presion_semantica,
            "presion_termodinamica": e.presion_termodinamica,
            "error_gobernador": e.error,
            "kp": e.kp,
            "ki": e.ki,
            "kd": e.kd,
            "salida_pid": e.salida,
            "estado": "ESTABLE" if not e.esta_saturado else "SATURADO",
            "instante": e.ultimo_instante,
            # Aliases EN for API compatibility
            "vsa_dimension": e.dimension_vsa,
            "semantic_pressure": e.presion_semantica,
            "thermodynamic_pressure": e.presion_termodinamica,
            "governor_error": e.error,
            "pid_output": e.salida,
            "status": "STABLE" if not e.esta_saturado else "SATURATED",
            "time": e.ultimo_instante,
        }

    def fijar_objetivo(self, objetivo: float):
        """Establece el punto de ajuste del controlador."""
        self.estado.punto_ajuste = objetivo

    def actualizar_parametros(self, kp: float = None, ki: float = None, kd: float = None):
        """Actualiza coeficientes PID en caliente."""
        if kp is not None:
            self.estado.kp = kp
        if ki is not None:
            self.estado.ki = ki
        if kd is not None:
            self.estado.kd = kd

    # ── Aliases EN (Puente) ──────────────────────────────────────────────────
    def tick(self, measured_entropy: float, dt: float = 1.0) -> Dict[str, Any]:
        return self.pulso(measured_entropy, dt)

    def set_target(self, target: float):
        return self.fijar_objetivo(target)

    def update_params(self, kp=None, ki=None, kd=None):
        return self.actualizar_parametros(kp, ki, kd)


# ── GobernadorEstabilidad ─────────────────────────────────────────────────────

class GobernadorEstabilidad:
    """
    Gobernador Estratégico (v3.0).
    Motor de Decisión para Gobierno Soberano Multidominio.

    Modos: VERDE (expandir) → ÁMBAR (cautela) → ROJO (evasión)
    """

    def __init__(self):
        self.estado = EstadoGobernador()

        # Coeficientes PID (Tasa Estratégica)
        self.KP = 0.9
        self.KI = 0.02
        self.KD = 0.30
        self.I_MAX = 10.0

        # Umbrales de Máquina de Estados (Exergía Estratégica)
        self.U_AMBAR_ARRIBA = 0.60
        self.U_ROJO_ARRIBA  = 0.90
        self.U_ROJO_ABAJO   = 0.70  # Histéresis

        # Tiempos de Permanencia (Estabilidad)
        self.PERMANENCIA_AMBAR_MIN = 15.0
        self.PERMANENCIA_ROJO_MIN  = 60.0

        # Disparadores Duros (Lógica de Evasión)
        self.RIESGO_MAXIMO_TOLERADO   = 0.95
        self.ENTROPIA_MAXIMA_PERMITIDA = 0.85

    def calcular_error_exergia(self, m: MuestraSeñalSoberana) -> float:
        """
        Calcula una señal de error compuesta basada en señales estratégicas.
        Pesos:
        - 40%: Riesgo (Protección de seguridad)
        - 30%: Entropía (Pureza de información)
        - 20%: Exergía (Calidad de rendimiento)
        - 10%: Impacto (Presión sobre objetivo)
        """
        error_riesgo = m.riesgo
        error_entropia = m.entropia
        error_rendimiento = 1.0 - m.exergia

        # Error Compuesto (0.0 = Seguro, 1.0 = Crítico)
        e = (0.4 * error_riesgo) + (0.3 * error_entropia) + (0.2 * error_rendimiento) + (0.1 * m.impacto)
        return e

    def pulso(self, muestra: MuestraSeñalSoberana) -> Dict[str, Any]:
        """Iteración del Gobernador (Tasa Estratégica). Produce una Política Estratégica."""
        s = self.estado
        ahora = muestra.ts
        dt = muestra.dt

        # 1. Señal de Error Compuesta
        e = self.calcular_error_exergia(muestra)

        # 2. Actualización PID
        s.I = max(-self.I_MAX, min(self.I_MAX, s.I + e * dt))
        de = (e - s.error_previo) / dt if dt > 0 else 0
        s.error_previo = e

        u = max(0.0, min(1.0, self.KP * e + self.KI * s.I + self.KD * de))
        s.u = u

        # 3. Lógica de Evasión (Disparadores Duros)
        regla = "MANTENER_ESTADO"
        siguiente_modo = s.modo

        # Disparadores ROJO inmediatos (Cortacircuitos)
        if muestra.riesgo > self.RIESGO_MAXIMO_TOLERADO:
            siguiente_modo = "ROJO"
            regla = "EVASION_RIESGO_CRITICO"
        elif muestra.entropia > 0.95:
            siguiente_modo = "ROJO"
            regla = "EVASION_PICO_ENTROPIA"

        # Transiciones Estándar con Histéresis y Permanencia
        if siguiente_modo != "ROJO":
            tiempo_en_modo = ahora - s.inicio_modo_ts

            if s.modo == "VERDE":
                if u >= self.U_AMBAR_ARRIBA:
                    siguiente_modo = "ÁMBAR"
                    regla = "UMBRAL_PRESION_ARRIBA"

            elif s.modo == "ÁMBAR":
                if u >= self.U_ROJO_ARRIBA:
                    siguiente_modo = "ROJO"
                    regla = "UMBRAL_EVASION_CRITICA"
                elif u < 0.35 and tiempo_en_modo >= self.PERMANENCIA_AMBAR_MIN:
                    siguiente_modo = "VERDE"
                    regla = "RECUPERACION_ESTABILIDAD_ESTRATEGICA"

            elif s.modo == "ROJO":
                if u < self.U_ROJO_ABAJO and tiempo_en_modo >= self.PERMANENCIA_ROJO_MIN:
                    siguiente_modo = "ÁMBAR"
                    regla = "SALIDA_ENFRIAMIENTO_EVASION"

        # Aplicar Cambio de Modo
        if siguiente_modo != s.modo:
            s.modo = siguiente_modo
            s.inicio_modo_ts = ahora

        # 4. Generación de Política Estratégica
        politica = self._generar_politica(s.modo, u)

        return {
            "modo": s.modo,
            "u": u,
            "regla": regla,
            "politica": politica,
            "metricas": {
                "riesgo": muestra.riesgo,
                "exergia": muestra.exergia,
                "entropia": muestra.entropia,
                "impacto": muestra.impacto,
                "e": e,
            },
            "ts": ahora,
            "id_muestra": muestra.id_muestra,
            # Aliases EN for API compatibility
            "mode": s.modo.replace("VERDE", "GREEN").replace("ÁMBAR", "YELLOW").replace("ROJO", "RED"),
            "rule": regla,
            "policy": politica,
            "metrics": {
                "risk": muestra.riesgo,
                "exergy": muestra.exergia,
                "entropy": muestra.entropia,
                "impact": muestra.impacto,
                "e": e,
            },
            "sample_id": muestra.id_muestra,
        }

    def _generar_politica(self, modo: str, intensidad: float) -> Dict[str, Any]:
        """Genera parámetros de misión (Políticas) para el Enjambre Agéntico."""
        if modo == "ROJO":
            return {
                "mision": "bloqueo_evasion",
                "densidad_investigacion": 0.05,
                "presupuesto_herramientas": 0.0,
                "aprobacion_humana": True,
                "alcance_firma": "SOLO_LECTURA",
                # EN aliases
                "engagement_mission": "evasion_lockdown",
                "research_density": 0.05,
                "tool_budget": 0.0,
                "human_approval": True,
                "signing_scope": "READ_ONLY",
            }
        elif modo == "ÁMBAR":
            return {
                "mision": "prototipo_cauteloso",
                "densidad_investigacion": 0.5 - (intensidad * 0.3),
                "presupuesto_herramientas": 0.3,
                "aprobacion_humana": True,
                "alcance_firma": "RESTRINGIDO",
                # EN aliases
                "engagement_mission": "cautious_prototype",
                "research_density": 0.5 - (intensidad * 0.3),
                "tool_budget": 0.3,
                "human_approval": True,
                "signing_scope": "RESTRICTED",
            }
        else:  # VERDE
            return {
                "mision": "expansion_estrategica",
                "densidad_investigacion": 0.9,
                "presupuesto_herramientas": 1.0,
                "aprobacion_humana": False,
                "alcance_firma": "AGENCIA_TOTAL",
                # EN aliases
                "engagement_mission": "strategic_expansion",
                "research_density": 0.9,
                "tool_budget": 1.0,
                "human_approval": False,
                "signing_scope": "FULL_AGENTIC",
            }

    # ── Aliases EN (Puente) ──────────────────────────────────────────────────
    def tick(self, sample) -> Dict[str, Any]:
        """EN bridge: accepts SovereignSignalSample-compatible dict or MuestraSeñalSoberana."""
        if isinstance(sample, MuestraSeñalSoberana):
            return self.pulso(sample)
        # Accept legacy EN dataclass by converting
        return self.pulso(MuestraSeñalSoberana(
            ts=sample.ts, dt=sample.dt,
            exergia=sample.exergy, entropia=sample.entropy,
            riesgo=sample.risk, impacto=sample.impact,
            id_muestra=getattr(sample, 'sample_id', 'pulso_s0p'),
        ))

    def calculate_exergy_error(self, sample) -> float:
        if isinstance(sample, MuestraSeñalSoberana):
            return self.calcular_error_exergia(sample)
        return self.calcular_error_exergia(MuestraSeñalSoberana(
            ts=0, dt=0,
            exergia=sample.exergy, entropia=sample.entropy,
            riesgo=sample.risk, impacto=sample.impact,
        ))
