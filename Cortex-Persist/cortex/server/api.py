"""
Agents.archi_persist_api.py
=====================
Agents.archi Persist — Local-First Trust Layer API
FastAPI server on :8001  |  SQLite+WAL  |  SHA-256 hash-chain  |  Merkle-sealed
"""

from __future__ import annotations
import hashlib
import json
import os
import secrets
import sqlite3
import time
import uuid
import asyncio
from contextlib import contextmanager
from typing import Any, Dict, List, Optional
from fastapi import Depends, FastAPI, HTTPException, Header, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Deterministic Substrate (Law Ω9) ──────────────────────────────────────────
class XORShift:
    def __init__(self, seed: int):
        self.state = seed & 0xFFFFFFFF
    
    def next(self) -> float:
        # 32-bit XORShift algorithm
        self.state ^= (self.state << 13) & 0xFFFFFFFF
        self.state ^= (self.state >> 17) & 0xFFFFFFFF
        self.state ^= (self.state << 5) & 0xFFFFFFFF
        return (self.state & 0xFFFFFF) / 0x1000000

DETERMINISTIC_PRNG = XORShift(0x5056)

# Internal CORTEX Imports
from cortex.agentic.agent_stability_governor import AgentStabilityGovernor, SovereignSignalSample
from cortex.gateway_factory import get_standard_gateway
from cortex.archi_core import get_archi_architect
from cortex.archi_forge import get_archi_forge

# ── Config ────────────────────────────────────────────────────────────────────
DB_PATH      = os.getenv("CORTEX_PERSIST_DB",    "cortex/data/persist.db")
ADMIN_SECRET = os.getenv("CORTEX_MASTER_KEY",    "DEMO_KEY_VULNERABLE_2026")
PORT         = int(os.getenv("CORTEX_PERSIST_PORT", "8001"))
LEDGER_PATH  = os.getenv("CORTEX_LEDGER_PATH", "cortex/data/forensic_ledger.jsonl")
BUILD_VER    = "v2.1.0-alpha"

# ── App Initialization ────────────────────────────────────────────────────────
app = FastAPI(
    title="Agents.archi Persist API",
    description="Local-first trust layer — SHA-256 hash-chain, tamper-evident, audit-ready",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global Engines ────────────────────────────────────────────────────────────
gateway = get_standard_gateway()
architect = get_archi_architect(gateway)
forge = get_archi_forge(workspace_root=os.getcwd())
governor = AgentStabilityGovernor()

# ── DB bootstrap ──────────────────────────────────────────────────────────────
def _init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as c:
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        c.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                token      TEXT PRIMARY KEY,
                role       TEXT NOT NULL,
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
                object_val  TEXT NOT NULL,
                source      TEXT NOT NULL,
                confidence  REAL NOT NULL DEFAULT 1.0,
                session_id  TEXT,
                result      TEXT,
                hash        TEXT NOT NULL,
                prev_hash   TEXT,
                tainted     INTEGER NOT NULL DEFAULT 0,
                taint_reason TEXT,
                created_at  REAL NOT NULL,
                metadata    TEXT
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
    role: str = "AGENT"
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

class HomeostasisUpdate(BaseModel):
    setpoint: Optional[float] = None
    kp: Optional[float] = None
    ki: Optional[float] = None
    kd: Optional[float] = None

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

# ── Admission Guard ───────────────────────────────────────────────────────────
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

# ── WebSocket Manager ─────────────────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

# ── Fact Core ─────────────────────────────────────────────────────────────────
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
        c.execute("""
            INSERT INTO facts_fts (fact_id, subject, predicate, object_val)
            VALUES (?,?,?,?)
        """, (fact_id, payload.subject, payload.predicate,
              json.dumps(payload.object, default=str)[:1000]))

    return {"fact_id": fact_id, "hash": fact_hash, "prev_hash": prev_hash, "created_at": now}

async def _commit_fact_and_broadcast(payload: FactPayload) -> Dict[str, Any]:
    result = _commit_fact(payload)
    asyncio.create_task(manager.broadcast({
        "type": "FACT_COMMITTED",
        "data": {
            "fact_id": result["fact_id"],
            "project": payload.project,
            "subject": payload.subject,
            "predicate": payload.predicate,
            "hash": result["hash"],
            "created_at": result["created_at"]
        }
    }))
    return result

# ── Homeostasis Engine ────────────────────────────────────────────────────────
@app.post("/v1/homeostasis/pulse")
async def homeostasis_pulse(payload: Dict[str, Any], ctx: Dict = Depends(_require_agent)):
    """Primary Control-Rate entry for Sovereign Telemetry."""
    try:
        sample = SovereignSignalSample(
            ts=time.time(),
            dt=payload.get("dt", 1.0),
            exergy=payload.get("exergy", 0.5),
            entropy=payload.get("entropy", 0.1),
            risk=payload.get("risk", 0.0),
            impact=payload.get("impact", 0.0),
            sample_id=payload.get("sample_id", "pulse")
        )
        pulse = governor.tick(sample)
        asyncio.create_task(manager.broadcast({"type": "HARMONIC_PULSE", "data": pulse}))
        return pulse
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def homeostasis_loop():
    """Background task (Simulated telemetry when headless)."""
    while True:
        try:
            now = time.time()
            sample = SovereignSignalSample(
                ts=now, dt=1.0,
                exergy=0.5 + (DETERMINISTIC_PRNG.next() * 0.3),
                entropy=0.1 + (DETERMINISTIC_PRNG.next() * 0.4),
                risk=0.01 * (int(DETERMINISTIC_PRNG.next() * 10)),
                impact=0.0,
                sample_id="background_pulse"
            )
            pulse = governor.tick(sample)
            await manager.broadcast({"type": "HARMONIC_PULSE", "data": pulse})
            
            # Ledger Record
            log_entry = {
                "ts": now, "mode": pulse["mode"], "u": pulse["u"],
                "rule": pulse["rule"], "policy": pulse["policy"], "metrics": pulse["metrics"]
            }
            with open(LEDGER_PATH, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
             print(f"◈ [HOMEODYNAMIS_ERROR] {e}")
        await asyncio.sleep(1.0)

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
    notes = []
    prev = _last_hash(payload.project)
    if prev:
        notes.append(f"chain_head:{prev[:12]}")
    notes.append(f"source:{payload.source}")
    return {"admitted": True, "notes": notes, "dry_run": payload.dry_run}

# ── Facts Surface ─────────────────────────────────────────────────────────────
@app.post("/v1/facts", status_code=201)
async def commit_fact(payload: FactPayload, ctx: Dict = Depends(_require_agent)):
    violations = _admission_check(payload)
    if violations:
        raise HTTPException(422, {"violations": violations})
    result = await _commit_fact_and_broadcast(payload)
    return {**result, "success": True}

@app.post("/v1/facts/batch")
def commit_batch(batch: BatchPayload, ctx: Dict = Depends(_require_agent)):
    results = []
    for f in batch.facts:
        f.project = batch.project
        violations = _admission_check(f)
        if violations:
            results.append({"success": False, "violations": violations})
        else:
            r = _commit_fact(f)
            results.append({**r, "success": True})
    return {"results": results}

@app.post("/v1/facts/search")
def search_facts(payload: SearchPayload, ctx: Dict = Depends(_verify_token)):
    with _db() as c:
        if payload.as_of:
            rows = c.execute("""
                SELECT * FROM facts
                WHERE project=? AND created_at<=? AND tainted=0
                  AND (subject LIKE ? OR predicate LIKE ? OR object_val LIKE ?)
                ORDER BY created_at DESC LIMIT ?
            """, (payload.project, payload.as_of, f"%{payload.query}%", f"%{payload.query}%", f"%{payload.query}%", payload.limit)).fetchall()
        else:
            rows = c.execute("""
                SELECT * FROM facts
                WHERE project=? AND tainted=0
                  AND (subject LIKE ? OR predicate LIKE ? OR object_val LIKE ?)
                ORDER BY created_at DESC LIMIT ?
            """, (payload.project, f"%{payload.query}%", f"%{payload.query}%", f"%{payload.query}%", payload.limit)).fetchall()
    facts = [dict(r) for r in rows]
    for f in facts:
        f["object_val"] = json.loads(f["object_val"])
    return {"facts": facts, "count": len(facts)}

@app.get("/v1/facts/{fact_id}/verify")
def verify_fact(fact_id: str, ctx: Dict = Depends(_verify_token)):
    with _db() as c:
        row = c.execute("SELECT * FROM facts WHERE fact_id=?", (fact_id,)).fetchone()
    if not row:
        raise HTTPException(404, f"Fact {fact_id} not found")
    row = dict(row)
    canonical_payload = {
        "fact_id": row["fact_id"], "project": row["project"], "subject": row["subject"],
        "predicate": row["predicate"], "object": json.loads(row["object_val"]),
        "source": row["source"], "confidence": row["confidence"],
        "created_at": row["created_at"], "prev_hash": row["prev_hash"],
    }
    expected_hash = _sha256(canonical_payload)
    intact = expected_hash == row["hash"]
    return {"fact_id": fact_id, "verified": intact and not row["tainted"], "hash_ok": intact}

# ── Homeostasis Control ───────────────────────────────────────────────────────
@app.post("/v1/homeostasis/control")
async def update_homeostasis(req: HomeostasisUpdate, ctx: Dict = Depends(_require_agent)):
    if req.setpoint is not None:
        governor.set_target(req.setpoint)
    governor.update_params(req.kp, req.ki, req.kd)
    return {"status": "UPDATED", "governor": governor.state.__dict__}

# ── WebSockets: Telemetry ─────────────────────────────────────────────────────
@app.websocket("/v1/telemetry")
async def telemetry_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json({"type": "SYSTEM_CONNECTED", "data": {"version": "1.0.0", "time": time.time()}})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ── Archi Directive Loop ──────────────────────────────────────────────────────
class ArchiDirective(BaseModel):
    prompt: str

@app.get("/v1/archi/history")
def archi_history(ctx: Dict = Depends(_verify_token)):
    """Retrieve recent synthesis history for the ARCHI_CORE project."""
    project = "ARCHI_CORE"
    with _db() as c:
        rows = c.execute("""
            SELECT fact_id, subject, predicate, object_val, created_at FROM facts
            WHERE project=? AND predicate='SYNTHESIS_COMPLETE'
            ORDER BY created_at DESC LIMIT 10
        """, (project,)).fetchall()
    
    history = []
    for r in rows:
        obj = json.loads(r["object_val"])
        # Prioritize original prompt, fallback to manifest concept
        directive = obj.get("prompt") or obj.get("manifest", {}).get("concept", "Unknown Directive")
        history.append({
            "id": r["fact_id"],
            "directive": directive,
            "timestamp": r["created_at"],
            "status": "sealed"
        })
    return history

@app.post("/v1/archi/directive")
async def archi_directive(request: ArchiDirective, ctx: Dict = Depends(_require_agent)):
    start_time = time.time()
    project = "ARCHI_CORE"
    try:
        # 1. Architects the Manifest
        manifest = await architect.compile_directive(request.prompt)
        
        # 2. Forges the Product
        forge_results = forge.execute_manifest(manifest)
        
        # 3. Commits to Ledger via Canonical Fact Handler
        payload = FactPayload(
            project=project,
            subject="PRODUCT_SYNTHESIS",
            predicate="SYNTHESIS_COMPLETE",
            object={
                "prompt": request.prompt,
                "manifest": manifest, 
                "forge_results": forge_results
            },
            source="archi",
            confidence=1.0
        )
        result = await _commit_fact_and_broadcast(payload)
        fact_id = result["fact_id"]
        
        return {"status": "SUCCESS", "fact_id": fact_id, "latency": time.time() - start_time, "manifest": manifest}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Lifecycle ─────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    _init_db()
    asyncio.create_task(homeostasis_loop())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("cortex.server.api:app", host="0.0.0.0", port=PORT, reload=False)
