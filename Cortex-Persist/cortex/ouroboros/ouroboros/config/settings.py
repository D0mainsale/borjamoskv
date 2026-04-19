"""Pydantic Settings — env var loading, configurable models, paths."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class OuroborosSettings(BaseSettings):
    """Unified configuration for the Ouroboros engine."""

    model_config = {"env_prefix": "OUROBOROS_", "env_file": ".env"}

    # ── LLM Models (configurable per Consensus) ───────────
    frugal_model: str = Field(
        default="claude-3-5-haiku-20241022",
        description="Cheapest tier model",
    )
    standard_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Standard tier model",
    )
    frontier_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Frontier tier model",
    )
    # Consensus multi-model voting
    consensus_models: list[str] = Field(
        default=[
            "gpt-4o",
            "claude-sonnet-4-20250514",
            "gemini-2.5-pro",
        ],
        description="Models for Stage 3 consensus voting",
    )

    # ── Persistence ───────────────────────────────────────
    db_path: Path = Field(
        default=Path(".ouroboros/events.db"),
        description="SQLite event store path (project-root relative)",
    )
    checkpoint_interval_seconds: int = Field(
        default=300, description="Periodic checkpoint interval (5 min)"
    )

    # ── Thresholds ────────────────────────────────────────
    ambiguity_gate: float = Field(
        default=0.2, description="Max ambiguity to proceed to Seed"
    )
    drift_threshold: float = Field(
        default=0.3, description="Max acceptable drift"
    )
    convergence_threshold: float = Field(
        default=0.95, description="Similarity for convergence"
    )
    max_generations: int = Field(
        default=30, description="Max evolutionary generations"
    )
    semantic_approval_threshold: float = Field(
        default=0.8, description="Stage 2 semantic score for approval"
    )

    # ── PAL Router ────────────────────────────────────────
    escalation_failures: int = Field(
        default=2, description="Consecutive failures to escalate tier"
    )
    downgrade_successes: int = Field(
        default=5, description="Consecutive successes to downgrade tier"
    )
    jaccard_similarity_threshold: float = Field(
        default=0.80, description="Jaccard threshold for tier inheritance"
    )

    # ── Autodidact Integration ────────────────────────────
    thermo_yield_threshold: float = Field(
        default=0.0,
        description="Minimum net yield for JIT branch to proceed (Ω3)",
    )
    jit_timeout_ms: int = Field(
        default=50, description="JIT sandbox timeout in milliseconds"
    )


# Singleton
settings = OuroborosSettings()
