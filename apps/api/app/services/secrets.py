"""
Secrets management for integration credentials.

Why this module exists:
  - Integration credentials (Google OAuth client secret, BankID certs,
    Aiia API keys, Altinn tokens, etc.) need to live SOMEWHERE that's
    not git and not environment variables that every dev sees.
  - Per-agency configs need per-agency storage — each BPO agency's
    Google Cloud project is theirs, not shared. Env vars are a single
    global value; the database lets us scope per agency.
  - Plaintext secrets in a DB column are one SELECT query away from
    being leaked. Encrypting at rest gives defense in depth against
    backups, logs, replicas, and developer access.

Design:
  - Fernet symmetric encryption via the `cryptography` library
    (AES-128-CBC + HMAC-SHA256, authenticated encryption)
  - The master key comes from INTEGRATION_SECRETS_KEY env var, loaded
    once at startup and held in a process-local cache
  - Values are encoded as base64url tokens for safe DB storage
  - encrypt()/decrypt() are the only public API — all router code goes
    through them, never touches Fernet directly
  - When the master key is missing in dev, we auto-generate a stable
    per-process key so the module can be imported without crashing.
    Loud warning in logs so nobody ships that to prod.

Key rotation:
  - Fernet supports multi-key rotation via MultiFernet. Future work:
    allow INTEGRATION_SECRETS_KEYS (plural) as comma-separated list,
    decrypt with any key, encrypt with the first.
"""
from __future__ import annotations

import base64
import hashlib
import logging
import os
import threading
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class SecretsError(Exception):
    """Raised when encryption/decryption fails."""


_lock = threading.Lock()
_fernet: Optional[Fernet] = None
_warned_dev_key = False


def _derive_key_from_password(password: str) -> bytes:
    """
    Turn an arbitrary-length string into a valid Fernet key
    (32 url-safe base64-encoded bytes).
    """
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _get_fernet() -> Fernet:
    global _fernet, _warned_dev_key
    with _lock:
        if _fernet is not None:
            return _fernet

        key = os.environ.get("INTEGRATION_SECRETS_KEY")
        if key:
            try:
                # Allow either a raw Fernet key or a password to derive from
                if len(key) == 44 and key.endswith("="):
                    _fernet = Fernet(key.encode("utf-8"))
                else:
                    _fernet = Fernet(_derive_key_from_password(key))
            except Exception as e:
                raise SecretsError(
                    f"Invalid INTEGRATION_SECRETS_KEY: {e}"
                ) from e
            return _fernet

        # Dev fallback — derive from a stable placeholder so imports work
        # in tests without needing the real key. WARN loudly so this never
        # silently lands in production.
        if not _warned_dev_key:
            logger.warning(
                "INTEGRATION_SECRETS_KEY is not set — using an insecure "
                "dev fallback key. Set INTEGRATION_SECRETS_KEY in "
                "/etc/claud-erp/.env before going to production."
            )
            _warned_dev_key = True
        _fernet = Fernet(
            _derive_key_from_password("claud-erp-dev-fallback-key-do-not-ship")
        )
        return _fernet


def encrypt(plaintext: str) -> str:
    """
    Encrypt a plaintext string. Returns a url-safe base64 ciphertext
    token that's safe to store in a TEXT column.
    """
    if plaintext is None:
        raise SecretsError("Cannot encrypt None")
    if not isinstance(plaintext, str):
        raise SecretsError(
            f"Expected string, got {type(plaintext).__name__}"
        )
    f = _get_fernet()
    token = f.encrypt(plaintext.encode("utf-8"))
    return token.decode("ascii")


def decrypt(token: str) -> str:
    """Decrypt a Fernet token back to its plaintext. Raises on tamper."""
    if not token:
        raise SecretsError("Cannot decrypt empty token")
    f = _get_fernet()
    try:
        data = f.decrypt(token.encode("ascii"))
    except InvalidToken as e:
        raise SecretsError("Invalid or tampered secret token") from e
    return data.decode("utf-8")


def mask(plaintext: str, show: int = 4) -> str:
    """
    Return a masked version of a secret, safe to log or return over the
    API. Shows the first `show` characters and hides the rest.

        mask("sk-ant-abcdefghijklmn") → "sk-a•••••••••••"
    """
    if not plaintext:
        return ""
    if len(plaintext) <= show:
        return "•" * len(plaintext)
    return plaintext[:show] + "•" * (len(plaintext) - show)


def reset_cache() -> None:
    """Test helper — clear the cached Fernet so reads re-derive the key."""
    global _fernet, _warned_dev_key
    with _lock:
        _fernet = None
        _warned_dev_key = False
