"""
Ouroboros EventStore — Append-only SQLite persistence.
Law Ω9: C5-REAL. Every write is a verified disk operation.
The serpent's memory survives restarts.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

from .types import Event, Generation, EvolutionAction


# ── Schema ────────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    aggregate_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    timestamp TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_aggregate_type ON events(aggregate_type);
CREATE INDEX IF NOT EXISTS idx_aggregate_id ON events(aggregate_id);
CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_agg_composite ON events(aggregate_type, aggregate_id);
"""


class EventStore:
    """
    Append-only event store backed by SQLite.
    Stateless recovery: replay() reconstructs full lineage.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            cortex_dir = Path.home() / ".cortex"
            cortex_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(cortex_dir / "ouroboros_events.db")

        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # ── Write ─────────────────────────────────────────────────────

    def append(self, event: Event) -> None:
        """Append a single event. Write-only, never mutate."""
        self._conn.execute(
            "INSERT INTO events (id, aggregate_type, aggregate_id, event_type, payload, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                event.id,
                event.aggregate_type,
                event.aggregate_id,
                event.event_type,
                json.dumps(event.payload),
                event.timestamp,
            ),
        )
        self._conn.commit()

    # ── Read ──────────────────────────────────────────────────────

    def replay(self, aggregate_id: str) -> list[Event]:
        """Replay all events for a given aggregate, ordered by timestamp."""
        cursor = self._conn.execute(
            "SELECT id, aggregate_type, aggregate_id, event_type, payload, timestamp "
            "FROM events WHERE aggregate_id = ? ORDER BY timestamp ASC",
            (aggregate_id,),
        )
        events = []
        for row in cursor.fetchall():
            events.append(
                Event(
                    id=row[0],
                    aggregate_type=row[1],
                    aggregate_id=row[2],
                    event_type=row[3],
                    payload=json.loads(row[4]),
                    timestamp=row[5],
                )
            )
        return events

    def get_lineage(self, session_id: str) -> list[Generation]:
        """Reconstruct generation lineage from events."""
        events = self.replay(session_id)
        generations: list[Generation] = []

        for ev in events:
            if ev.event_type == "evolution.generation.created":
                p = ev.payload
                generations.append(
                    Generation(
                        id=p.get("id", ""),
                        number=p.get("number", 0),
                        seed_hash=p.get("seed_hash", ""),
                        eval_score=p.get("eval_score", 0.0),
                        drift=p.get("drift", 1.0),
                        ontology_similarity=p.get("ontology_similarity", 0.0),
                        output_hash=p.get("output_hash", ""),
                        action=EvolutionAction[p.get("action", "CONTINUE")],
                        timestamp=ev.timestamp,
                    )
                )

        return generations

    def count(self, aggregate_id: Optional[str] = None) -> int:
        """Count events, optionally filtered by aggregate."""
        if aggregate_id:
            cursor = self._conn.execute(
                "SELECT COUNT(*) FROM events WHERE aggregate_id = ?",
                (aggregate_id,),
            )
        else:
            cursor = self._conn.execute("SELECT COUNT(*) FROM events")
        return cursor.fetchone()[0]

    # ── Lifecycle ─────────────────────────────────────────────────

    def close(self) -> None:
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
