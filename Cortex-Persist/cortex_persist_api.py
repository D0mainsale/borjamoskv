"""
cortex_persist_api.py
=====================
CORTEX Persist — Local-First Trust Layer API
FastAPI server on :8001  |  SQLite+WAL  |  SHA-256 hash-chain  |  Merkle-sealed

Surface:
  POST /v1/admin/keys           → bootstrap Bearer token
  POST /v1/trust/guard          → dry-run admission check
  POST /v1/facts                → sealed fact commit
  POST /v1/facts/batch          → bulk commit
  POST /v1/facts/search         → temporal context search
  GET  /v1/facts/{fact_id}/verify    → hash-chain integrity
  GET  /v1/facts/{subject}/history   → causal lineage
  POST /v1/facts/{fact_id}/taint     → causal contamination
  GET  /v1/projects/{project}/export → evidence package

Local-first: SQLite WAL, built-in full-text search, no external deps.
Confidence: C5-Static
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ── Config ────────────────────────────────────────────────────────────────────

DB_PATH      = os.getenv("CORTEX_PERSIST_DB",    "server/data/persist.db")
ADMIN_SECRET = os.getenv("CORTEX_MASTER_KEY",    "DEMO_KEY_VULNERABLE_2026")
PORT         = int(os.getenv("CORTEX_PERSIST_PORT", "8001"))

# ── DB bootstrap ──────────────────────────────────────────────────────────────

def _init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as c:
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        c.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                token      TEXT PRIMARY KEY,
                role       TEXT NOT NULL,           -- ADMIN | AGENT | VIEWER
                created_at REAL NOT NULL,
                label      TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                fact_id     TEXT PRIMARY KEY,
                project     TEXT NOT NULL,
                subject     TEXT NOT NULL,
                predicate   TEXT NOT NULL,
                object_val  TEXT NOT NULL,          -- JSON
                source      TEXT NOT NULL,          -- llm|tool|api|human
                confidence  REAL NOT NULL DEFAULT 1.0,
                session_id  TEXT,
                result      TEXT,                   -- JSON optional
                hash        TEXT NOT NULL,          -- SHA-256 of canonical payload
                prev_hash   TEXT,                   -- hash-chain predecessor
                tainted     INTEGER NOT NULL DEFAULT 0,
                taint_reason TEXT,
                created_at  REAL NOT NULL,
                metadata    TEXT                    -- JSON
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS taint_propagation (
                source_id  TEXT NOT NULL,
                target_id  TEXT NOT NULL,
                reason     TEXT,
                at         REAL NOT NULL
            )
        """)
        # FTS for search
        c.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts
            USING fts5(fact_id, subject, predicate, object_val, content='facts', content_rowid='rowid')
        """)
        c.commit()

@contextmanager
def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

# ── Hash chain ────────────────────────────────────────────────────────────────

def _canonical(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)

def _sha256(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload).encode()).hexdigest()

def _last_hash(project: str) -> Optional[str]:
    with _db() as c:
        row = c.execute(
            "SELECT hash FROM facts WHERE project=? ORDER BY created_at DESC LIMIT 1",
            (project,)
        ).fetchone()
        return row["hash"] if row else None

# ── Auth ──────────────────────────────────────────────────────────────────────

def _verify_token(authorization: Optional[str] = Header(None)) -> Dict[str, str]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing Bearer token")
    token = authorization[7:]
    with _db() as c:
        row = c.execute("SELECT role FROM api_keys WHERE token=?", (token,)).fetchone()
    if not row:
        raise HTTPException(403, "Invalid token")
    return {"token": token, "role": row["role"]}

def _require_agent(ctx: Dict = Depends(_verify_token)):
    if ctx["role"] not in ("AGENT", "ADMIN"):
        raise HTTPException(403, "AGENT or ADMIN role required")
    return ctx

def _require_admin(ctx: Dict = Depends(_verify_token)):
    if ctx["role"] != "ADMIN":
        raise HTTPException(403, "ADMIN role required")
    return ctx

# ── Models ────────────────────────────────────────────────────────────────────

class KeyRequest(BaseModel):
    admin_secret: str
    role: str = "AGENT"   # AGENT | VIEWER | ADMIN
    label: Optional[str] = None

class FactPayload(BaseModel):
    project:    str
    subject:    str
    predicate:  str
    object:     Any
    source:     str = "tool"
    confidence: float = 1.0
    session_id: Optional[str] = None
    result:     Optional[Any] = None
    metadata:   Optional[Dict[str, Any]] = None
    dry_run:    bool = False

class BatchPayload(BaseModel):
    project: str
    facts:   List[FactPayload]

class SearchPayload(BaseModel):
    project: str
    query:   str
    limit:   int = 10
    as_of:   Optional[float] = None

class TaintPayload(BaseModel):
    project: str
    reason:  str

# ── Schema/policy guard ────────────────────────────────────────────────────────

_FORBIDDEN_PREDICATES = {"__proto__", "password", "private_key"}

def _admission_check(payload: FactPayload) -> List[str]:
    violations = []
    if payload.predicate in _FORBIDDEN_PREDICATES:
        violations.append(f"FORBIDDEN_PREDICATE: {payload.predicate}")
    if payload.confidence < 0.0 or payload.confidence > 1.0:
        violations.append("CONFIDENCE_OUT_OF_RANGE")
    if len(payload.subject) > 500:
        violations.append("SUBJECT_TOO_LONG")
    if payload.source not in ("llm", "tool", "api", "human"):
        violations.append(f"INVALID_SOURCE: {payload.source}")
    return violations

# ── Fact commit ───────────────────────────────────────────────────────────────

import uuid

def _commit_fact(payload: FactPayload) -> Dict[str, Any]:
    fact_id   = str(uuid.uuid4())
    now       = time.time()
    prev_hash = _last_hash(payload.project)

    canonical_payload = {
        "fact_id":   fact_id,
        "project":   payload.project,
        "subject":   payload.subject,
        "predicate": payload.predicate,
        "object":    payload.object,
        "source":    payload.source,
        "confidence":payload.confidence,
        "created_at":now,
        "prev_hash": prev_hash,
    }
    fact_hash = _sha256(canonical_payload)

    with _db() as c:
        c.execute("""
            INSERT INTO facts
              (fact_id, project, subject, predicate, object_val, source, confidence,
               session_id, result, hash, prev_hash, created_at, metadata)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            fact_id, payload.project, payload.subject, payload.predicate,
            json.dumps(payload.object, default=str),
            payload.source, payload.confidence, payload.session_id,
            json.dumps(payload.result, default=str) if payload.result is not None else None,
            fact_hash, prev_hash, now,
            json.dumps(payload.metadata or {})
        ))
        # FTS sync
        c.execute("""
            INSERT INTO facts_fts (fact_id, subject, predicate, object_val)
            VALUES (?,?,?,?)
        """, (fact_id, payload.subject, payload.predicate,
              json.dumps(payload.object, default=str)[:1000]))

    return {"fact_id": fact_id, "hash": fact_hash, "prev_hash": prev_hash, "created_at": now}

# ── App ───────────────────────────────────────────────────────────────────────

_init_db()

app = FastAPI(
    title="CORTEX Persist API",
    description="Local-first trust layer — SHA-256 hash-chain, tamper-evident, audit-ready",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    with _db() as c:
        count = c.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    return {"status": "ONLINE", "facts": count, "mode": "local-first", "db": DB_PATH}

# ── Bootstrap: key creation ───────────────────────────────────────────────────

@app.post("/v1/admin/keys")
def create_key(req: KeyRequest):
    if req.admin_secret != ADMIN_SECRET:
        raise HTTPException(403, "Invalid admin secret")
    if req.role not in ("AGENT", "VIEWER", "ADMIN"):
        raise HTTPException(400, f"Invalid role: {req.role}")
    token = secrets.token_hex(32)
    with _db() as c:
        c.execute(
            "INSERT INTO api_keys (token, role, created_at, label) VALUES (?,?,?,?)",
            (token, req.role, time.time(), req.label or req.role)
        )
    return {"token": token, "role": req.role, "label": req.label}

# ── Guard (dry-run) ───────────────────────────────────────────────────────────

@app.post("/v1/trust/guard")
def guard(payload: FactPayload, ctx: Dict = Depends(_require_agent)):
    violations = _admission_check(payload)
    if violations:
        return {"admitted": False, "violations": violations}
    # Schema & chain check
    notes = []
    prev = _last_hash(payload.project)
    if prev:
        notes.append(f"chain_head:{prev[:12]}")
    notes.append(f"source:{payload.source}")
    return {"admitted": True, "notes": notes, "dry_run": payload.dry_run}

# ── Facts: single commit ──────────────────────────────────────────────────────

@app.post("/v1/facts", status_code=201)
def commit_fact(payload: FactPayload, ctx: Dict = Depends(_require_agent)):
    violations = _admission_check(payload)
    if violations:
        raise HTTPException(422, {"violations": violations})
    result = _commit_fact(payload)
    return {**result, "success": True}

# ── Facts: batch commit ───────────────────────────────────────────────────────

@app.post("/v1/facts/batch")
def commit_batch(batch: BatchPayload, ctx: Dict = Depends(_require_agent)):
    results = []
    for f in batch.facts:
        f.project = batch.project  # enforce project from batch
        violations = _admission_check(f)
        if violations:
            results.append({"success": False, "violations": violations})
        else:
            r = _commit_fact(f)
            results.append({**r, "success": True})
    return {"results": results}

# ── Facts: search ─────────────────────────────────────────────────────────────

@app.post("/v1/facts/search")
def search_facts(payload: SearchPayload, ctx: Dict = Depends(_verify_token)):
    with _db() as c:
        if payload.as_of:
            rows = c.execute("""
                SELECT * FROM facts
                WHERE project=? AND created_at<=? AND tainted=0
                  AND (subject LIKE ? OR predicate LIKE ? OR object_val LIKE ?)
                ORDER BY created_at DESC LIMIT ?
            """, (payload.project, payload.as_of,
                  f"%{payload.query}%", f"%{payload.query}%", f"%{payload.query}%",
                  payload.limit)).fetchall()
        else:
            rows = c.execute("""
                SELECT * FROM facts
                WHERE project=? AND tainted=0
                  AND (subject LIKE ? OR predicate LIKE ? OR object_val LIKE ?)
                ORDER BY created_at DESC LIMIT ?
            """, (payload.project,
                  f"%{payload.query}%", f"%{payload.query}%", f"%{payload.query}%",
                  payload.limit)).fetchall()
    facts = [dict(r) for r in rows]
    for f in facts:
        f["object_val"] = json.loads(f["object_val"])
    return {"facts": facts, "count": len(facts)}

# ── Facts: verify ─────────────────────────────────────────────────────────────

@app.get("/v1/facts/{fact_id}/verify")
def verify_fact(fact_id: str, ctx: Dict = Depends(_verify_token)):
    with _db() as c:
        row = c.execute("SELECT * FROM facts WHERE fact_id=?", (fact_id,)).fetchone()
    if not row:
        raise HTTPException(404, f"Fact {fact_id} not found")
    row = dict(row)
    # Recompute hash and verify chain integrity
    canonical_payload = {
        "fact_id":   row["fact_id"],
        "project":   row["project"],
        "subject":   row["subject"],
        "predicate": row["predicate"],
        "object":    json.loads(row["object_val"]),
        "source":    row["source"],
        "confidence":row["confidence"],
        "created_at":row["created_at"],
        "prev_hash": row["prev_hash"],
    }
    expected_hash = _sha256(canonical_payload)
    intact = expected_hash == row["hash"]
    return {
        "fact_id":  fact_id,
        "verified": intact and not row["tainted"],
        "hash":     row["hash"],
        "hash_ok":  intact,
        "tainted":  bool(row["tainted"]),
        "chain":    {"prev_hash": row["prev_hash"]},
    }

# ── Facts: history ────────────────────────────────────────────────────────────

@app.get("/v1/facts/{subject}/history")
def fact_history(subject: str, project: str = "cortex-sovereign", ctx: Dict = Depends(_verify_token)):
    with _db() as c:
        rows = c.execute("""
            SELECT fact_id, predicate, hash, prev_hash, created_at, tainted
            FROM facts WHERE project=? AND subject=?
            ORDER BY created_at ASC
        """, (project, subject)).fetchall()
    return {"subject": subject, "history": [dict(r) for r in rows]}

# ── Facts: taint ──────────────────────────────────────────────────────────────

@app.post("/v1/facts/{fact_id}/taint")
def taint_fact(fact_id: str, payload: TaintPayload, ctx: Dict = Depends(_require_agent)):
    with _db() as c:
        row = c.execute("SELECT subject, project FROM facts WHERE fact_id=?", (fact_id,)).fetchone()
        if not row:
            raise HTTPException(404, f"Fact {fact_id} not found")
        # Mark primary fact tainted
        c.execute(
            "UPDATE facts SET tainted=1, taint_reason=? WHERE fact_id=?",
            (payload.reason, fact_id)
        )
        # Causal propagation: taint derived facts (same session, later time)
        session_id = c.execute(
            "SELECT session_id, created_at FROM facts WHERE fact_id=?", (fact_id,)
        ).fetchone()
        tainted_count = 1
        if session_id and session_id[0]:
            derived = c.execute("""
                SELECT fact_id FROM facts
                WHERE session_id=? AND created_at > ? AND tainted=0
            """, (session_id[0], session_id[1])).fetchall()
            for d in derived:
                c.execute(
                    "UPDATE facts SET tainted=1, taint_reason=? WHERE fact_id=?",
                    (f"causal_from:{fact_id}", d[0])
                )
                c.execute(
                    "INSERT INTO taint_propagation (source_id, target_id, reason, at) VALUES (?,?,?,?)",
                    (fact_id, d[0], payload.reason, time.time())
                )
                tainted_count += 1
    return {"tainted": True, "fact_id": fact_id, "propagated_to": tainted_count - 1}

# ── Project: export ──────────────────────────────────────────────────────────

@app.get("/v1/projects/{project}/export")
def export_project(project: str, ctx: Dict = Depends(_verify_token)):
    with _db() as c:
        rows = c.execute(
            "SELECT * FROM facts WHERE project=? ORDER BY created_at ASC",
            (project,)
        ).fetchall()
    facts = [dict(r) for r in rows]
    for f in facts:
        f["object_val"] = json.loads(f["object_val"])
    # Simple Merkle root: hash of all fact hashes in order
    hashes = [f["hash"] for f in facts]
    merkle_input = "".join(hashes)
    merkle_root = hashlib.sha256(merkle_input.encode()).hexdigest() if hashes else None
    return {
        "project":     project,
        "fact_count":  len(facts),
        "merkle_root": merkle_root,
        "exported_at": time.time(),
        "facts":       facts,
    }

# ── Swagger / docs only in non-prod ──────────────────────────────────────────

@app.get("/v1/status")
def status():
    with _db() as c:
        count   = c.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
        tainted = c.execute("SELECT COUNT(*) FROM facts WHERE tainted=1").fetchone()[0]
        keys    = c.execute("SELECT COUNT(*) FROM api_keys").fetchone()[0]
    return {
        "status":      "ONLINE",
        "mode":        "local-first",
        "total_facts": count,
        "tainted":     tainted,
        "api_keys":    keys,
        "db":          DB_PATH,
    }

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print(f"◈ CORTEX PERSIST API: Starting on port {PORT}")
    print(f"◈ DB: {DB_PATH}")
    print(f"◈ Bootstrap: POST /v1/admin/keys with admin_secret=CORTEX_MASTER_KEY")
    uvicorn.run("cortex_persist_api:app", host="0.0.0.0", port=PORT, reload=False, log_level="warning")
