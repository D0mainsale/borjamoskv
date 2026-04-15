#!/usr/bin/env python3
"""
swarm_commander.py — Caza-Recompensas Swarm Commander v1.0
────────────────────────────────────────────────────────────
Orquestador del swarm completo:

  FASE 1 — SCOUT:   bounty_scout.py → tasks.md
  FASE 2 — HUNT:    ralph_parallel.py → workers claim tasks
  FASE 3 — REPORT:  bounty_hunter.py por cada worker
  FASE 4 — SUBMIT:  capital_extractor.py (C5-REAL si credenciales)

Uso rápido:
  python swarm_commander.py                  # full cycle
  python swarm_commander.py --phase scout    # solo discovery
  python swarm_commander.py --phase hunt     # solo analysis
  python swarm_commander.py --phase status   # dashboard

Reality level: 
  Scout/Clone/Slither → C5-REAL
  Submission          → C5-REAL si credenciales | C4-SIMULACIÓN si no
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Optional

# ─── ANSI / Industrial Noir ──────────────────────────────────────────────────
_R   = "\033[0m"
_B   = "\033[1m"
_DIM = "\033[2m"
_BLU = "\033[38;5;33m"
_GRN = "\033[38;5;46m"
_RED = "\033[38;5;196m"
_YEL = "\033[38;5;226m"
_CYN = "\033[38;5;51m"
_MGN = "\033[38;5;201m"

# ─── Config ──────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
TASKS_FILE    = BASE_DIR / "tasks.md"
BOUNTIES_DB   = BASE_DIR / "bounties.jsonl"
FINDINGS_LOG  = BASE_DIR / "findings.jsonl"
REPORTS_DIR   = BASE_DIR / "bounty_reports"
LEDGER_FILE   = BASE_DIR / "swarm_ledger.jsonl"

NUM_HUNTERS  = int(os.getenv("HUNTERS",      "3"))
MIN_REWARD   = int(os.getenv("MIN_REWARD_USD","1000"))

_print_lock = Lock()


def _banner() -> None:
    print(f"\n{_B}{_BLU}╔{'═'*62}╗")
    print(f"║{'  ⚡ CAZA-RECOMPENSAS SWARM COMMANDER v1.0':^62}║")
    print(f"║{'  CORTEX-Persist · Industrial Noir 2026':^62}║")
    print(f"║{'  Hunters: ' + str(NUM_HUNTERS) + ' · Min Reward: $' + str(MIN_REWARD):^62}║")
    print(f"╚{'═'*62}╝{_R}\n")


def _log(msg: str, color: str = _CYN) -> None:
    with _print_lock:
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        print(f"{_DIM}[{ts}]{_R} {color}{_B}CMD{_R} {msg}")


# ─── Credential Check ─────────────────────────────────────────────────────────

def _check_credentials() -> dict:
    creds = {
        "CODE4RENA_API_KEY": bool(os.getenv("CODE4RENA_API_KEY")),
        "IMMUNEFI_HANDLE":   bool(os.getenv("IMMUNEFI_HANDLE")),
        "HACKERONE_TOKEN":   bool(os.getenv("HACKERONE_TOKEN")),
        "ETH_RPC_URL":       bool(os.getenv("ETH_RPC_URL")),
        "WALLET_PRIVATE_KEY":bool(os.getenv("WALLET_PRIVATE_KEY")),
    }
    return creds


def _print_credential_status(creds: dict) -> None:
    print(f"\n{_DIM}Credential inventory:{_R}")
    for key, has_val in creds.items():
        icon = f"{_GRN}C5-REAL{_R}" if has_val else f"{_YEL}C4-SIM {_R}"
        print(f"  [{icon}] {key}")

    has_any = any(creds.values())
    if not has_any:
        print(f"\n  {_YEL}⚠ No credentials set — swarm will operate in RECON mode{_R}")
        print(f"  {_DIM}Set environment variables to enable C5-REAL submissions{_R}")
    else:
        real_count = sum(creds.values())
        print(f"\n  {_GRN}✓ {real_count}/{len(creds)} credentials active — partial C5-REAL mode{_R}")


# ─── Phase 1: Scout ──────────────────────────────────────────────────────────

def phase_scout() -> int:
    """Run bounty_scout.py to populate tasks.md."""
    _log("PHASE 1 — SCOUT: Discovering bounties...", _BLU)

    script = BASE_DIR / "bounty_scout.py"
    if not script.exists():
        _log(f"bounty_scout.py not found at {script}", _RED)
        return 0

    result = subprocess.run(
        [sys.executable, str(script),
         "--min-reward", str(MIN_REWARD),
         "--inject"],
        capture_output=False,
        cwd=str(BASE_DIR),
    )

    # Count injected tasks
    if TASKS_FILE.exists():
        content = TASKS_FILE.read_text(encoding="utf-8")
        count = content.count("- [ ] [BOUNTY·")
        _log(f"Scout complete: {count} tasks queued", _GRN)
        return count
    return 0


# ─── Phase 2+3: Hunt (parallel workers) ─────────────────────────────────────

def _extract_task_params(task_label: str) -> dict:
    """Parse bounty task label for hunter parameters."""
    params = {"repo_url": None, "platform": "unknown", "reward": 0, "bounty_url": None}

    # Platform
    m = re.search(r"\[BOUNTY·(\w+)\]", task_label)
    if m:
        params["platform"] = m.group(1).lower()

    # Repo URL
    m = re.search(r"repo=(\S+?)(?:\s|\|)", task_label + " ")
    if m:
        params["repo_url"] = m.group(1)

    # Bounty URL  
    m = re.search(r"url=(\S+?)(?:\s|\|)", task_label + " ")
    if m:
        params["bounty_url"] = m.group(1)

    # Reward
    m = re.search(r"reward=\$?(\d+)k?", task_label)
    if m:
        val = int(m.group(1))
        if "k" in task_label[m.start():m.end()+2]:
            val *= 1000
        params["reward"] = val

    return params


def _hunt_worker(worker_id: int, task_label: str) -> dict:
    """Single hunter worker."""
    with _print_lock:
        color = [_BLU, _CYN, _MGN, _YEL, _GRN][worker_id % 5]
        print(f"{_DIM}[{datetime.now(timezone.utc).strftime('%H:%M:%S')}]{_R} "
              f"{color}{_B}H{worker_id:02d}{_R} HUNTING: {task_label[:60]}")

    params = _extract_task_params(task_label)

    # Dynamic import of bounty_hunter
    try:
        sys.path.insert(0, str(BASE_DIR))
        from bounty_hunter import hunt
        result = hunt(
            task_label=task_label,
            platform=params["platform"],
            repo_url=params["repo_url"],
            bounty_url=params["bounty_url"],
            reward_usd=params["reward"],
        )
    except ImportError as e:
        result = {"status": f"import_error: {e}", "findings": 0}
    except Exception as e:
        result = {"status": f"error: {e}", "findings": 0}

    # Log to swarm ledger
    entry = {
        "worker_id": worker_id,
        "task": task_label[:120],
        "platform": params["platform"],
        "result": result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with _print_lock:
        with LEDGER_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return result


def phase_hunt(tasks: list[str]) -> dict:
    """Run parallel hunters on bounty tasks."""
    _log(f"PHASE 2+3 — HUNT: {len(tasks)} targets → {NUM_HUNTERS} hunters", _MGN)

    if not tasks:
        _log("No tasks to hunt", _YEL)
        return {"total": 0, "findings": 0, "high": 0}

    total_findings = 0
    total_high     = 0

    with ThreadPoolExecutor(max_workers=NUM_HUNTERS, thread_name_prefix="hunter") as pool:
        futures = {
            pool.submit(_hunt_worker, wid, task): (wid, task)
            for wid, task in enumerate(tasks)
        }
        for fut in as_completed(futures):
            wid, task = futures[fut]
            try:
                result = fut.result()
                f_count = result.get("findings", 0)
                h_count = result.get("high", 0)
                total_findings += f_count
                total_high     += h_count
                status_icon = _GRN if h_count == 0 else _RED
                _log(
                    f"H{wid:02d} done: {f_count} findings [{_RED if h_count > 0 else _GRN}{h_count} HIGH{_R}]",
                    status_icon,
                )
            except Exception as exc:
                _log(f"H{wid:02d} FATAL: {exc}", _RED)

    return {
        "total": len(tasks),
        "findings": total_findings,
        "high": total_high,
    }


# ─── Phase 4: Submit ─────────────────────────────────────────────────────────

def phase_submit() -> None:
    """Submit findings with real credentials (C5-REAL) if available."""
    creds = _check_credentials()

    if not any(creds.values()):
        _log("PHASE 4 — SUBMIT: No credentials — skipping (C4-SIMULACIÓN declared)", _YEL)
        _log("  Set CODE4RENA_API_KEY or IMMUNEFI_HANDLE for C5-REAL submission", _DIM)
        return

    _log("PHASE 4 — SUBMIT: Processing findings for submission...", _GRN)

    if not FINDINGS_LOG.exists():
        _log("No findings.jsonl — nothing to submit", _YEL)
        return

    findings = []
    with FINDINGS_LOG.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                findings.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    high_findings = [f for f in findings if f.get("severity") == "High" and not f.get("submitted")]

    if not high_findings:
        _log(f"No unsubmitted HIGH findings. Total findings: {len(findings)}", _YEL)
        return

    _log(f"Found {len(high_findings)} HIGH findings eligible for submission", _MGN)

    if creds["CODE4RENA_API_KEY"]:
        for finding in high_findings:
            if finding.get("platform") == "code4rena":
                _log(f"  → Submitting to Code4rena: {finding.get('title', 'Unknown')[:50]}", _BLU)
                # Import and call CapitalExtractorC5
                try:
                    sys.path.insert(0, str(BASE_DIR / "cortex_ouroboros"))
                    from capital_extractor import CapitalExtractorC5
                    extractor = CapitalExtractorC5()
                    result = extractor.submit_code4rena_finding(
                        handle=os.getenv("C4_HANDLE", "cortex-hunter"),
                        contest_id=finding.get("bounty_name", ""),
                        vulnerability_payload={
                            "title": finding.get("title", ""),
                            "risk": "3 (High Risk)",
                            "markdown_body": finding.get("description", ""),
                        },
                    )
                    _log(f"  ✓ Submitted: {result}", _GRN)
                except Exception as e:
                    _log(f"  ✗ Submission failed: {e}", _RED)


# ─── Status Dashboard ─────────────────────────────────────────────────────────

def phase_status() -> None:
    """Print current swarm status."""
    print(f"\n{_B}{'─'*64}{_R}")
    print(f"  {_BLU}CAZA-RECOMPENSAS SWARM STATUS{_R}")
    print(f"{'─'*64}")

    # Tasks
    if TASKS_FILE.exists():
        content = TASKS_FILE.read_text(encoding="utf-8")
        pending   = content.count("- [ ]")
        in_prog   = content.count("- [/]")
        done      = content.count("- [x]")
        blocked   = content.count("- [B]")
        total     = pending + in_prog + done + blocked
        print(f"  Tasks     : {total} total")
        print(f"    Pending : {_CYN}{pending}{_R}")
        print(f"    Active  : {_YEL}{in_prog}{_R}")
        print(f"    Done    : {_GRN}{done}{_R}")
        print(f"    Blocked : {_RED}{blocked}{_R}")
    else:
        print(f"  Tasks     : {_DIM}No tasks.md found{_R}")

    # Findings
    if FINDINGS_LOG.exists():
        findings = []
        with FINDINGS_LOG.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    findings.append(json.loads(line))
                except Exception:
                    pass
        high   = sum(1 for f in findings if f.get("severity") == "High")
        medium = sum(1 for f in findings if f.get("severity") == "Medium")
        print(f"\n  Findings  : {len(findings)} total")
        print(f"    High    : {_RED}{high}{_R}")
        print(f"    Medium  : {_YEL}{medium}{_R}")
    else:
        print(f"  Findings  : {_DIM}No findings.jsonl{_R}")

    # Reports
    if REPORTS_DIR.exists():
        reports = list(REPORTS_DIR.glob("*.md"))
        print(f"\n  Reports   : {_GRN}{len(reports)}{_R} generated → {REPORTS_DIR}/")

    # Bounties discovered
    if BOUNTIES_DB.exists():
        count = sum(1 for _ in BOUNTIES_DB.open(encoding="utf-8"))
        print(f"  Bounties  : {_MGN}{count}{_R} discovered")

    # Credentials
    creds = _check_credentials()
    _print_credential_status(creds)
    print(f"{'─'*64}{_R}\n")


# ─── Full Cycle ───────────────────────────────────────────────────────────────

def full_cycle() -> None:
    _banner()

    creds = _check_credentials()
    _print_credential_status(creds)

    # Scout
    task_count = phase_scout()

    if task_count == 0:
        _log("No tasks generated — check network or lower --min-reward", _YEL)
        # Still show status
        phase_status()
        return

    # Read injected tasks
    content = TASKS_FILE.read_text(encoding="utf-8")
    bounty_tasks = [
        line.strip()
        for line in content.splitlines()
        if line.strip().startswith("- [ ] [BOUNTY·")
    ]
    bounty_tasks = [re.sub(r"^- \[ \] ", "", t) for t in bounty_tasks]

    # Hunt
    hunt_results = phase_hunt(bounty_tasks[:NUM_HUNTERS * 3])  # cap at 3x hunters

    # Submit (if credentials)
    phase_submit()

    # Final status
    print(f"\n{_B}{'═'*64}")
    print(f"  SWARM CYCLE COMPLETE")
    print(f"{'═'*64}{_R}")
    print(f"  Targets hunted : {hunt_results['total']}")
    print(f"  Findings total : {_GRN}{hunt_results['findings']}{_R}")
    print(f"  High severity  : {_RED if hunt_results['high'] > 0 else _GRN}{hunt_results['high']}{_R}")
    if hunt_results['high'] > 0:
        print(f"\n  {_MGN}⚡ ACTION REQUIRED: Review bounty_reports/ for HIGH severity findings{_R}")
    print(f"{'═'*64}{_R}\n")

    phase_status()


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Caza-Recompensas Swarm Commander")
    ap.add_argument("--phase",
        choices=["scout", "hunt", "submit", "status", "full"],
        default="full",
        help="Execution phase (default: full cycle)",
    )
    ap.add_argument("--hunters", type=int, default=NUM_HUNTERS, help="Number of parallel hunters")
    ap.add_argument("--min-reward", type=int, default=MIN_REWARD, help="Minimum bounty reward USD")
    args = ap.parse_args()

    NUM_HUNTERS = args.hunters
    MIN_REWARD  = args.min_reward

    if args.phase == "scout":
        _banner()
        phase_scout()
    elif args.phase == "hunt":
        _banner()
        if TASKS_FILE.exists():
            content = TASKS_FILE.read_text(encoding="utf-8")
            tasks = [
                re.sub(r"^- \[ \] ", "", line.strip())
                for line in content.splitlines()
                if line.strip().startswith("- [ ] [BOUNTY·")
            ]
            phase_hunt(tasks)
        else:
            print(f"{_YEL}No tasks.md found — run scout first{_R}")
    elif args.phase == "submit":
        _banner()
        phase_submit()
    elif args.phase == "status":
        phase_status()
    else:
        full_cycle()
