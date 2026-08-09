"""
cortex.server.queue.py
===============
Industrial-grade SQLite-backed task queue for CORTEX.
Mandate: Sovereign, Local-first, Atomic.
"""

import json
import sqlite3
import time
import os
from contextlib import contextmanager
from typing import Any, Dict, Optional

class IndustrialQueue:
    def __init__(self, db_path: str = "server/data/queue.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._conn() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS work_queue (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type   TEXT NOT NULL,
                    payload     TEXT NOT NULL,          -- JSON
                    priority    INTEGER NOT NULL DEFAULT 100,
                    status      TEXT NOT NULL DEFAULT 'PENDING', -- PENDING | RUNNING | COMPLETED | FAILED
                    worker_id   TEXT,
                    attempts    INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 3,
                    created_at  REAL NOT NULL,
                    started_at  REAL,
                    finished_at REAL,
                    error_log   TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_queue_status_prio ON work_queue(status, priority, created_at)")
            conn.commit()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def enqueue(self, task_type: str, payload: Dict[str, Any], priority: int = 100, max_attempts: int = 3) -> int:
        """Add a new task to the queue."""
        now = time.time()
        with self._conn() as conn:
            cur = conn.execute("""
                INSERT INTO work_queue (task_type, payload, priority, max_attempts, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (task_type, json.dumps(payload), priority, max_attempts, now))
            return cur.lastrowid

    def claim(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """
        Atomically claim the highest priority PENDING task.
        Uses BEGIN IMMEDIATE to prevent race conditions in SQLite.
        """
        now = time.time()
        with self._conn() as conn:
            # Atomic lock
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("""
                SELECT * FROM work_queue
                WHERE status = 'PENDING'
                ORDER BY priority ASC, created_at ASC
                LIMIT 1
            """).fetchone()

            if not row:
                return None

            task_id = row["id"]
            conn.execute("""
                UPDATE work_queue
                SET status = 'RUNNING', worker_id = ?, started_at = ?, attempts = attempts + 1
                WHERE id = ?
            """, (worker_id, now, task_id))
            
            # Refresh row data
            updated = conn.execute("SELECT * FROM work_queue WHERE id = ?", (task_id,)).fetchone()
            return dict(updated)

    def complete(self, task_id: int, result: Optional[Dict[str, Any]] = None):
        """Mark task as COMPLETED."""
        now = time.time()
        with self._conn() as conn:
            conn.execute("""
                UPDATE work_queue
                SET status = 'COMPLETED', finished_at = ?, error_log = ?
                WHERE id = ?
            """, (now, json.dumps(result) if result else None, task_id))

    def fail(self, task_id: int, error_msg: str):
        """Mark task as FAILED or PENDING (for retry)."""
        now = time.time()
        with self._conn() as conn:
            row = conn.execute("SELECT attempts, max_attempts FROM work_queue WHERE id = ?", (task_id,)).fetchone()
            if not row: return

            if row["attempts"] < row["max_attempts"]:
                # Retry: set back to PENDING
                conn.execute("""
                    UPDATE work_queue
                    SET status = 'PENDING', error_log = ?, worker_id = NULL
                    WHERE id = ?
                """, (error_msg, task_id))
            else:
                # Permanent failure
                conn.execute("""
                    UPDATE work_queue
                    SET status = 'FAILED', finished_at = ?, error_log = ?
                    WHERE id = ?
                """, (now, error_msg, task_id))

    def get_stats(self) -> Dict[str, int]:
        """Aggregate stats for telemetry."""
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM work_queue
                GROUP BY status
            """).fetchall()
            stats = {row["status"]: row["count"] for row in rows}
            # Ensure all statuses exist in dict
            for s in ["PENDING", "RUNNING", "COMPLETED", "FAILED"]:
                if s not in stats: stats[s] = 0
            return stats

if __name__ == "__main__":
    # Self-test
    q = IndustrialQueue("scratch/test_queue.db")
    tid = q.enqueue("TEST_TASK", {"data": "debug_info"})
    print(f"Enqueued: {tid}")
    task = q.claim("worker_01")
    print(f"Claimed: {task['id']} by {task['worker_id']}")
    q.complete(tid, {"status": "success"})
    print(f"Stats: {q.get_stats()}")
