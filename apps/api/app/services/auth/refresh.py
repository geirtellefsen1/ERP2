"""Refresh-token rotation with Redis revocation.

Access tokens are short-lived (15 min).  Refresh tokens last 14 days and
belong to a *family* — when a refresh token is rotated the old jti is
revoked.  If a revoked jti is presented again (replay / theft) the entire
family is revoked immediately.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import redis
from jose import jwt, JWTError

from app.config import get_settings

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_settings = None

def _get_settings():
    global _settings
    if _settings is None:
        _settings = get_settings()
    return _settings


ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 14

# Redis key prefixes / sets
_REVOKED_TOKENS_PREFIX = "revoked_token:"
_REVOKED_FAMILIES_PREFIX = "revoked_family:"

# ---------------------------------------------------------------------------
# Redis connection (lazy singleton)
# ---------------------------------------------------------------------------

_redis_client: redis.Redis | None = None


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        settings = _get_settings()
        _redis_client = redis.Redis.from_url(
            settings.redis_url, decode_responses=True
        )
    return _redis_client


def set_redis_client(client: redis.Redis) -> None:
    """Allow injection of a Redis client (e.g. fakeredis in tests)."""
    global _redis_client
    _redis_client = client


def reset_settings() -> None:
    """Reset the cached settings (useful for tests)."""
    global _settings
    _settings = None


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


def _encode(payload: dict) -> str:
    settings = _get_settings()
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode(token: str) -> dict:
    settings = _get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def issue_pair(user_id: int, agency_id: int, family: str | None = None) -> dict:
    """Issue an access + refresh token pair.

    Parameters
    ----------
    user_id : int
    agency_id : int
    family : str | None
        If supplied the refresh token inherits this family (rotation).
        Otherwise a new family is created.

    Returns
    -------
    dict with keys ``access_token``, ``refresh_token``, ``token_type``.
    """
    now = datetime.now(timezone.utc)
    family = family or str(uuid.uuid4())

    access_jti = str(uuid.uuid4())
    access_payload = {
        "sub": str(user_id),
        "agency_id": agency_id,
        "type": "access",
        "jti": access_jti,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": now,
    }

    refresh_jti = str(uuid.uuid4())
    refresh_payload = {
        "sub": str(user_id),
        "agency_id": agency_id,
        "type": "refresh",
        "jti": refresh_jti,
        "family": family,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": now,
    }

    return {
        "access_token": _encode(access_payload),
        "refresh_token": _encode(refresh_payload),
        "token_type": "bearer",
    }


def rotate(refresh_token: str) -> dict:
    """Validate *refresh_token*, revoke its jti, and return a new pair.

    If the jti has **already** been revoked (replay detection) the entire
    family is revoked and ``None`` is returned.

    Raises
    ------
    ValueError
        If the token is invalid, expired, not a refresh token, or revoked.
    """
    try:
        payload = _decode(refresh_token)
    except JWTError as exc:
        raise ValueError(f"Invalid refresh token: {exc}") from exc

    if payload.get("type") != "refresh":
        raise ValueError("Token is not a refresh token")

    jti = payload["jti"]
    family = payload["family"]

    # Reuse detection: if the jti is already revoked, the token was stolen
    if is_revoked(jti, family):
        revoke_family(family)
        raise ValueError("Refresh token reuse detected — family revoked")

    # Revoke the consumed jti
    revoke(jti)

    # Issue new pair in the same family
    return issue_pair(
        user_id=int(payload["sub"]),
        agency_id=payload["agency_id"],
        family=family,
    )


def revoke(jti: str) -> None:
    """Mark a single jti as revoked (TTL = 14 days)."""
    r = _get_redis()
    key = f"{_REVOKED_TOKENS_PREFIX}{jti}"
    ttl_seconds = REFRESH_TOKEN_EXPIRE_DAYS * 86_400
    r.setex(key, ttl_seconds, "1")


def revoke_family(family: str) -> None:
    """Mark an entire token family as revoked (TTL = 14 days)."""
    r = _get_redis()
    key = f"{_REVOKED_FAMILIES_PREFIX}{family}"
    ttl_seconds = REFRESH_TOKEN_EXPIRE_DAYS * 86_400
    r.setex(key, ttl_seconds, "1")


def is_revoked(jti: str, family: str | None = None) -> bool:
    """Return ``True`` if *jti* or its *family* has been revoked."""
    r = _get_redis()
    if r.exists(f"{_REVOKED_TOKENS_PREFIX}{jti}"):
        return True
    if family and r.exists(f"{_REVOKED_FAMILIES_PREFIX}{family}"):
        return True
    return False
