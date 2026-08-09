"""
CORTEX AutoDream — Autonomous KI Consolidation Daemon.
"REM sleep for sovereign agents."

Law Ω2: Exergy-positive — prunes entropy, never adds it.
Law Ω9: C5-REAL. Every merge is a verified filesystem operation.

Triggers:
  1. Idle timer > 24h since last session
  2. Session count delta ≥ 5 since last dream
  3. Manual /anamnesis command (backward compatible)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Lazy import to avoid circular deps — EventStore is optional
try:
    from cortex.ouroboros.event_store import EventStore, Event
except ImportError:
    EventStore = None  # type: ignore
    Event = None  # type: ignore


# ── Configuration ──────────────────────────────────────────────────

IDLE_THRESHOLD_HOURS = 24
SESSION_DELTA_THRESHOLD = 5
STALE_DAYS = 30
DUPLICATE_JACCARD_THRESHOLD = 0.55
MAX_SUMMARY_TOKENS = 200  # Words for Jaccard comparison


# ── Types ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class KIProfile:
    """Snapshot of a Knowledge Item's metadata."""
    name: str
    path: Path
    summary: str
    last_accessed: str
    artifact_count: int
    title_tokens: frozenset[str] = frozenset()
    summary_tokens: frozenset[str] = frozenset()


@dataclass(frozen=True)
class StaleKI:
    """A KI that hasn't been accessed within the threshold."""
    ki: KIProfile
    days_stale: int
    recommendation: str  # "archive" | "review"


@dataclass(frozen=True)
class DuplicateGroup:
    """A group of KIs with high Jaccard similarity."""
    primary: KIProfile
    duplicates: tuple[KIProfile, ...]
    similarity: float
    merge_strategy: str  # "absorb_into_primary" | "create_unified"


@dataclass
class DreamReport:
    """Output of a single AutoDream cycle."""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    stale_kis: list[StaleKI] = field(default_factory=list)
    duplicate_groups: list[DuplicateGroup] = field(default_factory=list)
    actions_taken: list[str] = field(default_factory=list)
    ki_total: int = 0
    ki_scanned: int = 0
    exergy_reclaimed: float = 0.0  # Estimated bytes freed

    @property
    def has_findings(self) -> bool:
        return bool(self.stale_kis or self.duplicate_groups)


# ── Jaccard Similarity ─────────────────────────────────────────────

def _tokenize(text: str) -> frozenset[str]:
    """Normalize and tokenize text for Jaccard comparison."""
    # Remove common stop words for cleaner signal
    stop = {"the", "a", "an", "is", "are", "was", "were", "and", "or",
            "of", "to", "in", "for", "on", "with", "at", "by", "from",
            "this", "that", "it", "as", "be", "has", "had", "have"}
    words = text.lower().split()
    return frozenset(w for w in words if w not in stop and len(w) > 2)


def jaccard_similarity(a: frozenset[str], b: frozenset[str]) -> float:
    """Jaccard index: |A ∩ B| / |A ∪ B|. Returns 0.0 if both empty."""
    if not a and not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union else 0.0


# ── KI Scanner ─────────────────────────────────────────────────────

def scan_knowledge_dir(knowledge_dir: Path) -> list[KIProfile]:
    """
    Scan all KI directories for metadata.json.
    Returns list of KIProfile snapshots.
    """
    profiles: list[KIProfile] = []

    if not knowledge_dir.is_dir():
        return profiles

    for entry in sorted(knowledge_dir.iterdir()):
        if not entry.is_dir():
            continue
        meta_path = entry / "metadata.json"
        if not meta_path.exists():
            continue

        try:
            with open(meta_path, "r") as f:
                meta = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue

        summary = meta.get("summary", "")
        title = meta.get("title", entry.name)

        # Count artifacts
        artifacts_dir = entry / "artifacts"
        artifact_count = 0
        if artifacts_dir.is_dir():
            artifact_count = sum(
                1 for _ in artifacts_dir.rglob("*") if _.is_file()
            )

        profiles.append(KIProfile(
            name=entry.name,
            path=entry,
            summary=summary[:MAX_SUMMARY_TOKENS * 6],  # ~6 chars/word avg
            last_accessed=meta.get("last_accessed", ""),
            artifact_count=artifact_count,
            title_tokens=_tokenize(title),
            summary_tokens=_tokenize(summary),
        ))

    return profiles


# ── AutoDream Engine ───────────────────────────────────────────────

class AutoDream:
    """
    Autonomous KI consolidation daemon.
    Scans, detects staleness and duplicates, proposes actions.
    """

    def __init__(
        self,
        knowledge_dir: Optional[Path] = None,
        event_store=None,
        state_file: Optional[Path] = None,
    ):
        self.knowledge_dir = knowledge_dir or (
            Path.home() / ".gemini" / "antigravity" / "knowledge"
        )
        self.event_store = event_store
        self.state_file = state_file or (
            Path.home() / ".cortex" / "autodream_state.json"
        )
        self._state = self._load_state()

    # ── State Persistence ─────────────────────────────────────

    def _load_state(self) -> dict:
        """Load dream state (last run, session counter)."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "last_dream": None,
            "session_count_at_dream": 0,
            "total_dreams": 0,
        }

    def _save_state(self) -> None:
        """Persist dream state to disk."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self._state, f, indent=2)

    # ── Trigger Check ─────────────────────────────────────────

    def should_dream(self, current_session_count: int = 0) -> bool:
        """
        Check if AutoDream should trigger.
        Conditions (any):
          1. No dream ever run
          2. Idle > 24h since last dream
          3. Session delta ≥ 5 since last dream
        """
        if self._state["last_dream"] is None:
            return True

        # Time-based trigger
        try:
            last = datetime.fromisoformat(self._state["last_dream"])
            now = datetime.now(timezone.utc)
            hours_elapsed = (now - last).total_seconds() / 3600
            if hours_elapsed >= IDLE_THRESHOLD_HOURS:
                return True
        except (ValueError, TypeError):
            return True

        # Session-count trigger
        delta = current_session_count - self._state.get("session_count_at_dream", 0)
        if delta >= SESSION_DELTA_THRESHOLD:
            return True

        return False

    # ── Core Cycle ────────────────────────────────────────────

    def run_cycle(self, current_session_count: int = 0) -> DreamReport:
        """
        Execute one AutoDream consolidation cycle.
        1. Scan KIs
        2. Detect stale
        3. Detect duplicates
        4. Generate report
        5. Persist state + events
        """
        report = DreamReport()

        # Scan
        profiles = scan_knowledge_dir(self.knowledge_dir)
        report.ki_total = len(profiles)
        report.ki_scanned = len(profiles)

        if not profiles:
            return report

        # Detect stale
        report.stale_kis = self._detect_stale(profiles)

        # Detect duplicates
        report.duplicate_groups = self._detect_duplicates(profiles)

        # Estimate exergy reclaimed
        for stale in report.stale_kis:
            report.exergy_reclaimed += stale.ki.artifact_count * 1024  # est.
        for group in report.duplicate_groups:
            for dup in group.duplicates:
                report.exergy_reclaimed += dup.artifact_count * 1024

        # Update state
        self._state["last_dream"] = report.timestamp
        self._state["session_count_at_dream"] = current_session_count
        self._state["total_dreams"] = self._state.get("total_dreams", 0) + 1
        self._save_state()

        # Persist to EventStore
        self._emit_event(report)

        return report

    # ── Stale Detection ───────────────────────────────────────

    def _detect_stale(self, profiles: list[KIProfile]) -> list[StaleKI]:
        """Find KIs not accessed within STALE_DAYS threshold."""
        stale: list[StaleKI] = []
        now = datetime.now(timezone.utc)

        for ki in profiles:
            if not ki.last_accessed:
                continue
            try:
                accessed = datetime.fromisoformat(ki.last_accessed)
                # Handle timezone-naive timestamps
                if accessed.tzinfo is None:
                    accessed = accessed.replace(tzinfo=timezone.utc)
                days = (now - accessed).days
                if days >= STALE_DAYS:
                    stale.append(StaleKI(
                        ki=ki,
                        days_stale=days,
                        recommendation="archive" if days > 90 else "review",
                    ))
            except (ValueError, TypeError):
                continue

        return sorted(stale, key=lambda s: s.days_stale, reverse=True)

    # ── Duplicate Detection ───────────────────────────────────

    def _detect_duplicates(
        self, profiles: list[KIProfile]
    ) -> list[DuplicateGroup]:
        """
        Find KI pairs with Jaccard similarity > threshold.
        Groups by primary (highest artifact count).
        """
        n = len(profiles)
        if n < 2:
            return []

        # Compute pairwise similarity
        pairs: list[tuple[int, int, float]] = []
        for i in range(n):
            for j in range(i + 1, n):
                # Combine title + summary tokens for comparison
                tokens_i = profiles[i].title_tokens | profiles[i].summary_tokens
                tokens_j = profiles[j].title_tokens | profiles[j].summary_tokens
                sim = jaccard_similarity(tokens_i, tokens_j)
                if sim >= DUPLICATE_JACCARD_THRESHOLD:
                    pairs.append((i, j, sim))

        if not pairs:
            return []

        # Group by connected components (simple union-find)
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        for i, j, _ in pairs:
            union(i, j)

        # Build groups
        groups_map: dict[int, list[int]] = {}
        for idx in range(n):
            root = find(idx)
            groups_map.setdefault(root, []).append(idx)

        result: list[DuplicateGroup] = []
        for members in groups_map.values():
            if len(members) < 2:
                continue

            # Primary = highest artifact count
            member_profiles = [profiles[m] for m in members]
            member_profiles.sort(key=lambda p: p.artifact_count, reverse=True)

            primary = member_profiles[0]
            dups = tuple(member_profiles[1:])

            # Average similarity of pairs in this group
            group_sims = [
                s for i, j, s in pairs
                if i in members and j in members
            ]
            avg_sim = sum(group_sims) / len(group_sims) if group_sims else 0.0

            result.append(DuplicateGroup(
                primary=primary,
                duplicates=dups,
                similarity=round(avg_sim, 4),
                merge_strategy=(
                    "absorb_into_primary" if len(dups) == 1
                    else "create_unified"
                ),
            ))

        return sorted(result, key=lambda g: g.similarity, reverse=True)

    # ── Event Persistence ─────────────────────────────────────

    def _emit_event(self, report: DreamReport) -> None:
        """Persist dream cycle completion to EventStore."""
        if self.event_store is None or Event is None:
            return

        event = Event(
            aggregate_type="autodream",
            aggregate_id="cortex_knowledge",
            event_type="autodream.cycle.completed",
            payload={
                "ki_total": report.ki_total,
                "ki_scanned": report.ki_scanned,
                "stale_count": len(report.stale_kis),
                "duplicate_groups": len(report.duplicate_groups),
                "exergy_reclaimed": report.exergy_reclaimed,
                "total_dreams": self._state.get("total_dreams", 0),
            },
        )
        try:
            self.event_store.append(event)
        except Exception:
            pass  # Non-critical — dream still succeeded

    # ── Report Formatting ─────────────────────────────────────

    def format_report(self, report: DreamReport) -> str:
        """Generate human-readable dream report."""
        lines = [
            f"# AutoDream Report — {report.timestamp}",
            f"KIs scanned: {report.ki_scanned}/{report.ki_total}",
            f"Dreams total: {self._state.get('total_dreams', 0)}",
            "",
        ]

        if report.stale_kis:
            lines.append(f"## Stale KIs ({len(report.stale_kis)})")
            for s in report.stale_kis:
                lines.append(
                    f"- **{s.ki.name}** — {s.days_stale}d stale → {s.recommendation}"
                )
            lines.append("")

        if report.duplicate_groups:
            lines.append(f"## Duplicate Groups ({len(report.duplicate_groups)})")
            for g in report.duplicate_groups:
                dups = ", ".join(d.name for d in g.duplicates)
                lines.append(
                    f"- **{g.primary.name}** ← [{dups}] "
                    f"(sim={g.similarity:.2f}, strategy={g.merge_strategy})"
                )
            lines.append("")

        if report.exergy_reclaimed > 0:
            kb = report.exergy_reclaimed / 1024
            lines.append(f"Exergy reclaimable: ~{kb:.1f} KB")

        if not report.has_findings:
            lines.append("✓ Knowledge base is clean. No consolidation needed.")

        return "\n".join(lines)
