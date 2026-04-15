"""Immutable Seed — frozen Pydantic model. The specification never changes; the path adapts."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, model_validator


class Seed(BaseModel):
    """
    Immutable specification crystallized from the Socratic interview.
    Once generated, the Seed is frozen — all evolution happens around it.
    """

    model_config = {"frozen": True}

    goal: str = Field(..., min_length=10, description="Primary objective")
    constraints: list[str] = Field(
        default_factory=list, description="Hard constraints"
    )
    success_criteria: list[str] = Field(
        default_factory=list, description="Measurable acceptance criteria"
    )
    ontology: dict[str, Any] = Field(
        default_factory=dict, description="Domain concept graph"
    )
    ambiguity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Must be ≤ 0.2 to pass gate"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    content_hash: str = Field(default="", description="SHA-256 integrity hash")

    @model_validator(mode="after")
    def _compute_hash(self) -> "Seed":
        """Compute content hash from goal + constraints + criteria + ontology."""
        payload = json.dumps(
            {
                "goal": self.goal,
                "constraints": self.constraints,
                "success_criteria": self.success_criteria,
                "ontology": self.ontology,
            },
            sort_keys=True,
        )
        digest = hashlib.sha256(payload.encode()).hexdigest()
        # Bypass frozen to set hash (only during construction)
        object.__setattr__(self, "content_hash", digest)
        return self

    @classmethod
    def from_interview(
        cls,
        goal: str,
        constraints: list[str],
        success_criteria: list[str],
        ontology: dict[str, Any],
        ambiguity_score: float,
    ) -> "Seed":
        """Factory: create Seed from interview results."""
        return cls(
            goal=goal,
            constraints=constraints,
            success_criteria=success_criteria,
            ontology=ontology,
            ambiguity_score=ambiguity_score,
        )

    def verify_integrity(self) -> bool:
        """Verify SHA-256 hash hasn't been tampered with."""
        payload = json.dumps(
            {
                "goal": self.goal,
                "constraints": self.constraints,
                "success_criteria": self.success_criteria,
                "ontology": self.ontology,
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest() == self.content_hash
