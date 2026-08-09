"""
cortex.agentic.persist_membrane
================================
CORTEX Persist — Verification Membrane for the Write Path
Layer Ω-PERSIST (between ToolRegistry/Runtime and the Ledger)

ARCHITECTURE:
  CortexRuntime.execute_task()
    └─> PersistMembrane.guard_write()   ← dry-run trust check
    └─> ToolRegistry.execute()
    └─> PersistMembrane.commit_fact()   ← sealed persist
    └─> PersistMembrane.verify_fact()   ← post-action audit

CORTEX Persist HTTP surface (local-first, SQLite+WAL):
  POST /v1/trust/guard  → SchemaGuard dry-run
  POST /v1/facts        → Commit a single sealed fact
  POST /v1/facts/batch  → Bulk commit
  POST /v1/facts/search → Retrieve live context
  GET  /v1/facts/{id}/verify → Integrity check
  GET  /v1/projects/{project}/export → Evidence export
  POST /v1/facts/{id}/taint  → Causal contamination

Confidence: C5-Static (local-first mode hardened)
Maturity note: trust/guard & facts are core-stable; taint is beta.
"""

from __future__ import annotations

import os
import time
import json
import hashlib
import logging
from typing import Any, Dict, Optional, List, Literal
from dataclasses import dataclass, field

import httpx  # pip install httpx

logger = logging.getLogger("persist_membrane")

# ── Config (pulled from env, defaults to local dev) ──────────────────────────

PERSIST_BASE_URL = os.getenv("CORTEX_PERSIST_URL", "http://localhost:8001")
PERSIST_TOKEN    = os.getenv("CORTEX_PERSIST_TOKEN", "")       # Bearer token
PERSIST_PROJECT  = os.getenv("CORTEX_PERSIST_PROJECT", "cortex-sovereign")
PERSIST_TIMEOUT  = float(os.getenv("CORTEX_PERSIST_TIMEOUT", "3.0"))  # seconds

# Role: AGENT can write, VIEWER read-only, ADMIN for bootstrap
PERSIST_ROLE     = os.getenv("CORTEX_PERSIST_ROLE", "AGENT")

# ── Internal: SHA-256 fingerprint for local fallback chain ────────────────────

def _sha256(payload: Dict[str, Any]) -> str:
    canon = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canon.encode()).hexdigest()


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class FactProposal:
    """
    A proposed write. NOT yet state.
    Every LLM output, tool result, or external API response starts here.
    """
    subject:    str                                        # e.g. "deploy:ai-ml"
    predicate:  str                                        # e.g. "executed_by"
    object_val: Any                                        # value, can be dict
    source:     Literal["llm", "tool", "api", "human"]
    confidence: float = 1.0                                # [0.0 – 1.0]
    session_id: Optional[str] = None
    metadata:   Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return {
            "project":    PERSIST_PROJECT,
            "subject":    self.subject,
            "predicate":  self.predicate,
            "object":     self.object_val,
            "source":     self.source,
            "confidence": self.confidence,
            "session_id": self.session_id,
            "metadata":   self.metadata,
            "proposed_at": time.time(),
        }


@dataclass
class GuardResult:
    passed: bool
    status: str          # "PASS" | "BLOCK" | "WARN" | "OFFLINE"
    reasons: List[str] = field(default_factory=list)
    fact_id: Optional[str] = None  # populated after commit


@dataclass
class CommitResult:
    success: bool
    fact_id: Optional[str]
    hash:    Optional[str]
    status:  str   # "COMMITTED" | "FALLBACK" | "FAILED"


# ── PersistMembrane ───────────────────────────────────────────────────────────

class PersistMembrane:
    """
    Verification membrane for the CORTEX write path.

    Usage pattern (inside CortexRuntime.execute_task or a tool wrapper):

        membrane = PersistMembrane()

        # 1. Dry-run guard before any mutation
        guard = await membrane.guard_write(proposal)
        if not guard.passed:
            raise RuntimeError(f"PERSIST_BLOCKED: {guard.reasons}")

        # 2. Execute tool / action
        result = tool.execute(...)

        # 3. Commit result as sealed fact
        commit = await membrane.commit_fact(proposal, result)

        # 4. Post-action verify (async, fire-and-forget acceptable for P1)
        await membrane.verify_fact(commit.fact_id)
    """

    def __init__(self):
        headers = {"Content-Type": "application/json"}
        if PERSIST_TOKEN:
            headers["Authorization"] = f"Bearer {PERSIST_TOKEN}"
        self._client = httpx.AsyncClient(
            base_url=PERSIST_BASE_URL,
            headers=headers,
            timeout=PERSIST_TIMEOUT,
        )
        self._online: Optional[bool] = None  # None = unknown

    # ── 1. Guard (dry-run, idempotent) ────────────────────────────────────────

    async def guard_write(self, proposal: FactProposal) -> GuardResult:
        """
        POST /v1/trust/guard
        Non-destructive. Checks schema, policy, and admission rules.
        Call this BEFORE any tool execution.
        Fails OPEN (returns WARN) if CORTEX Persist is offline — log and continue.
        """
        payload = {**proposal.to_payload(), "dry_run": True}
        try:
            r = await self._client.post("/v1/trust/guard", json=payload)
            self._online = True
            body = r.json()
            if r.status_code == 200 and body.get("admitted", False):
                return GuardResult(passed=True, status="PASS", reasons=body.get("notes", []))
            else:
                return GuardResult(passed=False, status="BLOCK", reasons=body.get("violations", ["GUARD_REJECTED"]))
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            self._online = False
            logger.warning(f"◈ PERSIST_MEMBRANE: Guard offline — failing open. [{e}]")
            return GuardResult(passed=True, status="OFFLINE", reasons=["persist_unreachable"])

    # ── 2. Commit (sealed write) ───────────────────────────────────────────────

    async def commit_fact(
        self,
        proposal: FactProposal,
        result: Optional[Any] = None,
    ) -> CommitResult:
        """
        POST /v1/facts
        Seals the proposal (with optional result) as a tamper-evident fact.
        Falls back to local SHA-256 record if CORTEX Persist is offline.
        """
        payload = proposal.to_payload()
        if result is not None:
            payload["result"] = result if isinstance(result, dict) else {"value": str(result)}

        try:
            r = await self._client.post("/v1/facts", json=payload)
            self._online = True
            if r.status_code in (200, 201):
                body = r.json()
                return CommitResult(
                    success=True,
                    fact_id=body.get("fact_id"),
                    hash=body.get("hash"),
                    status="COMMITTED",
                )
            else:
                logger.error(f"◈ PERSIST_MEMBRANE: Commit rejected [{r.status_code}]: {r.text}")
                return CommitResult(success=False, fact_id=None, hash=None, status="FAILED")
        except (httpx.ConnectError, httpx.TimeoutException):
            # Local fallback: SHA-256 fingerprint stored in cortex/data/swarm_ledger.jsonl
            self._online = False
            local_hash = _sha256(payload)
            _write_local_fallback(payload, local_hash)
            return CommitResult(success=True, fact_id=None, hash=local_hash, status="FALLBACK")

    # ── 3. Batch commit ────────────────────────────────────────────────────────

    async def commit_batch(self, proposals: List[FactProposal]) -> List[CommitResult]:
        """POST /v1/facts/batch — bulk sealed write."""
        items = [p.to_payload() for p in proposals]
        try:
            r = await self._client.post("/v1/facts/batch", json={"facts": items, "project": PERSIST_PROJECT})
            self._online = True
            results = r.json().get("results", [])
            return [
                CommitResult(
                    success=item.get("success", False),
                    fact_id=item.get("fact_id"),
                    hash=item.get("hash"),
                    status="COMMITTED" if item.get("success") else "FAILED",
                )
                for item in results
            ]
        except (httpx.ConnectError, httpx.TimeoutException):
            return [await self.commit_fact(p) for p in proposals]

    # ── 4. Search (live context retrieval) ────────────────────────────────────

    async def search_context(
        self,
        query: str,
        as_of: Optional[float] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        POST /v1/facts/search
        Retrieve live, auditable context for the planner before generating a plan.
        Use as_of (unix timestamp) for temporal queries.
        """
        payload: Dict[str, Any] = {
            "project": PERSIST_PROJECT,
            "query":   query,
            "limit":   limit,
        }
        if as_of is not None:
            payload["as_of"] = as_of
        try:
            r = await self._client.post("/v1/facts/search", json=payload)
            self._online = True
            return r.json().get("facts", [])
        except (httpx.ConnectError, httpx.TimeoutException):
            logger.warning("◈ PERSIST_MEMBRANE: Search offline — returning empty context.")
            return []

    # ── 5. Verify (post-action audit) ─────────────────────────────────────────

    async def verify_fact(self, fact_id: Optional[str]) -> Dict[str, Any]:
        """
        GET /v1/facts/{fact_id}/verify
        Confirms hash-chain integrity after a critical action.
        Call after every P0 mutation.
        """
        if not fact_id:
            return {"verified": False, "reason": "no_fact_id"}
        try:
            r = await self._client.get(f"/v1/facts/{fact_id}/verify")
            self._online = True
            return r.json()
        except (httpx.ConnectError, httpx.TimeoutException):
            return {"verified": False, "reason": "persist_offline"}

    # ── 6. History + Taint (forensics) ────────────────────────────────────────

    async def taint_fact(self, fact_id: str, reason: str) -> Dict[str, Any]:
        """
        POST /v1/facts/{fact_id}/taint
        Marks a fact as compromised and propagates taint causally to derived facts.
        Use when a tool result is found to be incorrect or malicious.
        BETA: maturity level is lower; use with explicit logging.
        """
        try:
            r = await self._client.post(
                f"/v1/facts/{fact_id}/taint",
                json={"reason": reason, "project": PERSIST_PROJECT},
            )
            self._online = True
            return r.json()
        except (httpx.ConnectError, httpx.TimeoutException):
            return {"tainted": False, "reason": "persist_offline"}

    async def get_history(self, subject: str) -> List[Dict[str, Any]]:
        """GET /v1/facts/{subject}/history — causal lineage for forensics."""
        try:
            r = await self._client.get(f"/v1/facts/{subject}/history", params={"project": PERSIST_PROJECT})
            return r.json().get("history", [])
        except (httpx.ConnectError, httpx.TimeoutException):
            return []

    # ── 7. Export (evidence package) ──────────────────────────────────────────

    async def export_project(self) -> Dict[str, Any]:
        """
        GET /v1/projects/{project}/export
        Full evidence export: audit log, hash-chain, Merkle proof.
        Call after a completed agentic run for audit-readiness.
        """
        try:
            r = await self._client.get(f"/v1/projects/{PERSIST_PROJECT}/export")
            self._online = True
            return r.json()
        except (httpx.ConnectError, httpx.TimeoutException):
            return {"exported": False, "reason": "persist_offline"}

    async def aclose(self):
        await self._client.aclose()


# ── Local fallback writer (when CORTEX Persist offline) ─────────────────────

def _write_local_fallback(payload: Dict[str, Any], local_hash: str):
    """
    Writes to cortex/data/swarm_ledger.jsonl as SHA-256 fingerprinted fallback.
    Preserves auditability when CORTEX Persist is unreachable.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ledger_path = os.path.join(base_dir, "cortex/data/swarm_ledger.jsonl")
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "persist_mode": "LOCAL_FALLBACK",
        "hash": local_hash,
        "payload": payload,
    }
    with open(ledger_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    logger.info(f"◈ PERSIST_MEMBRANE: Local fallback written [{local_hash[:12]}]")


# ── Convenience: sync wrapper for non-async callers (sovereign_proxy) ────────

def guard_and_commit_sync(
    subject: str,
    predicate: str,
    object_val: Any,
    source: Literal["llm", "tool", "api", "human"] = "tool",
    result: Optional[Any] = None,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> CommitResult:
    """
    Sync wrapper for use inside SovereignRequestHandler (non-async).
    Runs the guard → commit cycle in an isolated event loop.
    Returns CommitResult — caller decides whether to block on BLOCK status.
    """
    import asyncio

    proposal = FactProposal(
        subject=subject,
        predicate=predicate,
        object_val=object_val,
        source=source,
        session_id=session_id,
        metadata=metadata or {},
    )

    async def _run():
        membrane = PersistMembrane()
        try:
            guard = await membrane.guard_write(proposal)
            if not guard.passed:
                logger.warning(f"◈ PERSIST: GUARD_BLOCK [{guard.reasons}]")
                return CommitResult(success=False, fact_id=None, hash=None, status=f"BLOCKED:{guard.reasons}")
            commit = await membrane.commit_fact(proposal, result)
            logger.info(f"◈ PERSIST: COMMITTED [{commit.fact_id or commit.hash[:12]}] status={commit.status}")
            return commit
        finally:
            await membrane.aclose()

    return asyncio.run(_run())
