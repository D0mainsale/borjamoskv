"""
cortex.sovereign.puente
=======================
Puente Dual-Interface — Capa de Interoperabilidad

"Puedes mantener una interfaz pública en inglés y una implementación
 interna en tu idioma. Igual que una API tiene contratos externos
 pero lógica interna libre."

Este módulo re-exporta TODAS las clases soberanas con alias en inglés
para la capa API HTTP y consumidores externos.

Uso:
    from cortex.sovereign.puente import DimensionalityGovernor, CortexRuntime
    # These are the SAME classes, just with English names.
"""

# ── Gobernador ────────────────────────────────────────────────────
from .gobernador import (
    GobernadorDimensional as DimensionalityGovernor,
    GobernadorEstabilidad as AgentStabilityGovernor,
    EstadoPID as PIDState,
    MuestraSeñalSoberana as SovereignSignalSample,
    EstadoGobernador as GovernorState,
)

# ── Memoria ───────────────────────────────────────────────────────
from .memoria import (
    AlmacenMemoria as MemoryStore,
)

# ── Membrana ──────────────────────────────────────────────────────
from .membrana import (
    MembranaPersistencia as PersistMembrane,
    PropuestaHecho as FactProposal,
    ResultadoGuardia as GuardResult,
    ResultadoSellado as CommitResult,
    custodiar_y_sellar_sync as guard_and_commit_sync,
)

# ── Forja ─────────────────────────────────────────────────────────
from .forja import (
    Forja as ToolRegistry,
)

# ── Planificador ──────────────────────────────────────────────────
from .planificador import (
    Planificador as CortexPlanner,
)

# ── Motor ─────────────────────────────────────────────────────────
from .motor import (
    MotorSoberano as CortexRuntime,
    EstadoEjecucion as RunStatus,
    PasoEjecucion as RunStep,
)

# ── Ganchos ───────────────────────────────────────────────────────
from .ganchos import (
    RegistroGanchos as HookRegistry,
    EventoGancho as HookEvent,
    ResultadoGancho as HookResult,
    AccionGancho as HookAction,
    obtener_registro as get_registry,
    ejecucion_herramienta_con_ganchos as hooked_tool_execution,
)

# ── Re-export soberano (ES preferred) ────────────────────────────
from .gobernador import GobernadorDimensional, GobernadorEstabilidad
from .memoria import AlmacenMemoria
from .membrana import MembranaPersistencia, PropuestaHecho
from .forja import Forja
from .planificador import Planificador
from .motor import MotorSoberano
from .ganchos import RegistroGanchos
