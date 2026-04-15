"""
cortex_agentic.agent_capabilities
==================================
Sovereign Capability Manifest — Layer Ω0

Every CORTEX agent inherits this capability substrate by default.
No agent is instantiated without these 7 expert domains.

Confidence: C5-Static (structural invariant — not empirical claim)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import FrozenSet


# ─── Capability taxonomy ──────────────────────────────────────────────────────

class CapabilityDomain(Enum):
    WEB_SEARCH       = auto()   # Búsqueda web — serp, crawl, scrape
    CODE_EXECUTION   = auto()   # Ejecución de código — Python, bash, sandboxed
    FILE_ACCESS      = auto()   # Acceso a ficheros — read/write/watch, git
    API_INTEGRATION  = auto()   # APIs — REST, GraphQL, gRPC, webhooks
    COMMS_CALENDAR   = auto()   # Correo · calendario · bases de datos
    BROWSER_GUI      = auto()   # Navegadores y entornos GUI — Playwright, headless
    AGENT_MEMORY     = auto()   # VSA-SDM — sovereign vector memory substrate


# ─── Manifest ─────────────────────────────────────────────────────────────────

_ALL_DOMAINS: FrozenSet[CapabilityDomain] = frozenset(CapabilityDomain)


@dataclass(frozen=True)
class AgentCapabilityManifest:
    """
    Immutable capability declaration for every CORTEX agent.

    Rule: an agent MUST declare at minimum one domain. The base
    CortexAgent class always injects the full sovereign set.
    """
    domains: FrozenSet[CapabilityDomain] = field(
        default_factory=lambda: _ALL_DOMAINS
    )

    # ── Introspection helpers ──────────────────────────────────────────────────

    def has(self, domain: CapabilityDomain) -> bool:
        return domain in self.domains

    def summary(self) -> list[str]:
        labels = {
            CapabilityDomain.WEB_SEARCH:      "búsqueda web",
            CapabilityDomain.CODE_EXECUTION:  "ejecución de código",
            CapabilityDomain.FILE_ACCESS:     "acceso a ficheros",
            CapabilityDomain.API_INTEGRATION: "APIs",
            CapabilityDomain.COMMS_CALENDAR:  "correo · calendario · bases de datos",
            CapabilityDomain.BROWSER_GUI:     "navegadores y entornos GUI",
            CapabilityDomain.AGENT_MEMORY:    "VSA-SDM sovereign memory",
        }
        return [labels[d] for d in sorted(self.domains, key=lambda d: d.value)]

    def __repr__(self) -> str:
        return f"AgentCapabilityManifest(domains={len(self.domains)}/7)"


# ─── Sovereign default — applied to all agents automatically ──────────────────

SOVEREIGN_MANIFEST = AgentCapabilityManifest(domains=_ALL_DOMAINS)
"""
All 7 domains active. This is the invariant baseline for every CORTEX agent.
Override only in sandboxed / restricted execution contexts.
"""
