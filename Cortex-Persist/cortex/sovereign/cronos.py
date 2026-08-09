import time
import math
import logging
from datetime import datetime
from sqlite3 import connect
from contextlib import contextmanager

from cortex.sovereign.memoria import AlmacenMemoria
# Configuración de CRONOS-Ω
DECAY_INTERVAL = 5.0  # Frecuencia de actualización (segundos)
BASE_LAMBDA = 0.005   # Tasa de decaimiento base (exergía)
STABILITY_THRESHOLD = 0.85 # Umbral para cristalización
DEATH_THRESHOLD = 0.10     # Umbral para pérdida total de señal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [CRONOS-Ω] %(levelname)s: %(message)s'
)
logger = logging.getLogger("cronos")

class DemonioCronos:
    """
    Motor termodinámico de CORTEX.
    Gobierna el decaimiento y la cristalización de los Hechos Soberanos.
    """

    def __init__(self):
        self.memoria = AlmacenMemoria()
        self.running = True

    def iniciar(self):
        logger.info("CRONOS-Ω Protocolo de Decaimiento Temporal: ACTIVO")
        try:
            while self.running:
                self.procesar_ciclo()
                time.sleep(DECAY_INTERVAL)
        except KeyboardInterrupt:
            logger.info("CRONOS-Ω Detenido por intervención humana.")

    def procesar_ciclo(self):
        hechos = self.memoria.obtener_hechos_activos()
        if not hechos:
            return

        # Simular entropía global (en producción vendría del GobernadorEstabilidad)
        # Para demo, usamos una fluctuación controlada
        entropia_global = 0.2 + (math.sin(time.time() / 100) * 0.1)

        for h in hechos:
            self.aplicar_decaimiento(h, entropia_global)

    def aplicar_decaimiento(self, hecho: dict, entropia_global: float):
        """Calcula y persiste el nuevo estado termodinámico del hecho."""
        id_hecho = hecho['id']
        exergia_og = hecho['exergia']
        estado_og = hecho['estado']
        
        # Ley de Decaimiento de CORTEX: E = E0 * e^(-lambda * t)
        # lambda aumenta con la entropía global
        lambda_t = BASE_LAMBDA * (1.0 + entropia_global + hecho['entropia'])
        
        nueva_exergia = exergia_og * math.exp(-lambda_t)
        nuevo_estado = estado_og

        # Lógica de Transición de Fase
        if nueva_exergia > STABILITY_THRESHOLD and hecho['entropia'] < 0.05:
            nuevo_estado = 'CRISTALIZADO'
            logger.info(f"Hecho {id_hecho} CRISTALIZADO (Exergía: {nueva_exergia:.4f})")
        elif nueva_exergia < DEATH_THRESHOLD:
            nuevo_estado = 'DECAIDO'
            logger.info(f"Hecho {id_hecho} DECAIDO — Pérdida de señal.")
        
        # Persistir cambios
        self._actualizar_db(id_hecho, nueva_exergia, nuevo_estado)

    def _actualizar_db(self, id_hecho: int, exergia: float, estado: str):
        with self.memoria.conexion_directa() as conn:
            conn.execute(
                "UPDATE hechos_soberanos SET exergia = ?, estado = ?, ultima_mutacion = ? WHERE id = ?",
                (exergia, estado, datetime.now(), id_hecho)
            )
            conn.commit()

# Extender AlmacenMemoria para conexión directa en el demonio
@contextmanager
def conexion_directa(self):
    conn = connect(self.ruta_bd)
    try:
        yield conn
    finally:
        conn.close()

AlmacenMemoria.conexion_directa = conexion_directa

if __name__ == "__main__":
    cronos = DemonioCronos()
    cronos.iniciar()
