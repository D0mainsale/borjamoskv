#!/usr/bin/env python3
"""
ralph_parallel.py — Ralph Wickham · Parallel Worker Pool v2.0
──────────────────────────────────────────────────────────────
Cada worker:
  1. Adquiere el advisory lock exclusivo sobre tasks.md.lock
  2. Lee tasks.md, elige la primera tarea PENDING
  3. La marca IN_PROGRESS (atómico) y libera el lock
  4. Ejecuta la tarea (sin holding el lock — paralelismo real)
  5. Re-adquiere el lock, persiste resultado (DONE | BLOCKED)
  6. Libera el lock → siguiente worker puede reclamar

Mecanismo de claim:
  - fcntl.flock (POSIX advisory lock) sobre `.ralph.lock`
  - Atomic: read → claim → write → release — todo dentro del lock
  - Ejecución fuera del lock → N workers en paralelo real

Configuración env:
  RALPH_WORKERS   = número de workers paralelos (default: 3)
  RALPH_MAX_ITER  = iteraciones máx por worker (default: 20)
  RALPH_MAX_RETRIES = intentos antes de bloquear (default: 3)
  RALPH_TIMEOUT   = segundos por tarea (default: 120)
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import subprocess
import sys
import textwrap
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Optional

# ─── Config ──────────────────────────────────────────────────────────────────

TASKS_FILE     = Path("tasks.md")
LEDGER_FILE    = Path("ralph_ledger.jsonl")
LOCK_FILE      = Path(".ralph.lock")
LOG_DIR        = Path("logs")
NUM_WORKERS    = int(os.getenv("RALPH_WORKERS",     "3"))
MAX_ITER       = int(os.getenv("RALPH_MAX_ITER",    "20"))
MAX_RETRIES    = int(os.getenv("RALPH_MAX_RETRIES", "3"))
TASK_TIMEOUT   = int(os.getenv("RALPH_TIMEOUT",     "120"))

# ANSI Industrial Noir
_R   = "\033[0m"
_B   = "\033[1m"
_DIM = "\033[2m"
_BLU = "\033[38;5;33m"
_GRN = "\033[38;5;46m"
_RED = "\033[38;5;196m"
_YEL = "\033[38;5;226m"
_CYN = "\033[38;5;51m"
_MGN = "\033[38;5;201m"

_print_lock = Lock()   # serialise stdout from multiple threads

def _log(worker_id: int, msg: str) -> None:
    with _print_lock:
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        color = [_BLU, _CYN, _MGN, _YEL, _GRN][worker_id % 5]
        print(f"{_DIM}[{ts}]{_R} {color}{_B}W{worker_id:02d}{_R} {msg}")


# ─── Data model ──────────────────────────────────────────────────────────────

@dataclass
class Task:
    raw:    str
    label:  str
    status: str   # pending | in_progress | done | blocked
    notes:  str = ""

    @classmethod
    def from_line(cls, line: str) -> "Task":
        stripped = line.strip()
        if stripped.startswith("- [x]"):
            status = "done"
        elif stripped.startswith("- [/]"):
            status = "in_progress"
        elif stripped.startswith("- [ ]"):
            status = "pending"
        else:
            status = "unknown"
        label = re.sub(r"^- \[.\] ", "", stripped).strip()
        return cls(raw=stripped, label=label, status=status)

    def to_md(self) -> str:
        marker = {"done": "[x]", "blocked": "[B]", "in_progress": "[/]", "pending": "[ ]"}.get(self.status, "[ ]")
        base = f"- {marker} {self.label}"
        if self.notes:
            base += f"  <!-- {self.notes} -->"
        return base


@dataclass
class LedgerEntry:
    worker_id:  int
    task_id:    str
    task_label: str
    status:     str        # success | failure | blocked
    iteration:  int
    retry:      int
    timestamp:  str
    duration_s: float
    stdout:     str = ""
    stderr:     str = ""
    exit_code:  Optional[int] = None


# ─── Ledger (thread-safe) ─────────────────────────────────────────────────────

_ledger_lock = Lock()

def _append_ledger(entry: LedgerEntry) -> None:
    with _ledger_lock:
        LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LEDGER_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")


# ─── Atomic claim (the core of parallel safety) ───────────────────────────────

class TaskStore:
    """
    Single point of mutation for tasks.md.
    All methods acquire the OS-level advisory lock before R/W.
    """

    def __init__(self, path: Path, lock_path: Path) -> None:
        self.path      = path
        self.lock_path = lock_path
        self._fh       = None   # lock file handle (persistent across calls)

    # ── internal lock helpers ──

    def _acquire(self) -> None:
        self._fh = self.lock_path.open("a+")
        fcntl.flock(self._fh, fcntl.LOCK_EX)   # blocking exclusive lock

    def _release(self) -> None:
        fcntl.flock(self._fh, fcntl.LOCK_UN)
        self._fh.close()
        self._fh = None

    # ── public API ──

    def claim_next(self, worker_id: int) -> Optional[Task]:
        """
        Atomically:
          read tasks.md → find first PENDING → mark IN_PROGRESS → write → return task.
        Returns None if queue is empty.
        """
        self._acquire()
        try:
            text  = self.path.read_text(encoding="utf-8")
            lines = text.splitlines(keepends=True)

            for i, line in enumerate(lines):
                stripped = line.strip()
                if not stripped.startswith("- [ ]"):
                    continue

                task = Task.from_line(stripped)
                task.status = "in_progress"

                # Replace exactly this line
                original_line = line
                new_line      = line.replace(stripped, task.to_md(), 1)
                lines[i]      = new_line
                task.raw      = stripped   # keep original for later replace

                self.path.write_text("".join(lines), encoding="utf-8")
                return task

            return None  # nothing to claim
        finally:
            self._release()

    def persist_result(
        self,
        task:       Task,
        new_status: str,
        note:       str = "",
    ) -> None:
        """Atomically update task status after execution."""
        self._acquire()
        try:
            text  = self.path.read_text(encoding="utf-8")
            # The task is currently [/] in file; build both patterns for safety
            in_progress_line = task.to_md()   # current: [/]
            task.status = new_status
            task.notes  = note
            final_line  = task.to_md()

            updated = text.replace(in_progress_line, final_line, 1)

            # Append to ## Progreso section
            ts   = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            icon = "✅" if new_status == "done" else "🔴" if new_status == "blocked" else "🔄"
            log_entry = f"\n- {icon} `{ts}` W{worker_id:02d} — {task.label[:80]}"
            if "<!-- Ralph documenta aquí cada ciclo completado -->" in updated:
                updated = updated.replace(
                    "<!-- Ralph documenta aquí cada ciclo completado -->",
                    f"<!-- Ralph documenta aquí cada ciclo completado -->{log_entry}",
                )

            self.path.write_text(updated, encoding="utf-8")
        finally:
            self._release()

    def is_queue_empty(self) -> bool:
        self._acquire()
        try:
            text = self.path.read_text(encoding="utf-8")
        finally:
            self._release()
        return not any(
            l.strip().startswith("- [ ]") or l.strip().startswith("- [/]")
            for l in text.splitlines()
        )


# ─── Shell executor ───────────────────────────────────────────────────────────

def _extract_command(label: str) -> Optional[str]:
    m = re.search(r"`([^`]+)`", label)
    if m:
        return m.group(1)
    if label.lower().startswith(("run:", "ejecutar:", "exec:")):
        cmd = re.sub(r"^[^:]+:\s*", "", label).strip()
        return cmd or None
    return None


def _execute_shell(cmd: str) -> tuple[bool, str, str, int]:
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=TASK_TIMEOUT,
            cwd=str(TASKS_FILE.parent),
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return False, "", f"TIMEOUT after {TASK_TIMEOUT}s", -1
    except Exception as exc:
        return False, "", str(exc), -1


# ─── Worker ───────────────────────────────────────────────────────────────────

def worker(worker_id: int, store: TaskStore) -> dict:
    """
    A single parallel worker. Loops until:
      - queue empty (no PENDING tasks)
      - MAX_ITER reached
    """
    stats    = {"done": 0, "blocked": 0, "errors": 0, "iterations": 0}
    retry_map: dict[str, int] = {}

    _log(worker_id, "→ BOOT")

    for iteration in range(1, MAX_ITER + 1):

        # 1. Atomic claim
        task = store.claim_next(worker_id)
        if task is None:
            _log(worker_id, f"{_DIM}queue empty — exiting{_R}")
            break

        retries = retry_map.get(task.label, 0)
        _log(worker_id, f"[{iteration:02d}] CLAIMED: {task.label[:60]}")

        # 2. Guard: block if retries exhausted (claim anyway to remove from pending)
        if retries >= MAX_RETRIES:
            note = f"blocked after {MAX_RETRIES} retries"
            store.persist_result(task, "blocked", note)
            _append_ledger(LedgerEntry(
                worker_id=worker_id, task_id=f"W{worker_id}T{iteration:03d}",
                task_label=task.label, status="blocked",
                iteration=iteration, retry=retries,
                timestamp=datetime.now(timezone.utc).isoformat(),
                duration_s=0.0,
            ))
            _log(worker_id, f"{_YEL}⚠ BLOCKED — {note}{_R}")
            stats["blocked"] += 1
            stats["iterations"] += 1
            continue

        # 3. Execute (no lock held during execution — true parallelism)
        t0  = time.perf_counter()
        cmd = _extract_command(task.label)

        if cmd:
            success, stdout, stderr, exit_code = _execute_shell(cmd)
        else:
            success   = True
            stdout    = "Advisory — no shell command."
            stderr    = ""
            exit_code = 0

        duration = round(time.perf_counter() - t0, 3)

        # 4. Persist result (atomic)
        if success:
            store.persist_result(task, "done")
            stats["done"] += 1
            _log(worker_id, f"{_GRN}✓ DONE{_R} ({duration:.2f}s) {task.label[:50]}")
        else:
            retries += 1
            retry_map[task.label] = retries
            if retries >= MAX_RETRIES:
                note = f"failed {retries}x — exit={exit_code}"
                store.persist_result(task, "blocked", note)
                stats["blocked"] += 1
                _log(worker_id, f"{_RED}✗ BLOCKED{_R} {note}")
            else:
                note = f"retry {retries}/{MAX_RETRIES}"
                # Revert to pending so another worker (or this one) can retry
                task.status = "in_progress"  # persist_result will read current [/]
                store.persist_result(task, "pending", note)
                stats["errors"] += 1
                _log(worker_id, f"{_YEL}↺ RETRY {retries}/{MAX_RETRIES}{_R}")

        # 5. Ledger
        _append_ledger(LedgerEntry(
            worker_id=worker_id, task_id=f"W{worker_id}T{iteration:03d}",
            task_label=task.label,
            status="success" if success else "failure",
            iteration=iteration, retry=retries - (0 if success else 1),
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_s=duration,
            stdout=stdout[:2000],
            stderr=stderr[:500],
            exit_code=exit_code,
        ))
        stats["iterations"] += 1

    else:
        _log(worker_id, f"{_YEL}⚠ MAX_ITER reached{_R}")

    return stats


# ─── Entry point ─────────────────────────────────────────────────────────────

def _banner() -> None:
    print(f"\n{_B}{_BLU}┌{'─'*62}┐")
    print(f"│{'  RALPH WICKHAM — Parallel Worker Pool v2.0':^62}│")
    print(f"│{'  CORTEX-Persist · Industrial Noir 2026':^62}│")
    print(f"│{'  Workers: ' + str(NUM_WORKERS) + '  ·  MaxIter/worker: ' + str(MAX_ITER):^62}│")
    print(f"└{'─'*62}┘{_R}\n")


def run() -> None:
    _banner()
    LOG_DIR.mkdir(exist_ok=True)
    LOCK_FILE.touch(exist_ok=True)

    store = TaskStore(TASKS_FILE, LOCK_FILE)

    if store.is_queue_empty():
        print(f"{_GRN}{_B}✅  Queue already empty.{_R}\n")
        return

    all_stats: list[dict] = []

    with ThreadPoolExecutor(max_workers=NUM_WORKERS, thread_name_prefix="ralph") as pool:
        futures = {
            pool.submit(worker, wid, store): wid
            for wid in range(NUM_WORKERS)
        }
        for fut in as_completed(futures):
            wid = futures[fut]
            try:
                all_stats.append(fut.result())
            except Exception as exc:
                _log(wid, f"{_RED}FATAL: {exc}{_R}")

    # ── Aggregate summary ─────────────────────────────────────────────────────
    total = {k: sum(s.get(k, 0) for s in all_stats) for k in ("iterations", "done", "blocked", "errors")}

    print(f"\n{_B}{'─'*64}")
    print(f"  RALPH PARALLEL SESSION SUMMARY  ({NUM_WORKERS} workers)")
    print(f"{'─'*64}{_R}")
    print(f"  Iterations : {total['iterations']}")
    print(f"  Done       : {_GRN}{total['done']}{_R}")
    print(f"  Blocked    : {_YEL}{total['blocked']}{_R}")
    print(f"  Errors     : {_RED}{total['errors']}{_R}")
    print(f"  Ledger     : {LEDGER_FILE}")
    print(f"{_B}{'─'*64}{_R}\n")


if __name__ == "__main__":
    # Allow: python ralph_parallel.py [--workers N]
    import argparse
    p = argparse.ArgumentParser(description="Ralph Wickham Parallel Runner v2.0")
    p.add_argument("--workers", type=int, default=NUM_WORKERS, help="Number of parallel workers")
    p.add_argument("--max-iter", type=int, default=MAX_ITER,   help="Max iterations per worker")
    args = p.parse_args()
    NUM_WORKERS = args.workers
    MAX_ITER    = args.max_iter
    run()
