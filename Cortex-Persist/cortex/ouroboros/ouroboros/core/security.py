"""DoS prevention limits and input validation — Ω6 enforcement."""

from __future__ import annotations

import re

from .errors import SecurityLimitError

# ── Constants ─────────────────────────────────────────────────

MAX_INITIAL_CONTEXT_LENGTH: int = 50_000  # chars
MAX_USER_RESPONSE_LENGTH: int = 10_000  # chars
MAX_SEED_FILE_SIZE: int = 1_000_000  # bytes
MAX_LLM_RESPONSE_LENGTH: int = 100_000  # chars

# Control character pattern (keep newlines and tabs)
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


# ── Validators ────────────────────────────────────────────────


def validate_initial_context(text: str) -> str:
    """Validate and sanitize initial context input."""
    sanitized = _sanitize(text)
    if len(sanitized) > MAX_INITIAL_CONTEXT_LENGTH:
        raise SecurityLimitError(
            "initial_context", len(sanitized), MAX_INITIAL_CONTEXT_LENGTH
        )
    return sanitized


def validate_user_response(text: str) -> str:
    """Validate and sanitize user response."""
    sanitized = _sanitize(text)
    if len(sanitized) > MAX_USER_RESPONSE_LENGTH:
        raise SecurityLimitError(
            "user_response", len(sanitized), MAX_USER_RESPONSE_LENGTH
        )
    return sanitized


def validate_seed_file(data: bytes) -> bytes:
    """Validate seed file size."""
    if len(data) > MAX_SEED_FILE_SIZE:
        raise SecurityLimitError("seed_file", len(data), MAX_SEED_FILE_SIZE)
    return data


def validate_llm_response(text: str) -> str:
    """Validate LLM response length."""
    if len(text) > MAX_LLM_RESPONSE_LENGTH:
        raise SecurityLimitError(
            "llm_response", len(text), MAX_LLM_RESPONSE_LENGTH
        )
    return text


def _sanitize(text: str) -> str:
    """Strip control characters, enforce UTF-8."""
    # Ensure valid UTF-8 by round-tripping
    clean = text.encode("utf-8", errors="replace").decode("utf-8")
    # Strip control chars (preserve \n, \t, \r)
    return _CONTROL_CHARS.sub("", clean)
