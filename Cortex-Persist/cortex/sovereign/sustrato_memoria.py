"""
cortex.sovereign.sustrato_memoria
===============================
Capa de Persistencia Soberana — Nivel Ω4

Gestiona el historial de conversaciones, el estado efímero y los metadatos de
VSA-SDM. Utiliza SQLite para registros estructurados y JSON para fragmentos.

Confianza: C5-Static
"""

import sqlite3
import json
import os
from typing import List, Dict, Any
from datetime import datetime

# Ruta de la base de datos (relativa a la raíz del proyecto)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_DB = os.path.join(_BASE_DIR, "server", "data", "cortex_soberano.db")


class AlmacenMemoria:
    """
    Sustrato de Memoria Soberana.
    Garantiza que cada interacción sea registrada para el LEDGER-C5.
    """

    def __init__(self, ruta_db: str = RUTA_DB):
        self.ruta_db = ruta_db
        self._inicializar_db()

    def _inicializar_db(self):
        """Prepara el esquema de base de datos soberana."""
        os.makedirs(os.path.dirname(self.ruta_db), exist_ok=True)
        with sqlite3.connect(self.ruta_db) as conn:
            # Mensajes soberanos
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mensajes_soberanos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_sesion TEXT,
                    rol TEXT,
                    contenido TEXT,
                    marca_tiempo DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Ejecuciones de agentes (Runs)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ejecuciones_agente (
                    id TEXT PRIMARY KEY,
                    estado TEXT,
                    pasos JSON,
                    ultima_actualizacion DATETIME
                )
            """)
            conn.commit()

    def agregar_mensaje(self, id_sesion: str, rol: str, contenido: str):
        """Añade un mensaje al historial de la sesión."""
        with sqlite3.connect(self.ruta_db) as conn:
            conn.execute(
                "INSERT INTO mensajes_soberanos (id_sesion, rol, contenido) "
                "VALUES (?, ?, ?)",
                (id_sesion, rol, contenido)
            )
            conn.commit()

    def obtener_historial(
        self, id_sesion: str, limite: int = 50
    ) -> List[Dict[str, str]]:
        """Recupera el historial de mensajes de una sesión."""
        with sqlite3.connect(self.ruta_db) as conn:
            cursor = conn.execute(
                "SELECT rol, contenido FROM mensajes_soberanos "
                "WHERE id_sesion = ? ORDER BY marca_tiempo ASC LIMIT ?",
                (id_sesion, limite)
            )
            return [
                {"role": fila[0], "content": fila[1]}
                for fila in cursor.fetchall()
            ]

    def registrar_ejecucion(
        self, id_ejecucion: str, estado: str, pasos: List[Dict[str, Any]]
    ):
        """Registra o actualiza una traza de ejecución de agente."""
        with sqlite3.connect(self.ruta_db) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO ejecuciones_agente "
                "(id, estado, pasos, ultima_actualizacion) "
                "VALUES (?, ?, ?, ?)",
                (id_ejecucion, estado, json.dumps(pasos), datetime.now())
            )
            conn.commit()


if __name__ == "__main__":
    # Prueba de humo
    # mem = AlmacenMemoria()
    # mem.agregar_mensaje("test-id", "usuario", "Auditar niveles de exergía")
    # print(mem.obtener_historial("test-id"))
    pass
