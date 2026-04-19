"""
cortex.agentic.memory
=====================
Sovereign Persistence Layer — Layer Ω4
[BRIDGE] This module now acts as a bridge to cortex.sovereign.sustrato_memoria.
Includes dual-lookup support for legacy data continuity.
"""

from typing import List, Dict, Any
from cortex.sovereign.sustrato_memoria import AlmacenMemoria, RUTA_DB as RUTA_SOBERANA
import sqlite3
import os

# Legacy DB Path
RUTA_LEGACY = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "server", "data", "cortex.agentic.db"
)

class MemoryStore:
    """
    Sovereign Memory Substrate.
    [BRIDGE] Proxies to cortex.sovereign.AlmacenMemoria.
    Supports dual-lookup to maintain Law Ω4 (Temporal Continuity).
    """

    def __init__(self, db_path: str = RUTA_SOBERANA):
        self._sovereign = AlmacenMemoria(ruta_db=db_path)
        self.legacy_path = RUTA_LEGACY

    def add_message(self, session_id: str, role: str, content: str):
        """Always write to the new sovereign substrate."""
        self._sovereign.agregar_mensaje(session_id, role, content)

    def get_history(self, session_id: str, limit: int = 50) -> List[Dict[str, str]]:
        """Dual-lookup: Combine legacy and sovereign history."""
        # 1. Get sovereign history
        results = self._sovereign.obtener_historial(session_id, limit)
        
        # 2. If limit not reached, check legacy
        if len(results) < limit and os.path.exists(self.legacy_path):
            try:
                with sqlite3.connect(self.legacy_path) as conn:
                    cursor = conn.execute(
                        "SELECT role, content FROM sovereign_messages "
                        "WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?",
                        (session_id, limit - len(results))
                    )
                    legacy_rows = [{"role": r[0], "content": r[1]} for r in cursor.fetchall()]
                    # Prepend legacy data
                    results = legacy_rows + results
            except Exception:
                pass # Silently fail for legacy integrity
                
        return results

    def record_run(self, run_id: str, status: str, steps: List[Dict[str, Any]]):
        """Always record to the new sovereign substrate."""
        self._sovereign.registrar_ejecucion(run_id, status, steps)
