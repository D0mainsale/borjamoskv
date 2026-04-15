#!/usr/bin/env python3
"""
ralph.py — Técnica Ralph Wickham · Production Runner v1.0
──────────────────────────────────────────────────────────
Loop autónomo secuencial:
  1. Lee tasks.md
  2. Toma la primera tarea [ ] o [/]
  3. La ejecuta (shell o handler interno)
  4. Registra resultado en ralph_ledger.jsonl
  5. Actualiza tasks.md
  6. Repite hasta cola vacía o límite de iteraciones

Seguridad:
  - MAX_ITERATIONS: límite de ciclos por sesión
  - MAX_RETRIES: bloqueo automático tras N fallos consecutivos
  - Timeout configurable por tarea
  - Nunca inventa tareas nuevas
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─── Config ─────────────────────────────────────────────────────────────────

TASKS_FILE    = Path("tasks.md")
LEDGER_FILE   = Path("ralph_ledger.jsonl")
LOG_DIR       = Path("logs")
MAX_ITERATIONS = int(os.getenv("RALPH_MAX_ITER", "20"))
MAX_RETRIES    = int(os.getenv("RALPH_MAX_RETRIES", "3"))
TASK_TIMEOUT   = int(os.getenv("RALPH_TIMEOUT", "120"))   # seconds

# ANSI Industrial Noir palette
_R  = "\033[0m"
_B  = "\033[1m"
_DIM = "\033[2m"
_BLU = "\033[38;5;33m"
_GRN = "\033[38;5;46m"
_RED = "\033[38;5;196m"
_YEL = "\033[38;5;226m"
_CYN = "\033[38;5;51m"

# ─── Data model ─────────────────────────────────────────────────────────────

@dataclass
class Task:
    raw: str           # original markdown line
    label: str         # human text stripped of markers
    status: str        # "pending" | "in_progress" | "done" | "blocked"
    retries: int = 0
    notes: str = ""

    @classmethod
    def from_line(cls, line: str) -> "Task":
        if line.startswith("- [x]"):
            status = "done"
        elif line.startswith("- [/]"):
            status = "in_progress"
        elif line.startswith("- [ ]"):
            status = "pending"
        else:
            status = "unknown"
        label = re.sub(r"^- \[.\] ", "", line).strip()
        return cls(raw=line, label=label, status=status)

    def to_md(self) -> str:
        marker = {"done": "[x]", "blocked": "[B]", "in_progress": "[/]", "pending": "[ ]"}.get(self.status, "[ ]")
        base = f"- {marker} {self.label}"
        if self.notes:
            base += f"  <!-- {self.notes} -->"
        return base


@dataclass
class LedgerEntry:
    task_id: str
    task_label: str
    status: str           # "success" | "failure" | "blocked"
    iteration: int
    retry: int
    timestamp: str
    duration_s: float
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None


# ─── Ledger ──────────────────────────────────────────────────────────────────

def _append_ledger(entry: LedgerEntry) -> None:
    LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")


# ─── tasks.md parser / writer ────────────────────────────────────────────────

def _read_tasks_raw() -> str:
    if not TASKS_FILE.exists():
        raise FileNotFoundError(f"{TASKS_FILE} not found — create it first.")
    return TASKS_FILE.read_text(encoding="utf-8")


def _parse_pending(text: str) -> list[Task]:
    tasks = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- [ ]") or stripped.startswith("- [/]"):
            tasks.append(Task.from_line(stripped))
    return tasks


def _update_tasks_file(original: str, task: Task, new_status: str, note: str = "") -> None:
    task.status = new_status
    task.notes  = note
    new_line    = task.to_md()
    updated     = original.replace(task.raw, new_line, 1)

    # Append to ## Progreso section
    ts   = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    icon = "✅" if new_status == "done" else "🔴" if new_status == "blocked" else "🔄"
    log_entry = f"\n- {icon} `{ts}` — {task.label[:80]}"
    if "## Progreso" in updated:
        updated = updated.replace(
            "<!-- Ralph documenta aquí cada ciclo completado -->",
            f"<!-- Ralph documenta aquí cada ciclo completado -->{log_entry}"
        )

    TASKS_FILE.write_text(updated, encoding="utf-8")


# ─── Shell executor ──────────────────────────────────────────────────────────

def _extract_command(label: str) -> Optional[str]:
    """Extract shell command from backtick markers: Run: `cmd` or Fix: `cmd`."""
    m = re.search(r"`([^`]+)`", label)
    if m:
        return m.group(1)
    # If label starts with "Run:" take the rest
    if label.lower().startswith(("run:", "ejecutar:", "exec:")):
        cmd = re.sub(r"^[^:]+:\s*", "", label).strip()
        return cmd if cmd else None
    return None


def _execute_shell(cmd: str) -> tuple[bool, str, str, int]:
    """Run a shell command. Returns (success, stdout, stderr, exit_code)."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=TASK_TIMEOUT,
            cwd=str(TASKS_FILE.parent),
        )
        success = result.returncode == 0
        return success, result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return False, "", f"TIMEOUT after {TASK_TIMEOUT}s", -1
    except Exception as exc:
        return False, "", str(exc), -1


# ─── Retry tracking (in-memory, per session) ─────────────────────────────────

_retry_map: dict[str, int] = {}


def _get_retries(task: Task) -> int:
    return _retry_map.get(task.label, 0)


def _increment_retries(task: Task) -> int:
    count = _retry_map.get(task.label, 0) + 1
    _retry_map[task.label] = count
    return count


# ─── Display ─────────────────────────────────────────────────────────────────

def _banner() -> None:
    print(f"\n{_B}{_BLU}┌{'─'*58}┐")
    print(f"│{'  RALPH WICKHAM — Autonomous Task Runner v1.0':^58}│")
    print(f"│{'  CORTEX-Persist · Industrial Noir 2026':^58}│")
    print(f"└{'─'*58}┘{_R}\n")


def _print_cycle(iteration: int, task: Task) -> None:
    print(f"{_DIM}{'─'*60}{_R}")
    print(f"{_B}{_CYN}[ITER {iteration:02d}]{_R} {task.label[:72]}")


def _print_result(success: bool, stdout: str, stderr: str, duration: float) -> None:
    icon = f"{_GRN}✓ SUCCESS{_R}" if success else f"{_RED}✗ FAILURE{_R}"
    print(f"  {icon}  {_DIM}({duration:.2f}s){_R}")
    if stdout:
        preview = textwrap.shorten(stdout, width=160, placeholder="…")
        print(f"  {_DIM}stdout:{_R} {preview}")
    if stderr and not success:
        preview = textwrap.shorten(stderr, width=160, placeholder="…")
        print(f"  {_RED}stderr:{_R} {preview}")


# ─── Main loop ───────────────────────────────────────────────────────────────

def run() -> None:
    _banner()
    LOG_DIR.mkdir(exist_ok=True)

    stats = {"iterations": 0, "done": 0, "blocked": 0, "errors": 0}

    for iteration in range(1, MAX_ITERATIONS + 1):
        raw_text = _read_tasks_raw()
        pending  = _parse_pending(raw_text)

        if not pending:
            print(f"\n{_GRN}{_B}✅  Queue empty — Ralph done.{_R}")
            break

        task = pending[0]
        retries = _get_retries(task)

        _print_cycle(iteration, task)

        # ── Guard: block if retries exhausted ──
        if retries >= MAX_RETRIES:
            note = f"blocked after {MAX_RETRIES} retries"
            _update_tasks_file(raw_text, task, "blocked", note)
            entry = LedgerEntry(
                task_id=f"T{iteration:03d}",
                task_label=task.label,
                status="blocked",
                iteration=iteration,
                retry=retries,
                timestamp=datetime.now(timezone.utc).isoformat(),
                duration_s=0.0,
            )
            _append_ledger(entry)
            print(f"  {_YEL}⚠  BLOCKED — {note}{_R}")
            stats["blocked"] += 1
            stats["iterations"] += 1
            continue

        # ── Mark in-progress ──
        raw_text = _read_tasks_raw()
        _update_tasks_file(raw_text, task, "in_progress")

        # ── Execute ──
        t0  = time.perf_counter()
        cmd = _extract_command(task.label)

        if cmd:
            success, stdout, stderr, exit_code = _execute_shell(cmd)
        else:
            # Non-shell task: log as manual / advisory
            success   = True
            stdout    = "Advisory task — no shell command. Mark complete manually or extend handler."
            stderr    = ""
            exit_code = 0

        duration = round(time.perf_counter() - t0, 3)
        _print_result(success, stdout, stderr, duration)

        # ── Update tasks.md ──
        raw_text = _read_tasks_raw()
        if success:
            _update_tasks_file(raw_text, task, "done")
            stats["done"] += 1
        else:
            new_retries = _increment_retries(task)
            if new_retries >= MAX_RETRIES:
                note = f"failed {new_retries}x — exit_code={exit_code}"
                _update_tasks_file(raw_text, task, "blocked", note)
                stats["blocked"] += 1
            else:
                note = f"retry {new_retries}/{MAX_RETRIES}"
                _update_tasks_file(raw_text, task, "pending", note)
                stats["errors"] += 1

        # ── Ledger ──
        entry = LedgerEntry(
            task_id=f"T{iteration:03d}",
            task_label=task.label,
            status="success" if success else "failure",
            iteration=iteration,
            retry=retries,
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_s=duration,
            stdout=stdout[:2000],
            stderr=stderr[:500],
            exit_code=exit_code,
        )
        _append_ledger(entry)
        stats["iterations"] += 1

        time.sleep(0.1)  # breathing room between cycles

    else:
        print(f"\n{_YEL}⚠  MAX_ITERATIONS ({MAX_ITERATIONS}) reached — stopping Ralph.{_R}")

    # ── Summary ──
    print(f"\n{_B}{'─'*60}")
    print(f"  RALPH SESSION SUMMARY")
    print(f"{'─'*60}{_R}")
    print(f"  Iterations : {stats['iterations']}")
    print(f"  Done       : {_GRN}{stats['done']}{_R}")
    print(f"  Blocked    : {_YEL}{stats['blocked']}{_R}")
    print(f"  Errors     : {_RED}{stats['errors']}{_R}")
    print(f"  Ledger     : {LEDGER_FILE}")
    print(f"{_B}{'─'*60}{_R}\n")


if __name__ == "__main__":
    run()
