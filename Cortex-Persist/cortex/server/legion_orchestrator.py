import time
import random
from typing import Dict, Any


class LegionAgent:
    """Representación de una entidad élite de la Legion."""
    def __init__(self, agent_id: str, role: str, task: str):
        self.agent_id = agent_id
        self.role = role  # AUDIT, STRIKE, ANALYST
        self.task = task
        self.exergy = 0.95 + (random.random() * 0.04)
        self.progress = 0.0
        self.status = "ACTIVE"
        self.start_time = time.time()

    def update(self):
        """Simula progresión de tarea."""
        if self.progress < 1.0:
            self.progress += 0.01 * random.random()
        else:
            self.status = "COMPLETED"

        # Jitter de exergía basado en entropía simulada
        self.exergy = max(
            0.8,
            min(1.0, self.exergy + (random.uniform(-0.01, 0.01)))
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.agent_id,
            "role": self.role,
            "task": self.task,
            "exergy": round(self.exergy, 4),
            "progress": round(self.progress, 2),
            "status": self.status,
            "uptime": round(time.time() - self.start_time, 2)
        }


class SwarmVirtualizer:
    """
    Gestor del Enjambre de agentes del AOS orientado a escalado masivo (10k).
    Implementa virtualización: solo los 'Elite' tienen objetos pesados.
    """
    def __init__(self, total_agents: int = 10000):
        self.total_count = total_agents
        self.elites: Dict[str, LegionAgent] = {}
        self.swarm_stats = {
            "exergy_avg": 0.984,
            "progress_avg": 0.45,
            "role_distribution": {"AUDIT": 0.4, "STRIKE": 0.3, "ANALYST": 0.3}
        }
        self._initialize_elites()

    def _initialize_elites(self):
        """Genera los 12 agentes élite con telemetría detallada."""
        roles = ["AUDIT", "STRIKE", "ANALYST"]
        tasks = [
            "Escaneando vectores L0",
            "Preparando Strike Ouroboros",
            "Analizando flujo de exergía",
            "Verificando integridad del Ledger",
            "Sincronizando con Moskv-Nexus"
        ]

        for i in range(12):
            a_id = f"ELITE-{i:02d}"
            role = roles[i % len(roles)]
            task = tasks[i % len(tasks)]
            self.elites[a_id] = LegionAgent(a_id, role, task)

    def update_swarm(self):
        """Ciclo de vida de la Legion (Virtualizado)."""
        # 1. Update Elites
        for agent in self.elites.values():
            agent.update()

        # 2. Update Virtual Swarm Stats (Brownian motion style)
        self.swarm_stats["exergy_avg"] = max(
            0.9,
            min(1.0, self.swarm_stats["exergy_avg"] + random.uniform(-0.005, 0.005))
        )
        self.swarm_stats["progress_avg"] = (
            self.swarm_stats["progress_avg"] + 0.001
        ) % 1.0

    def get_telemetry(self) -> Dict[str, Any]:
        self.update_swarm()
        return {
            "total_count": self.total_count,
            "elites": [a.to_dict() for a in self.elites.values()],
            "stats": self.swarm_stats,
            "timestamp": time.time()
        }

    def get_swarm_status(self):
        """Compatibility method for existing proxy calls."""
        tel = self.get_telemetry()
        # Return a simplified list if the frontend still expects it,
        # but we'll update the frontend to handle the full object.
        return tel


# Singleton instance for the proxy
LEGION_COMMANDER = SwarmVirtualizer()
