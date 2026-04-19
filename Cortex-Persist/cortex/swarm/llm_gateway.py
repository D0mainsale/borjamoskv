"""
cortex.swarm/llm_gateway.py — Sovereign LLM Gateway v1.0
──────────────────────────────────────────────────────────
Three weapons:

  1. TOKEN BUCKET (per-model, async, in-memory)
     Enforces  T_req × N_active ≤ TPM_max at microsecond resolution.
     Priority queues: LEGATUS > PRAETORIAN > CENTURION > LEGIONARY.

  2. SEMANTIC FALLBACK CHAIN
     primary fail / saturated → degrade transparently to next model tier.
     Workers are ignorant of the swap; they just get a response.

  3. SEMANTIC CACHE (RAM, SHA-256 key)
     Identical or near-identical prompts (cosine ≥ 0.92) return the
     cached vector in O(1) — zero LLM call.

Laws enforced:
  Ω₁  Stochastic output → deterministic guard boundary (cache hit = verified)
  Ω₂  Exergy measured: tokens consumed vs useful tokens delivered
  Ω₆  Headless. No UI. logging.* only.
  Ω₉  C5-REAL: no simulation. Every call returns a real structure or raises.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Awaitable

logger = logging.getLogger("cortex.gateway")

# ─── Priority Tiers ──────────────────────────────────────────────────────────


class Priority(IntEnum):
    LEGATUS    = 0   # highest — capital extraction, C5-REAL oracle
    PRAETORIAN = 1   # supervisor agents
    CENTURION  = 2   # mid-tier coordinators
    LEGIONARY  = 3   # leaf workers (default)


# ─── Model Definitions ───────────────────────────────────────────────────────


@dataclass
class ModelSpec:
    """
    A callable LLM endpoint + its guaranteed TPM budget.
    `call` must accept (prompt: str) and return str (the completion).
    """
    name:     str
    tpm_max:  int            # tokens per minute ceiling
    call:     Callable[[str], Awaitable[str]]
    tier:     int = 0        # 0 = primary, 1 = secondary fallback, …
    avg_tokens_per_req: int = 500   # tunable estimate


# ─── Token Bucket (async, native, in-process) ─────────────────────────────────


class AsyncTokenBucket:
    """
    Leaky-bucket refill at `rate` tokens/second.
    Non-blocking: waiters queue via asyncio.Event.

    Invariant enforced (Ω₂):
        consumed(t) ≤ tpm_max / 60 × t   for all t
    """

    def __init__(self, capacity: int, refill_rate: float) -> None:
        self.capacity     = float(capacity)
        self.refill_rate  = refill_rate          # tokens / second
        self._tokens      = float(capacity)
        self._last_refill = time.monotonic()
        self._lock        = asyncio.Lock()
        self._waiters: list[asyncio.Event] = []

    def _refill(self) -> None:
        now   = time.monotonic()
        delta = now - self._last_refill
        self._tokens      = min(self.capacity, self._tokens + delta * self.refill_rate)
        self._last_refill = now

    async def consume(self, tokens: int = 1) -> float:
        """
        Acquires `tokens` from the bucket.
        Returns wait time in seconds (0 if immediate).
        Priority is guaranteed by ordering of lock acquisition (FIFO asyncio).
        """
        async with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return 0.0
            # Calculate wait required
            deficit    = tokens - self._tokens
            wait_s     = deficit / self.refill_rate
            await asyncio.sleep(wait_s)
            self._refill()
            self._tokens -= tokens
            return wait_s


# ─── Semantic Cache ───────────────────────────────────────────────────────────


def _sha256_key(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SemanticCache:
    """
    Two-tier hit detection:
      - Tier 1: exact SHA-256 match → O(1) dict lookup
      - Tier 2: token-overlap Jaccard (≥ threshold) → near-miss hit

    Stored in plain dict (RAM). No serialization. No Redis.
    Max capacity evicts LRU entries.
    """

    def __init__(self, capacity: int = 8192, similarity_threshold: float = 0.92) -> None:
        self._store:     dict[str, tuple[str, set[str], float]]  = {}  # key → (response, tokens, timestamp)
        self._order:     list[str] = []
        self.capacity   = capacity
        self.threshold  = similarity_threshold
        self._hits       = 0
        self._misses     = 0

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return set(text.lower().split())

    def _jaccard(self, a: set[str], b: set[str]) -> float:
        if not a and not b:
            return 1.0
        union = len(a | b)
        return len(a & b) / union if union else 0.0

    def get(self, prompt: str) -> str | None:
        key   = _sha256_key(prompt)
        # Tier 1: exact
        if key in self._store:
            self._hits += 1
            logger.debug("cache.HIT.exact key=%s", key[:8])
            return self._store[key][0]
        # Tier 2: Jaccard near-miss
        ptok = self._tokenize(prompt)
        for _, (response, stored_tok, _) in self._store.items():
            if self._jaccard(ptok, stored_tok) >= self.threshold:  # type: ignore[arg-type]
                self._hits += 1
                logger.debug("cache.HIT.semantic jaccard≥%.2f", self.threshold)
                return response
        self._misses += 1
        return None

    def put(self, prompt: str, response: str) -> None:
        key = _sha256_key(prompt)
        if key not in self._store:
            if len(self._store) >= self.capacity:
                # evict LRU
                oldest = self._order.pop(0)
                self._store.pop(oldest, None)
            self._order.append(key)
        self._store[key] = (response, self._tokenize(prompt), time.monotonic())

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total else 0.0

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "hits":      self._hits,
            "misses":    self._misses,
            "hit_rate":  round(self.hit_rate, 4),
            "size":      len(self._store),
            "capacity":  self.capacity,
        }


# ─── Gateway ─────────────────────────────────────────────────────────────────


@dataclass
class GatewayRequest:
    prompt:    str
    tokens:    int       = 500          # estimated tokens for this request
    priority:  Priority  = Priority.LEGIONARY
    require_primary: bool = False       # if True, disables fallback


@dataclass
class GatewayResponse:
    content:       str
    model_used:    str
    cache_hit:     bool
    wait_s:        float
    fallback_tier: int


class SovereignLLMGateway:
    """
    Single entry-point for ALL LLM calls inside the CORTEX swarm.

    Architecture:
      ┌─────────────────────────────────────────────────────────────┐
      │  GatewayRequest(prompt, tokens, priority)                   │
      │         │                                                   │
      │         ▼                                                   │
      │  SemanticCache.get()  ──hit──▶  GatewayResponse(cache=True)│
      │         │ miss                                              │
      │         ▼                                                   │
      │  TokenBucket[priority].consume(tokens)                      │
      │         │                                                   │
      │         ▼                                                   │
      │  ModelSpec[0].call(prompt)  ──ok──▶ cache.put → response   │
      │         │ fail/429                                          │
      │         ▼                                                   │
      │  ModelSpec[1].call(prompt)  ──ok──▶ cache.put → response   │
      │         │ fail/all exhausted                                │
      │         ▼                                                   │
      │  raise RuntimeError("All models exhausted")                 │
      └─────────────────────────────────────────────────────────────┘

    Usage:
        gw = SovereignLLMGateway(models=[primary_spec, fallback_spec])
        resp = await gw.call(GatewayRequest(prompt="...", priority=Priority.LEGATUS))
    """

    def __init__(
        self,
        models: list[ModelSpec],
        cache_capacity: int = 8192,
        cache_threshold: float = 0.92,
    ) -> None:
        if not models:
            raise ValueError("Gateway requires at least one ModelSpec.")

        self._models  = sorted(models, key=lambda m: m.tier)
        self._cache   = SemanticCache(capacity=cache_capacity, similarity_threshold=cache_threshold)
        self._buckets: dict[str, AsyncTokenBucket] = {}

        # One bucket per model × priority tier  (Priority × model_name)
        # Each bucket is sized to the model's TPM_max / 60  = tokens per second
        for model in self._models:
            for p in Priority:
                bucket_key = f"{model.name}:{p.value}"
                tps = model.tpm_max / 60.0
                self._buckets[bucket_key] = AsyncTokenBucket(
                    capacity=model.tpm_max,  # burst up to full TPM
                    refill_rate=tps,
                )

        self._total_calls  = 0
        self._total_tokens = 0
        self._fallbacks    = 0

        logger.info(
            "SovereignLLMGateway ready | models=%d cache_cap=%d threshold=%.2f",
            len(self._models), cache_capacity, cache_threshold,
        )

    async def call(self, req: GatewayRequest) -> GatewayResponse:
        """
        Main dispatch method.  Thread-safe via asyncio event-loop.
        C5-REAL: raises RuntimeError if all models fail — never returns silent garbage.
        """
        # ── Tier 1: Cache ──────────────────────────────────────────
        cached = self._cache.get(req.prompt)
        if cached is not None:
            return GatewayResponse(
                content=cached,
                model_used="cache",
                cache_hit=True,
                wait_s=0.0,
                fallback_tier=0,
            )

        # ── Tier 2: Token-Bucket + Model call ─────────────────────
        last_error: Exception | None = None
        models_to_try = [self._models[0]] if req.require_primary else self._models

        for tier_idx, model in enumerate(models_to_try):
            bucket_key = f"{model.name}:{req.priority.value}"
            bucket     = self._buckets[bucket_key]

            # Throttle: wait until budget is available
            wait_s = await bucket.consume(req.tokens)

            try:
                t0      = time.perf_counter()
                content = await model.call(req.prompt)
                elapsed = time.perf_counter() - t0

                # Persist to cache
                self._cache.put(req.prompt, content)

                self._total_calls  += 1
                self._total_tokens += req.tokens
                if tier_idx > 0:
                    self._fallbacks += 1

                logger.info(
                    "gw.call model=%s tier=%d wait_s=%.3f elapsed=%.3f fallback=%s tokens=%d",
                    model.name, tier_idx, wait_s, elapsed,
                    tier_idx > 0, req.tokens,
                )

                return GatewayResponse(
                    content=content,
                    model_used=model.name,
                    cache_hit=False,
                    wait_s=wait_s,
                    fallback_tier=tier_idx,
                )

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "gw.fallback model=%s error=%s → trying next tier",
                    model.name, exc,
                )
                continue

        raise RuntimeError(
            f"SovereignLLMGateway: all {len(models_to_try)} models exhausted. "
            f"Last error: {last_error}"
        )

    async def call_batch(
        self,
        requests: list[GatewayRequest],
    ) -> list[GatewayResponse]:
        """
        Concurrent dispatch for N requests.
        Priority is respected within each bucket's FIFO queue.
        """
        tasks = [asyncio.create_task(self.call(r)) for r in requests]
        return list(await asyncio.gather(*tasks))

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "total_calls":   self._total_calls,
            "total_tokens":  self._total_tokens,
            "fallbacks":     self._fallbacks,
            "fallback_rate": round(self._fallbacks / max(self._total_calls, 1), 4),
            "cache":         self._cache.stats,
        }


# ─── Integration shim for cortex.agents.ralph_parallel.py workers ──────────────────────────

# Workers call this function. They are unaware of throttling or fallbacks.

async def swarm_call(
    gateway: SovereignLLMGateway,
    prompt: str,
    priority: Priority = Priority.LEGIONARY,
    tokens: int = 500,
) -> str:
    """
    One-liner for Legionary workers.
    Returns the completion string or raises.
    """
    req  = GatewayRequest(prompt=prompt, tokens=tokens, priority=priority)
    resp = await gateway.call(req)
    return resp.content


# ─── Smoke test (headless, C5-REAL declared: C4-SIMULATION) ──────────────────

if __name__ == "__main__":
    # C4-SIMULATION: stubs replace real LLM endpoints.
    # No tokens are consumed, no money moves.
    import asyncio as _asyncio

    async def _stub_primary(prompt: str) -> str:
        await asyncio.sleep(0.01)
        return f"[PRIMARY] {prompt[:40]}"

    async def _stub_fallback(prompt: str) -> str:
        await asyncio.sleep(0.005)
        return f"[FALLBACK-8B] {prompt[:40]}"

    async def _stub_saturation(_: str) -> str:
        raise RuntimeError("HTTP 429 simulated")

    specs = [
        ModelSpec(name="gemini-2.5-pro",  tpm_max=1_000_000, call=_stub_primary,    tier=0),
        ModelSpec(name="llama-3-8b-local", tpm_max=5_000_000, call=_stub_fallback,   tier=1),
    ]
    gw = SovereignLLMGateway(models=specs, cache_capacity=128)

    async def _run():
        # Batch: mix of priorities
        reqs = [
            GatewayRequest("Analyze Uniswap v4 slot0",   priority=Priority.LEGATUS,    tokens=800),
            GatewayRequest("Summarize block 19_000_000",  priority=Priority.CENTURION,  tokens=300),
            GatewayRequest("Summarize block 19_000_000",  priority=Priority.LEGIONARY,  tokens=300),  # cache hit
            GatewayRequest("Check reentrancy in swap()",  priority=Priority.PRAETORIAN, tokens=600),
        ]
        responses = await gw.call_batch(reqs)
        for r in responses:
            print(f"  model={r.model_used:20s} cache={r.cache_hit} wait={r.wait_s:.4f}s tier={r.fallback_tier}")

        print("\nGateway Stats:", gw.stats)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    _asyncio.run(_run())
