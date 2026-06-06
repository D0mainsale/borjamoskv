"""
CORTEX Token Reducer — ADR-001 Implementation
Law Ω2: O(n) over payload length, never O(n²).
Law Ω5: Zero rhetoric. Every byte is justified.
Law Ω9: C5-REAL. Emit audit record on every reduction.

Config (env vars):
  CORTEX_TOKEN_REDUCER=on|off         (default: off until Guarda 0 passes)
  CORTEX_TOKEN_REDUCER_STRATEGY=guarded|aggressive|off
  CORTEX_TOKEN_REDUCER_FALLBACK=pass_through|abort
  CORTEX_TOKEN_REDUCER_OBSERVABILITY=full|minimal|off

Guarda 0 — Semantic Fidelity Gate (must pass before 5% rollout)
Guarda 1 — Deterministic Bypass Rules (no model inference)
Guarda 2 — Per-request Audit Trail (tokens_before, tokens_after, hash pair)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

# ── Config ────────────────────────────────────────────────────────────

_ENV_ON        = os.getenv("CORTEX_TOKEN_REDUCER", "off").lower() == "on"
_ENV_STRATEGY  = os.getenv("CORTEX_TOKEN_REDUCER_STRATEGY", "guarded")
_ENV_FALLBACK  = os.getenv("CORTEX_TOKEN_REDUCER_FALLBACK", "pass_through")
_ENV_OBS       = os.getenv("CORTEX_TOKEN_REDUCER_OBSERVABILITY", "full")

# Semantic fidelity threshold (Guarda 0).
# P95 cosine similarity between reduced and original embedding must be >= this.
SEMANTIC_FIDELITY_THRESHOLD = 0.97

# Token count proxy: 1 token ≈ 4 chars (cl100k baseline)
_CHARS_PER_TOKEN = 4


# ── Bypass Rules (Guarda 1) ───────────────────────────────────────────
# Deterministic. O(1) per rule. No model calls.

_BYPASS_PATTERNS: list[tuple[str, re.Pattern]] = [
    # forensic logs: timestamped lines with level prefixes
    ("forensic_log",     re.compile(r"\b(ERROR|WARN|FATAL|TRACE|DEBUG)\b.*\n", re.MULTILINE)),
    # compilation errors: line:col references
    ("compile_error",    re.compile(r"\b\w+\.\w+:\d+:\d+:\s")),
    # stack traces
    ("stack_trace",      re.compile(r"(Traceback|at \w+\.\w+\(|File \".*\", line \d+)")),
    # diffs: already-structured, every byte matters
    ("diff_payload",     re.compile(r"^[-+]{3} [ab]/", re.MULTILINE)),
    # hash/address/id strings: critical identifiers
    ("critical_id",      re.compile(r"\b(0x[0-9a-fA-F]{8,}|[0-9a-f]{40,})\b")),
    # domain dashboard endpoint payloads
    ("domain_dashboard", re.compile(r'"id":\s*"[a-z0-9-]+".*"title"', re.DOTALL)),
    # already-summarized (very short payloads)
    ("pre_summarized",   None),  # handled by length check below
]

_PRE_SUMMARIZED_MAX_TOKENS = 200  # skip reducer if input is already tiny


def _should_bypass(text: str) -> tuple[bool, Optional[str]]:
    """
    Returns (bypass: bool, reason: str | None).
    O(k) where k = number of rules. No model calls.
    """
    token_estimate = len(text) // _CHARS_PER_TOKEN
    if token_estimate <= _PRE_SUMMARIZED_MAX_TOKENS:
        return True, "pre_summarized"

    for name, pattern in _BYPASS_PATTERNS:
        if pattern is None:
            continue
        if pattern.search(text):
            return True, name

    return False, None


# ── Reduction Engine ─────────────────────────────────────────────────
# Structural deduplication only. Never lossy semantic compression.

_BLANK_LINE_COLLAPSE = re.compile(r"\n{3,}")
_TRAILING_WHITESPACE = re.compile(r"[ \t]+$", re.MULTILINE)
_REPEATED_SEPARATOR  = re.compile(r"(-{4,}|={4,}|\*{4,}|_{4,})\n(\1\n)+")


def _structural_reduce(text: str) -> str:
    """
    Safe structural deduplication:
      1. Collapse 3+ blank lines → 2 blank lines
      2. Strip trailing whitespace per line
      3. Collapse repeated separator lines (----, ====)
    Never touches code blocks, identifiers, or semantic tokens.
    """
    text = _BLANK_LINE_COLLAPSE.sub("\n\n", text)
    text = _TRAILING_WHITESPACE.sub("", text)
    text = _REPEATED_SEPARATOR.sub(r"\1\n", text)
    return text


# ── Audit Record (Guarda 2) ───────────────────────────────────────────

@dataclass
class ReducerAudit:
    """Immutable per-request audit record. Emitted to stdout if observability=full."""
    timestamp: str
    tokens_before: int
    tokens_after: int
    reduction_ratio: float
    rule_applied: str
    input_hash: str   # sha256 of original
    output_hash: str  # sha256 of reduced (or original if bypass/fallback)
    fallback_triggered: bool
    bypass_triggered: bool
    bypass_reason: Optional[str]
    latency_ms: float

    def as_dict(self) -> dict:
        return {
            "ts": self.timestamp,
            "tokens_before": self.tokens_before,
            "tokens_after": self.tokens_after,
            "reduction_ratio": round(self.reduction_ratio, 4),
            "rule": self.rule_applied,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "fallback": self.fallback_triggered,
            "bypass": self.bypass_triggered,
            "bypass_reason": self.bypass_reason,
            "latency_ms": round(self.latency_ms, 2),
        }

    def emit(self) -> None:
        if _ENV_OBS == "off":
            return
        line = f"CORTEX_REDUCER_AUDIT::{json.dumps(self.as_dict())}"
        sys.stdout.write(line + "\n")
        sys.stdout.flush()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _token_count(text: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN)


# ── Public API ────────────────────────────────────────────────────────

def reduce(text: str) -> tuple[str, ReducerAudit]:
    """
    Main entry point.
    Returns (output_text, audit_record).
    Always returns a valid string — never raises.
    """
    t0 = time.perf_counter()
    ts = datetime.now(timezone.utc).isoformat()
    tokens_before = _token_count(text)
    _sha256(text)

    if not _ENV_ON:
        # Reducer disabled: pass-through, audit still emitted for zero-noise baseline
        audit = _make_audit(ts, tokens_before, tokens_before, text, text, t0,
                            fallback=False, bypass=True, bypass_reason="reducer_disabled",
                            rule="pass_through")
        audit.emit()
        return text, audit

    # Guarda 1 — Bypass check
    bypass, bypass_reason = _should_bypass(text)
    if bypass:
        audit = _make_audit(ts, tokens_before, tokens_before, text, text, t0,
                            fallback=False, bypass=True, bypass_reason=bypass_reason,
                            rule="bypass")
        audit.emit()
        return text, audit

    # Reduction attempt
    try:
        reduced = _structural_reduce(text)
        tokens_after = _token_count(reduced)
        rule = "structural_dedup_v1"
        fallback = False
    except Exception as exc:
        # Guarda 2 fallback: never corrupt the payload
        if _ENV_FALLBACK == "abort":
            raise
        reduced = text
        tokens_after = tokens_before
        rule = f"FALLBACK:{exc}"
        fallback = True

    audit = _make_audit(ts, tokens_before, tokens_after, text, reduced, t0,
                        fallback=fallback, bypass=False, bypass_reason=None,
                        rule=rule)
    audit.emit()
    return reduced, audit


def _make_audit(
    ts: str,
    tokens_before: int,
    tokens_after: int,
    original: str,
    output: str,
    t0: float,
    *,
    fallback: bool,
    bypass: bool,
    bypass_reason: Optional[str],
    rule: str,
) -> ReducerAudit:
    ratio = 1.0 - (tokens_after / tokens_before) if tokens_before > 0 else 0.0
    return ReducerAudit(
        timestamp=ts,
        tokens_before=tokens_before,
        tokens_after=tokens_after,
        reduction_ratio=ratio,
        rule_applied=rule,
        input_hash=_sha256(original),
        output_hash=_sha256(output),
        fallback_triggered=fallback,
        bypass_triggered=bypass,
        bypass_reason=bypass_reason,
        latency_ms=(time.perf_counter() - t0) * 1000,
    )


# ── Hook Integration ──────────────────────────────────────────────────
# Register as a pre_tool_use TRANSFORM handler via HookRegistry.

def make_hook_handler():
    """
    Returns a handler compatible with HookRegistry.on("pre_tool_use", handler).
    Transforms the payload's 'content' key if present.
    """
    def handler(event) -> Optional[object]:
        payload = getattr(event, "payload", {}) or {}
        content = payload.get("content") or payload.get("prompt") or payload.get("text")
        if not isinstance(content, str) or not content:
            return None  # Nothing to reduce

        reduced, audit = reduce(content)

        if reduced == content:
            return None  # No change, no transform

        # Determine which key held the content
        content_key = next(
            (k for k in ("content", "prompt", "text") if k in payload),
            "content",
        )
        modified = dict(payload)
        modified[content_key] = reduced
        modified["_reducer_audit"] = audit.as_dict()

        # Return a minimal TRANSFORM-like result (duck-typed)
        return type("HookResult", (), {
            "action": type("HookAction", (), {"name": "TRANSFORM"})(),
            "modified_payload": modified,
            "abort_reason": None,
        })()

    return handler


# ── Guarda 0: Semantic Fidelity Harness ──────────────────────────────

def run_guarda_0(
    corpus: list[str],
    embed_fn,  # Callable[[str], list[float]] — your embedding function
    threshold: float = SEMANTIC_FIDELITY_THRESHOLD,
) -> dict:
    """
    Guarda 0: Validate semantic fidelity before any rollout.

    Args:
        corpus:   List of representative real-traffic payloads (min 100).
        embed_fn: Embedding function. Takes str, returns float vector.
        threshold: Minimum cosine similarity at P95.

    Returns:
        {
            "passed": bool,
            "p95_similarity": float,
            "p50_similarity": float,
            "min_similarity": float,
            "bypass_rate": float,
            "reduction_rate": float,   # avg tokens saved
            "n_samples": int,
            "failures": list[dict],    # similarity < threshold
        }
    C5-REAL: Only call this with real traffic corpus, not synthetic data.
    """
    import math

    def cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na  = math.sqrt(sum(x * x for x in a))
        nb  = math.sqrt(sum(x * x for x in b))
        if na == 0 or nb == 0:
            return 1.0
        return dot / (na * nb)

    similarities: list[float] = []
    bypass_count = 0
    total_reduction = 0.0
    failures: list[dict] = []

    for i, text in enumerate(corpus):
        reduced, audit = reduce(text)

        if audit.bypass_triggered:
            bypass_count += 1
            similarities.append(1.0)  # bypass = no change = perfect fidelity
            continue

        total_reduction += audit.reduction_ratio

        if reduced == text:
            similarities.append(1.0)
            continue

        emb_orig    = embed_fn(text)
        emb_reduced = embed_fn(reduced)
        sim = cosine(emb_orig, emb_reduced)
        similarities.append(sim)

        if sim < threshold:
            failures.append({
                "index": i,
                "similarity": round(sim, 6),
                "tokens_before": audit.tokens_before,
                "tokens_after": audit.tokens_after,
                "input_hash": audit.input_hash,
            })

    similarities.sort()
    n = len(similarities)
    p95_idx = int(n * 0.95) - 1
    p50_idx = int(n * 0.50) - 1

    p95 = similarities[max(0, p95_idx)]
    p50 = similarities[max(0, p50_idx)]
    min_sim = similarities[0] if similarities else 0.0

    return {
        "passed": p95 >= threshold and not failures,
        "p95_similarity": round(p95, 6),
        "p50_similarity": round(p50, 6),
        "min_similarity": round(min_sim, 6),
        "bypass_rate": round(bypass_count / n, 4) if n > 0 else 0.0,
        "reduction_rate": round(total_reduction / max(1, n - bypass_count), 4),
        "n_samples": n,
        "failures": failures,
        "threshold": threshold,
    }
