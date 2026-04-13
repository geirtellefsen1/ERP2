"""
JWT signing key resolution.

Why this module exists:
  - The original codebase signed JWTs with `claude_api_key[:32]` which
    is a real security bug: it tied token validity to an unrelated
    provider credential, made rotation impossible without re-issuing
    every user's token, and meant anyone who could read the Claude
    key could also forge auth tokens.
  - This module centralises the resolution logic so routers/auth.py
    and app/auth.py both use the same derivation rules.

Resolution order:
  1. JWT_SIGNING_KEY env var (preferred, set explicitly in production)
  2. A stable placeholder for dev/test, with a loud warning
  3. Never falls through to another provider's key

The key is always at least 32 bytes (HS256 requires ≥ 32). Short input
is hashed via SHA-256 and used as the signing key.
"""
from __future__ import annotations

import hashlib
import logging
import threading

from app.config import get_settings

logger = logging.getLogger(__name__)


_DEV_PLACEHOLDER = (
    "claud-erp-dev-jwt-signing-key-do-not-use-in-production"
)

_lock = threading.Lock()
_cached_key: bytes | None = None
_warned_dev = False


def get_signing_key() -> bytes:
    """
    Return the signing key as raw bytes, suitable for `jwt.encode`.

    Uses the `jwt_signing_key` setting if set. Otherwise derives a
    stable key from a hardcoded placeholder and logs a one-time
    warning so dev/test works without further setup.
    """
    global _cached_key, _warned_dev
    with _lock:
        if _cached_key is not None:
            return _cached_key

        settings = get_settings()
        source = settings.jwt_signing_key or ""
        if not source:
            if not _warned_dev:
                logger.warning(
                    "JWT_SIGNING_KEY is not set — using the insecure dev "
                    "fallback. Set JWT_SIGNING_KEY in /etc/claud-erp/.env "
                    "to a 32+ byte random string before going to production: "
                    "openssl rand -hex 32"
                )
                _warned_dev = True
            source = _DEV_PLACEHOLDER

        # Expand short keys via SHA-256 to always have 32 bytes
        key = hashlib.sha256(source.encode("utf-8")).digest()
        _cached_key = key
        return key


def reset_cache() -> None:
    """Test helper — clear the cached key so changes to settings take effect."""
    global _cached_key, _warned_dev
    with _lock:
        _cached_key = None
        _warned_dev = False
