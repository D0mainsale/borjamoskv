"""
cortex.sovereign.gobernador_homeostasis
======================================
Gobernador de Dimensionalidad Basado en PID (DDG).
Implementa la §16 Homeostasis Soberana (Sintetología Agéntica v3.2).

Controla la 'dimensionalidad' agéntica (resolución de contexto) para mantener 
el equilibrio frente a la entropía medida del sistema.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class EstadoPID:
    kp: float = 0.8
    ki: float = 0.05
    kd: float = 0.3
    punto_consigna: float = 50.0  # Setpoint
    medido: float = 50.0
    error: float = 0.0
    integral: float = 0.0
    derivada: float = 0.0
    salida: float = 50.0
    ultima_activacion: float = field(default_factory=time.time)
    dimension_vsa: int = 10000
    presion_semantica: float = 0.0
    presion_termodinamica: float = 0.0
    esta_saturado: bool = False


class GobernadorDimensional:
    """
    Controlador Soberano para Homeostasis Agéntica.
    Regula la 'D' (Dimensionalidad) del sustrato VSA-SDM.
    """
    def __init__(self, kp=0.8, ki=0.05, kd=0.3):
        self.estado = EstadoPID(kp=kp, ki=ki, kd=kd)
        self.limite_integral = 30.0  # Límite Anti-windup ZENÓN-1
        self.ultimo_error = 0.0

    def procesar(self, entropia_medida: float, dt: float = 1.0) -> Dict[str, Any]:
        """
        Ejecuta un ciclo del controlador.
        Retorna el estado completo para la transmisión de telemetría.
        """
        e = self.estado
        e.medido = entropia_medida

        # 1. Cálculo del error
        error = e.punto_consigna - entropia_medida
        e.error = error

        # 2. Términos PID
        # P: Proportional (Reactividad)
        termino_p = e.kp * error

        # I: Integral (Hechos Fantasma / Historial)
        e.integral += error * dt
        # Protocolo ZENÓN-1: Anti-windup
        if e.integral > self.limite_integral:
            e.integral = self.limite_integral
        if e.integral < -self.limite_integral:
            e.integral = -self.limite_integral
        termino_i = e.ki * e.integral

        # D: Derivativo (KAIROS-Ω / Tendencia)
        derivada = (error - self.ultimo_error) / dt if dt > 0 else 0.0
        e.derivada = derivada
        termino_d = e.kd * derivada

        # 3. Cálculo de salida [0 - 100]
        salida = 50.0 + termino_p + termino_i + termino_d
        e.salida = max(0.0, min(100.0, salida))
        e.esta_saturado = (e.salida >= 100.0 or e.salida <= 0.0)

        # 4. Mapeos físicos (Sustrato VSA)
        e.dimension_vsa = int(10000 * (e.salida / 50.0))
        e.presion_semantica = abs(error) / 50.0
        e.presion_termodinamica = e.salida / 100.0

        self.ultimo_error = error
        e.ultima_activacion = time.time()

        return {
            "vsa_dimension": e.dimension_vsa,
            "semantic_pressure": e.presion_semantica,
            "thermodynamic_pressure": e.presion_termodinamica,
            "governor_error": e.error,
            "kp": e.kp,
            "ki": e.ki,
            "kd": e.kd,
            "pid_output": e.salida,
            "status": "ESTABLE" if not e.esta_saturado else "SATURADO",
            "time": e.ultima_activacion
        }

    def obtener_telemetria_homeostasis(self) -> Dict[str, Any]:
        """
        Deriva métricas termodinámicas reales basadas en el estado del gobernador.
        [Ley Termodinámica Ω2 Enforced]
        """
        e = self.estado
        
        # Entropía: Fracción de error acumulado y reactividad
        entropia = (abs(e.error) / e.punto_consigna) if e.punto_consigna > 0 else 1.0
        entropia = max(0.01, min(0.99, entropia))
        
        # Exergía: Potencial de trabajo útil (1 - Entropía) * Salida PID
        exergia = (1.0 - entropia) * (e.salida / 100.0)
        exergia = max(0.05, min(1.0, exergia))
        
        # Estabilidad: Inversa de la derivada del error (KAIROS-Ω)
        estabilidad = 1.0 - min(1.0, abs(e.derivada) / 10.0)
        
        return {
            "exergia": exergia,
            "entropia": entropia,
            "estabilidad": estabilidad,
            "dimensionalidad": e.dimension_vsa,
            "presion": e.presion_termodinamica,
            "timestamp": time.time()
        }

    def definir_objetivo(self, objetivo: float):
        self.estado.punto_consigna = objetivo

    def actualizar_parametros(
        self, kp: float = None, ki: float = None, kd: float = None
    ):
        if kp is not None:
            self.estado.kp = kp
        if ki is not None:
            self.estado.ki = ki
        if kd is not None:
            self.estado.kd = kd
