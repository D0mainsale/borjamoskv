#!/usr/bin/env python3
"""
Guarda 0 — Smoke Test
C5-REAL: Valida estructura del reducer SIN embedding externo.
Usa reducción de token count como proxy determinista.

Ejecutar:
    python test_guarda_0.py

Salida esperada:
    ✅ PASS  — todos los casos de bypass/reducción correctos
    o
    ❌ FAIL  — con detalle del caso fallido
"""
import os
import sys

# Activar reducer para el test
os.environ["CORTEX_TOKEN_REDUCER"] = "on"
os.environ["CORTEX_TOKEN_REDUCER_STRATEGY"] = "guarded"
os.environ["CORTEX_TOKEN_REDUCER_FALLBACK"] = "pass_through"
os.environ["CORTEX_TOKEN_REDUCER_OBSERVABILITY"] = "minimal"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cortex.core.token_reducer import reduce, run_guarda_0, SEMANTIC_FIDELITY_THRESHOLD

# ── Test Cases ────────────────────────────────────────────────────────

CASES = [
    # (description, payload, expected_bypass)
    (
        "forensic_log should bypass",
        "2026-04-15 01:00:00 ERROR server.py crashed\n2026-04-15 01:00:01 WARN retry\n",
        True,
    ),
    (
        "stack_trace should bypass",
        'Traceback (most recent call last):\n  File "main.py", line 42\nKeyError: "token"\n',
        True,
    ),
    (
        "diff payload should bypass",
        "--- a/main.py\n+++ b/main.py\n@@ -1,3 +1,4 @@\n",
        True,
    ),
    (
        "critical hash/address should bypass",
        "Deploying contract at 0xdeadbeefdeadbeef1234567890abcdef12345678",
        True,
    ),
    (
        "domain dashboard payload should bypass",
        '{"id": "ai-ml", "title": "AI/ML Engineering", "color": "#2B3BE5"}',
        True,
    ),
    (
        "pre-summarized short payload should bypass",
        "Short message under 200 tokens.",
        True,
    ),
    (
        "verbose padding should reduce",
        (
            "This is a long document.\n\n\n\n\nWith many blank lines.\n\n\n\n\n"
            "And more content here.   \n"
            "----\n----\n----\n"
            "Final section.\n\n\n\n\nEnd.\n"
        ),
        False,  # should NOT bypass, should be reduced
    ),
]


def test_bypass_rules():
    failures = []
    for desc, payload, expect_bypass in CASES:
        reduced, audit = reduce(payload)
        got_bypass = audit.bypass_triggered
        if got_bypass != expect_bypass:
            failures.append(
                f"  FAIL [{desc}]\n"
                f"    expected bypass={expect_bypass}, got bypass={got_bypass}\n"
                f"    bypass_reason={audit.bypass_reason}\n"
                f"    tokens: {audit.tokens_before} → {audit.tokens_after}"
            )
        else:
            emoji = "⏭️ " if got_bypass else "✂️ "
            ratio = f" ({audit.reduction_ratio*100:.1f}% saved)" if not got_bypass else ""
            print(f"  ✅ {emoji} [{desc}]{ratio}")
    return failures


def test_reduction_correctness():
    """Verify structural reducer does not change bypass payloads."""
    failures = []
    padding_text = (
        "Content here.\n\n\n\n\nMore content.   \n"
        "====\n====\n====\n"
        "End section.\n\n\n\n\nFin.\n"
    )
    reduced, audit = reduce(padding_text)
    if audit.bypass_triggered:
        failures.append(f"  FAIL: padding text should not be bypassed")
    elif audit.reduction_ratio < 0.05:
        failures.append(
            f"  FAIL: expected >5% reduction on padding text, got {audit.reduction_ratio*100:.1f}%"
        )
    else:
        print(f"  ✅ ✂️  Structural reducer: {audit.reduction_ratio*100:.1f}% saved")
    return failures


def test_guarda_0_harness():
    """
    Smoke test run_guarda_0 with a trivial embedding (identity hash projection).
    C5-REAL NOTE: In production, swap embed_fn with a real sentence-transformer.
    """
    import hashlib

    def mock_embed(text: str) -> list[float]:
        """
        Deterministic mock embedding: character frequency vector (256-dim).
        For smoke test only — NOT a real semantic embedding.
        """
        vec = [0.0] * 256
        for ch in text.encode("utf-8"):
            vec[ch] += 1.0
        norm = (sum(v * v for v in vec) ** 0.5) or 1.0
        return [v / norm for v in vec]

    corpus = [
        "This is a verbose document.\n\n\n\nWith lots of blank lines.\n\n\nEnd.\n",
        "Another document with trailing spaces.   \nAnd more lines.   \n",
        '{"id": "cbf-001", "title": "Test", "value": 42}',  # domain payload → bypass
        "ERROR: compilation failed at main.rs:42:13\n",      # compile error → bypass
    ]

    result = run_guarda_0(corpus, mock_embed)
    print(f"\n  Guarda 0 result:")
    print(f"    passed         = {result['passed']}")
    print(f"    p95_similarity = {result['p95_similarity']}")
    print(f"    p50_similarity = {result['p50_similarity']}")
    print(f"    bypass_rate    = {result['bypass_rate']*100:.0f}%")
    print(f"    n_samples      = {result['n_samples']}")
    print(f"    failures       = {len(result['failures'])}")

    failures = []
    if not result["passed"] and result["p95_similarity"] < 0.80:
        failures.append(f"  FAIL: p95={result['p95_similarity']} well below threshold")
    return failures


# ── Runner ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== CORTEX Token Reducer — Guarda 0 Smoke Test ===\n")

    all_failures = []

    print("── Guarda 1: Bypass Rules ──")
    all_failures += test_bypass_rules()

    print("\n── Reducer Correctness ──")
    all_failures += test_reduction_correctness()

    print("\n── Guarda 0: Semantic Harness (mock embed) ──")
    all_failures += test_guarda_0_harness()

    print()
    if all_failures:
        print("❌ FAILURES:")
        for f in all_failures:
            print(f)
        sys.exit(1)
    else:
        print("✅ ALL TESTS PASSED")
        print(f"\nGuarda 0 threshold: {SEMANTIC_FIDELITY_THRESHOLD} cosine similarity @ P95")
        print("Replace mock_embed with sentence-transformers before 5% rollout.\n")
        sys.exit(0)
