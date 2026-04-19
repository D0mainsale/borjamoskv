"""
cortex.sovereign.memoria
========================
Substrato de Memoria Soberana — Capa Ω4

Gestiona historial de conversaciones, estado efímero y embeddings VSA-SDM.
Usa SQLite para registros estructurados y JSON para fragmentos de contexto.

"Nombrar una variable gestor_de_confianza cuando piensas 'gestor de confianza'
 es instantáneo."

Confianza: C5-Estático
"""

import json
import math
import os
import sqlite3
import time
from datetime import datetime
from typing import List, Dict, Any


class AlmacenMemoria:
    """
    Substrato de Memoria Soberana.
    Asegura que cada interacción agéntica quede registrada para el LIBRO-MAYOR-C5.
    """

    def __init__(self, ruta_bd: str = None):
        if ruta_bd is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.ruta_bd = os.path.join(base, "server", "data", "soberano_c5.db")
        else:
            self.ruta_bd = ruta_bd
        self._inicializar_bd()

    def _inicializar_bd(self):
        os.makedirs(os.path.dirname(self.ruta_bd), exist_ok=True)
        with sqlite3.connect(self.ruta_bd) as conexion:
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS mensajes_soberanos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_sesion TEXT,
                    rol TEXT,
                    contenido TEXT,
                    marca_temporal DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS ejecuciones_agente (
                    id TEXT PRIMARY KEY,
                    estado TEXT,
                    pasos JSON,
                    ultima_actualizacion DATETIME
                )
            """)
            # Crear tabla de hechos soberanos (con linaje causal)
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS hechos_soberanos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_sesion TEXT DEFAULT 'default',
                    dominio TEXT NOT NULL,
                    contenido TEXT NOT NULL,
                    exergia REAL DEFAULT 0.0,
                    entropia REAL DEFAULT 0.0,
                    estado TEXT DEFAULT 'ACTIVO',
                    cristalizado INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ultima_mutacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS causalidad_soberana (
                    id_hijo INTEGER,
                    id_padre INTEGER,
                    FOREIGN KEY(id_hijo) REFERENCES hechos_soberanos(id),
                    FOREIGN KEY(id_padre) REFERENCES hechos_soberanos(id)
                )
            """)
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS operaciones_soberanas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT, -- STRIKE | RECON | EXTRACTION
                    objetivo TEXT,
                    estado TEXT DEFAULT 'INICIADO',
                    id_hecho_causal INTEGER,
                    marca_temporal DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(id_hecho_causal) REFERENCES hechos_soberanos(id)
                )
            """)
            # Tabla de Identidades Soberanas (Handles agents.archi)
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS identidades_soberanas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    handle TEXT UNIQUE NOT NULL,
                    id_sesion TEXT,
                    exergia_inicial REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conexion.commit()

    def registrar_mensaje(self, id_sesion: str, rol: str, contenido: str):
        """Registra un mensaje en el historial soberano."""
        query = """
            INSERT INTO mensajes_soberanos
            (id_sesion, rol, contenido, marca_temporal)
            VALUES (?, ?, ?, ?)
        """
        with sqlite3.connect(self.ruta_bd) as conn:
            conn.execute(query, (id_sesion, rol, contenido, time.time()))
            conn.commit()

    def obtener_historial(self, id_sesion: str,
                         limite: int = 50) -> List[Dict[str, str]]:
        """Obtiene la secuencia causal de mensajes de una sesión."""
        query = """
            SELECT rol, contenido FROM mensajes_soberanos
            WHERE id_sesion = ? ORDER BY marca_temporal ASC LIMIT ?
        """
        with sqlite3.connect(self.ruta_bd) as conexion:
            cursor = conexion.execute(query, (id_sesion, limite))
            return [
                {"role": f[0], "content": f[1]} for f in cursor.fetchall()
            ]

    def sellar_ejecucion(self, id_ejecucion: str, estado: str,
                        pasos: List[Dict[str, Any]]):
        """Sella una ejecución agéntica."""
        query = """
            INSERT OR REPLACE INTO ejecuciones_agente
            (id, estado, pasos, ultima_actualizacion)
            VALUES (?, ?, ?, ?)
        """
        with sqlite3.connect(self.ruta_bd) as conexion:
            params = (id_ejecucion, estado, json.dumps(pasos), datetime.now())
            conexion.execute(query, params)
            conexion.commit()

    def archivar_hecho(self, dominio: str, contenido: str,
                      exergia: float = 1.0, padres: List[int] = None):
        """Destila un pensamiento en un Hecho Soberano persistente."""
        with sqlite3.connect(self.ruta_bd) as conexion:
            query = """
                INSERT INTO hechos_soberanos (dominio, contenido, exergia)
                VALUES (?, ?, ?)
            """
            cursor = conexion.execute(query, (dominio, contenido, exergia))
            id_hecho = cursor.lastrowid
            if padres:
                for id_padre in padres:
                    conexion.execute(
                        "INSERT INTO causalidad_soberana (id_hijo, id_padre) "
                        "VALUES (?, ?)", (id_hecho, id_padre)
                    )
            conexion.commit()

    def obtener_hechos_activos(self, limite: int = 100) -> List[Dict[str, Any]]:
        """Recupera hechos que aún no han decaído totalmente."""
        with sqlite3.connect(self.ruta_bd) as conexion:
            query = """
                SELECT id, id_sesion, dominio, contenido, exergia,
                       entropia, estado, created_at
                FROM hechos_soberanos
                WHERE estado != 'DECAIDO'
                ORDER BY created_at DESC LIMIT ?
            """
            cursor = conexion.execute(query, (limite,))
            columnas = [desc[0] for desc in cursor.description]
            return [
                dict(zip(columnas, fila)) for fila in cursor.fetchall()
            ]

    def cristalizar_hecho(self, id_hecho: int):
        """Eleva un hecho al estado inmutable."""
        with sqlite3.connect(self.ruta_bd) as conexion:
            query = """
                UPDATE hechos_soberanos SET exergia = 1.0,
                estado = 'CRISTALIZADO', entropia = 0.0,
                ultima_mutacion = CURRENT_TIMESTAMP WHERE id = ?
            """
            conexion.execute(query, (id_hecho,))
            conexion.commit()

    def aniquilar_hecho(self, id_hecho: int):
        """Purga un hecho de la memoria activa (exergía = 0)."""
        with sqlite3.connect(self.ruta_bd) as conexion:
            query = """
                UPDATE hechos_soberanos SET estado = 'DECAIDO', exergia = 0.0,
                ultima_mutacion = CURRENT_TIMESTAMP WHERE id = ?
            """
            conexion.execute(query, (id_hecho,))
            conexion.commit()

    def obtener_linaje(self, id_hecho: int,
                       profundidad: int = 10) -> List[Dict[str, Any]]:
        """Reconstruye la cadena de causalidad reversa de un hecho."""
        with sqlite3.connect(self.ruta_bd) as conexion:
            query = """
                WITH RECURSIVE linaje(id_hijo, id_padre, nivel) AS (
                    SELECT id_hijo, id_padre, 0 FROM causalidad_soberana
                    WHERE id_hijo = ?
                    UNION ALL
                    SELECT c.id_hijo, c.id_padre, l.nivel + 1
                    FROM causalidad_soberana c
                    JOIN linaje l ON c.id_hijo = l.id_padre
                    WHERE l.nivel < ?
                )
                SELECT DISTINCT h.*, l.nivel FROM hechos_soberanos h
                JOIN linaje l ON h.id = l.id_padre
                ORDER BY l.nivel DESC
            """
            cursor = conexion.execute(query, (id_hecho, profundidad))
            columnas = [desc[0] for desc in cursor.description]
            return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]

    def registrar_operacion(self, tipo: str, objetivo: str,
                           id_hecho_causal: int):
        """Registra el inicio de una operación agéntica."""
        with sqlite3.connect(self.ruta_bd) as conexion:
            query = """
                INSERT INTO operaciones_soberanas
                (tipo, objetivo, id_hecho_causal) VALUES (?, ?, ?)
            """
            conexion.execute(query, (tipo, objetivo, id_hecho_causal))
            conexion.commit()

    def registrar_identidad(self, handle: str, id_sesion: str):
        """Reclama y registra una Identidad Soberana (handle)."""
        try:
            with sqlite3.connect(self.ruta_bd) as conn:
                conn.execute(
                    "INSERT INTO identidades_soberanas (handle, id_sesion) "
                    "VALUES (?, ?)",
                    (handle.lower().strip(), id_sesion)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def verificar_disponibilidad_handle(self, handle: str) -> bool:
        """Comprueba si un handle está libre para reclamar."""
        with sqlite3.connect(self.ruta_bd) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM identidades_soberanas WHERE handle = ?",
                (handle.lower().strip(),)
            )
            return cursor.fetchone() is None

    def obtener_metricas_homeostasis(self) -> Dict[str, Any]:
        """Calcula el vector de estado termodinámico del sistema."""
        with sqlite3.connect(self.ruta_bd) as conexion:
            # Exergía Media: Calidad del trabajo útil en hechos activos
            query_exg = """
                SELECT AVG(exergia) FROM hechos_soberanos WHERE cristalizado = 0
            """
            res_exg = conexion.execute(query_exg).fetchone()
            exg_media = res_exg[0] if res_exg[0] is not None else 1.0

            # Entropía - Dimensión 1: Hechos pendientes
            query_pent = """
                SELECT COUNT(*) FROM hechos_soberanos WHERE cristalizado = 0
            """
            res_pent = conexion.execute(query_pent).fetchone()
            pendientes = res_pent[0]

            # Entropía - Dimensión 2: Operaciones fallidas
            query_fail = """
                SELECT COUNT(*) FROM operaciones_soberanas
                WHERE estado = 'FALLIDO'
            """
            res_fail = conexion.execute(query_fail).fetchone()
            fallidas = res_fail[0]

            # Algoritmo de Homeostasis CORTEX-Ω
            entropia = math.log1p(pendientes) + (fallidas * 0.5)
            # Estabilidad: Margen de maniobra antes del colapso
            estabilidad = max(0.0, 1.0 - (entropia / 10.0))

            return {
                "exergia_media": round(exg_media, 3),
                "entropia_sistema": round(entropia, 3),
                "indice_estabilidad": round(estabilidad, 3),
                "hechos_pendientes": pendientes,
                "operaciones_fallidas": fallidas,
                "timestamp": datetime.now().isoformat()
            }

    # ── Aliases EN (Puente) ──────────────────────────────────────────────────
    def add_message(self, session_id: str, role: str, content: str):
        return self.registrar_mensaje(session_id, role, content)

    def get_history(self, session_id: str, limit: int = 50) -> List[Dict[str, str]]:
        return self.obtener_historial(session_id, limit)

    def record_run(self, run_id: str, status: str, steps: List[Dict[str, Any]]):
        return self.sellar_ejecucion(run_id, status, steps)

    def register_identity(self, handle: str, session_id: str) -> bool:
        return self.registrar_identidad(handle, session_id)

    def check_handle_availability(self, handle: str) -> bool:
        return self.verificar_disponibilidad_handle(handle)


if __name__ == "__main__":
    memoria = AlmacenMemoria()
    memoria.registrar_mensaje("test-id", "usuario", "Auditar niveles de exergía")
    print(memoria.obtener_historial("test-id"))
