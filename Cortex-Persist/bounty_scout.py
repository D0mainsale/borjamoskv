#!/usr/bin/env python3
"""
bounty_scout.py — Caza-Recompensas Scout Engine v1.0
──────────────────────────────────────────────────────
Descubimiento autónomo de programas de bounty activos.

Plataformas:
  - Immunefi    (GraphQL API pública)
  - Code4rena   (REST API pública)
  - Sherlock    (scraping público)
  - HackerOne   (REST API, requiere token para privados)

Output:
  - tasks.md    (Ralph-compatible task queue)
  - bounties.jsonl (ledger de programas descubiertos)

Reality Level: C5-REAL (APIs reales, sin simulación)
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠ requests not installed — run: pip install requests")

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
TASKS_FILE   = Path("tasks.md")
BOUNTIES_DB  = Path("bounties.jsonl")
MIN_REWARD   = int(os.getenv("MIN_REWARD_USD", "1000"))   # filtra bounties < umbral
MAX_BOUNTIES = int(os.getenv("MAX_BOUNTIES",   "20"))     # máx tasks generadas
TIMEOUT      = 15  # segundos por request

IMMUNEFI_GRAPHQL = "https://immunefi.com/api/bounty/list"
CODE4RENA_API    = "https://code4rena.com/api/contests"
SHERLOCK_API     = "https://app.sherlock.xyz/audits/contests"


@dataclass
class BountyProgram:
    id:          str
    platform:    str   # immunefi | code4rena | sherlock | hackerone
    name:        str
    url:         str
    max_reward:  int   # USD
    asset_count: int
    repo_url:    Optional[str]
    deadline:    Optional[str]
    tags:        list[str]
    discovered:  str   # ISO timestamp

    def score(self) -> float:
        """Exergy score: reward × asset_density / effort_proxy."""
        asset_factor = min(self.asset_count, 10) / 10.0
        reward_factor = min(self.max_reward, 100_000) / 100_000.0
        return round(reward_factor * 0.7 + asset_factor * 0.3, 4)

    def to_task_line(self) -> str:
        reward_k = f"${self.max_reward // 1000}k" if self.max_reward >= 1000 else f"${self.max_reward}"
        repo_hint = f" · repo={self.repo_url}" if self.repo_url else ""
        return (
            f"- [ ] [BOUNTY·{self.platform.upper()}] {self.name} "
            f"| reward={reward_k} | score={self.score():.3f}"
            f"{repo_hint} | url={self.url}"
        )


# ─── Platform Scouts ─────────────────────────────────────────────────────────

def _scout_immunefi() -> list[BountyProgram]:
    """Immunefi public bounty list."""
    if not HAS_REQUESTS:
        return []
    programs = []
    try:
        # Immunefi public JSON endpoint
        r = requests.get(
            "https://immunefi.com/bounty/list/",
            headers={"Accept": "application/json", "User-Agent": "CORTEX-Scout/1.0"},
            timeout=TIMEOUT,
        )
        # Immunefi returns HTML with embedded JSON — extract __NEXT_DATA__
        if r.status_code == 200:
            m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text, re.DOTALL)
            if m:
                data = json.loads(m.group(1))
                bounties_raw = (
                    data.get("props", {})
                        .get("pageProps", {})
                        .get("bounties", [])
                )
                for b in bounties_raw[:MAX_BOUNTIES]:
                    try:
                        max_r = int(b.get("maxBounty", "0").replace("$", "").replace(",", "").strip() or 0)
                    except (ValueError, AttributeError):
                        max_r = 0
                    if max_r < MIN_REWARD:
                        continue
                    assets = b.get("assets", [])
                    programs.append(BountyProgram(
                        id=f"immunefi-{b.get('id', b.get('project', 'unknown'))}",
                        platform="immunefi",
                        name=b.get("project", "Unknown"),
                        url=f"https://immunefi.com/bounty/{b.get('id', '')}",
                        max_reward=max_r,
                        asset_count=len(assets),
                        repo_url=b.get("github") or b.get("repoUrl"),
                        deadline=b.get("deadline"),
                        tags=b.get("ecosystems", []),
                        discovered=datetime.now(timezone.utc).isoformat(),
                    ))
        print(f"{_GRN}  ✓ Immunefi: {len(programs)} programs found{_R}")
    except Exception as e:
        print(f"{_YEL}  ⚠ Immunefi scout error: {e}{_R}")
    return programs


def _scout_code4rena() -> list[BountyProgram]:
    """Code4rena public contest API."""
    if not HAS_REQUESTS:
        return []
    programs = []
    try:
        r = requests.get(
            "https://code4rena.com/api/contests",
            headers={"Accept": "application/json", "User-Agent": "CORTEX-Scout/1.0"},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            contests = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
            now = datetime.now(timezone.utc)
            for c in contests:
                # Only active/upcoming contests
                end_raw = c.get("end_time") or c.get("endTime") or c.get("endDate")
                if end_raw:
                    try:
                        end_dt = datetime.fromisoformat(str(end_raw).replace("Z", "+00:00"))
                        if end_dt < now:
                            continue  # expired
                    except Exception:
                        pass
                try:
                    pool = int(c.get("total_prize_pool", c.get("prizePool", 0)) or 0)
                except (ValueError, TypeError):
                    pool = 0
                if pool < MIN_REWARD:
                    continue
                repo = c.get("repo") or c.get("repoUrl") or c.get("github")
                programs.append(BountyProgram(
                    id=f"c4-{c.get('id', c.get('slug', 'unknown'))}",
                    platform="code4rena",
                    name=c.get("title", c.get("name", "Unknown")),
                    url=f"https://code4rena.com/contests/{c.get('id', '')}",
                    max_reward=pool,
                    asset_count=c.get("numSolFiles", 0) or 1,
                    repo_url=repo,
                    deadline=str(end_raw) if end_raw else None,
                    tags=["solidity", "evm"],
                    discovered=datetime.now(timezone.utc).isoformat(),
                ))
        print(f"{_GRN}  ✓ Code4rena: {len(programs)} active contests{_R}")
    except Exception as e:
        print(f"{_YEL}  ⚠ Code4rena scout error: {e}{_R}")
    return programs


def _scout_sherlock() -> list[BountyProgram]:
    """Sherlock public contest page (HTML scraping fallback)."""
    if not HAS_REQUESTS:
        return []
    programs = []
    try:
        r = requests.get(
            "https://audits.sherlock.xyz/contests",
            headers={"Accept": "text/html", "User-Agent": "CORTEX-Scout/1.0"},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            # Extract contest data from embedded JSON (Next.js __NEXT_DATA__)
            m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text, re.DOTALL)
            if m:
                data = json.loads(m.group(1))
                contests = (
                    data.get("props", {})
                        .get("pageProps", {})
                        .get("contests", [])
                )
                for c in contests:
                    try:
                        pool = int(c.get("prize_pool", 0) or 0)
                    except (ValueError, TypeError):
                        pool = 0
                    if pool < MIN_REWARD:
                        continue
                    programs.append(BountyProgram(
                        id=f"sherlock-{c.get('id', 'unknown')}",
                        platform="sherlock",
                        name=c.get("title", c.get("protocol", "Unknown")),
                        url=f"https://audits.sherlock.xyz/contests/{c.get('id', '')}",
                        max_reward=pool,
                        asset_count=1,
                        repo_url=c.get("repo"),
                        deadline=str(c.get("ends_at", "")),
                        tags=["solidity"],
                        discovered=datetime.now(timezone.utc).isoformat(),
                    ))
        print(f"{_GRN}  ✓ Sherlock: {len(programs)} active contests{_R}")
    except Exception as e:
        print(f"{_YEL}  ⚠ Sherlock scout error: {e}{_R}")
    return programs


def _scout_hackerone() -> list[BountyProgram]:
    """HackerOne public programs (no auth required for public scope)."""
    if not HAS_REQUESTS:
        return []
    programs = []
    try:
        r = requests.get(
            "https://hackerone.com/programs.json",
            params={"limit": 25, "order_direction": "DESC", "order_field": "launched_at"},
            headers={"Accept": "application/json", "User-Agent": "CORTEX-Scout/1.0"},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            data = r.json()
            for prog in data.get("results", []):
                try:
                    max_r = int(prog.get("max_bounty", 0) or 0)
                except (ValueError, TypeError):
                    max_r = 1000  # assume minimum
                if max_r < MIN_REWARD:
                    continue
                programs.append(BountyProgram(
                    id=f"h1-{prog.get('id', 'unknown')}",
                    platform="hackerone",
                    name=prog.get("name", "Unknown"),
                    url=f"https://hackerone.com/{prog.get('handle', '')}",
                    max_reward=max_r,
                    asset_count=len(prog.get("in_scope", [])),
                    repo_url=None,
                    deadline=None,
                    tags=prog.get("focused_on", []),
                    discovered=datetime.now(timezone.utc).isoformat(),
                ))
        print(f"{_GRN}  ✓ HackerOne: {len(programs)} programs found{_R}")
    except Exception as e:
        print(f"{_YEL}  ⚠ HackerOne scout error: {e}{_R}")
    return programs


# ─── Aggregator ──────────────────────────────────────────────────────────────

def run_scout() -> list[BountyProgram]:
    print(f"\n{_B}{_BLU}┌{'─'*60}┐")
    print(f"│{'  CAZA-RECOMPENSAS SCOUT ENGINE v1.0':^60}│")
    print(f"│{'  CORTEX-Persist · C5-REAL Discovery':^60}│")
    print(f"│{'  Min reward: $' + str(MIN_REWARD) + ' · Max programs: ' + str(MAX_BOUNTIES):^60}│")
    print(f"└{'─'*60}┘{_R}\n")

    print(f"{_DIM}Scanning platforms...{_R}")
    all_programs: list[BountyProgram] = []
    all_programs.extend(_scout_immunefi())
    all_programs.extend(_scout_code4rena())
    all_programs.extend(_scout_sherlock())
    all_programs.extend(_scout_hackerone())

    # Sort by exergy score descending
    all_programs.sort(key=lambda p: p.score(), reverse=True)

    # Deduplicate by name
    seen: set[str] = set()
    unique: list[BountyProgram] = []
    for p in all_programs:
        key = p.name.lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(p)

    unique = unique[:MAX_BOUNTIES]

    print(f"\n{_B}  Found {len(unique)} programs above ${MIN_REWARD} threshold{_R}")
    for i, p in enumerate(unique, 1):
        print(f"  {_CYN}{i:02d}.{_R} {p.name:<30} {_YEL}${p.max_reward:>7,}{_R} — score={p.score():.3f} [{p.platform}]")

    return unique


# ─── Task Queue Writer ────────────────────────────────────────────────────────

def inject_into_tasks(programs: list[BountyProgram]) -> None:
    """Append bounty tasks to tasks.md for Ralph parallel consumption."""
    if not programs:
        print(f"{_YEL}No programs to inject.{_R}")
        return

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    new_section = f"\n\n## 🎯 Bounty Queue — {ts}\n"
    new_section += f"<!-- Scout injected {len(programs)} targets -->\n"
    for p in programs:
        new_section += p.to_task_line() + "\n"
    new_section += "\n<!-- Ralph documenta aquí cada ciclo completado -->\n"

    if TASKS_FILE.exists():
        existing = TASKS_FILE.read_text(encoding="utf-8")
        TASKS_FILE.write_text(existing + new_section, encoding="utf-8")
    else:
        TASKS_FILE.write_text(f"# Caza-Recompensas Tasks\n{new_section}", encoding="utf-8")

    print(f"\n{_GRN}✓ {len(programs)} tasks injected → {TASKS_FILE}{_R}")


def save_bounties_ledger(programs: list[BountyProgram]) -> None:
    """Persist discovered programs to bounties.jsonl."""
    with BOUNTIES_DB.open("a", encoding="utf-8") as fh:
        for p in programs:
            fh.write(json.dumps(asdict(p), ensure_ascii=False) + "\n")
    print(f"{_DIM}  Ledger persisted → {BOUNTIES_DB}{_R}")


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Caza-Recompensas Scout Engine")
    ap.add_argument("--min-reward", type=int, default=MIN_REWARD, help="Min bounty reward USD")
    ap.add_argument("--max",        type=int, default=MAX_BOUNTIES, help="Max programs to fetch")
    ap.add_argument("--inject",     action="store_true", default=True, help="Inject into tasks.md")
    ap.add_argument("--no-inject",  dest="inject", action="store_false")
    args = ap.parse_args()

    MIN_REWARD   = args.min_reward
    MAX_BOUNTIES = args.max

    programs = run_scout()

    if programs:
        save_bounties_ledger(programs)
        if args.inject:
            inject_into_tasks(programs)
        print(f"\n{_B}{_GRN}🎯 Scout complete. {len(programs)} bounty targets queued.{_R}\n")
    else:
        print(f"\n{_YEL}⚠ No viable bounties found above ${MIN_REWARD} threshold.{_R}\n")
        print(f"  Try: python bounty_scout.py --min-reward 500\n")
