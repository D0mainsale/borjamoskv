"""Acceptance Criteria tree — MECE decomposition with atomicity detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Iterator

MAX_DEPTH: int = 5


class ACStatus(Enum):
    """Acceptance criteria node status."""

    PENDING = auto()
    IN_PROGRESS = auto()
    PASSED = auto()
    FAILED = auto()
    SKIPPED = auto()


@dataclass
class ACNode:
    """
    Single node in the Acceptance Criteria tree.
    Leaf nodes with ≤2 files are atomic (no further decomposition).
    """

    id: str
    description: str
    files_touched: list[str] = field(default_factory=list)
    children: list["ACNode"] = field(default_factory=list)
    status: ACStatus = ACStatus.PENDING
    depth: int = 0
    parent_id: str | None = None

    @property
    def is_atomic(self) -> bool:
        """1-2 files = atomic, skip further decomposition."""
        return len(self.files_touched) <= 2 and len(self.children) == 0

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    @property
    def can_decompose(self) -> bool:
        """Can only decompose if below MAX_DEPTH and not atomic."""
        return self.depth < MAX_DEPTH and not self.is_atomic

    def add_child(self, child: "ACNode") -> None:
        """Add child node with depth enforcement."""
        if self.depth >= MAX_DEPTH:
            raise ValueError(
                f"Cannot decompose beyond MAX_DEPTH={MAX_DEPTH}"
            )
        child.depth = self.depth + 1
        child.parent_id = self.id
        self.children.append(child)

    def leaves(self) -> Iterator["ACNode"]:
        """Yield all leaf nodes (executable units)."""
        if self.is_leaf:
            yield self
        else:
            for child in self.children:
                yield from child.leaves()

    def all_passed(self) -> bool:
        """Check if all leaves have passed."""
        return all(leaf.status == ACStatus.PASSED for leaf in self.leaves())

    def count_by_status(self) -> dict[ACStatus, int]:
        """Count leaves by status."""
        counts: dict[ACStatus, int] = {s: 0 for s in ACStatus}
        for leaf in self.leaves():
            counts[leaf.status] += 1
        return counts


@dataclass
class ACTree:
    """Root container for the acceptance criteria tree."""

    root: ACNode
    seed_hash: str  # Links back to Seed.content_hash

    @property
    def total_leaves(self) -> int:
        return sum(1 for _ in self.root.leaves())

    @property
    def progress(self) -> float:
        """Fraction of leaves that passed."""
        total = self.total_leaves
        if total == 0:
            return 0.0
        passed = sum(
            1 for leaf in self.root.leaves() if leaf.status == ACStatus.PASSED
        )
        return passed / total
