"""Tests for refresh-token rotation with Redis revocation.

Uses a simple dict-based Redis mock so the test suite does not need a live
Redis instance.
"""

from __future__ import annotations

import time
from typing import Any

import pytest
from jose import jwt

from app.config import get_settings
from app.services.auth import refresh as refresh_mod
from app.services.auth.refresh import (
    issue_pair,
    rotate,
    revoke,
    revoke_family,
    is_revoked,
    set_redis_client,
    reset_settings,
)


# ---------------------------------------------------------------------------
# Minimal dict-based Redis mock
# ---------------------------------------------------------------------------


class _FakeRedis:
    """In-memory Redis stand-in that supports the subset used by refresh.py."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[str, float | None]] = {}

    # -- write -----------------------------------------------------------

    def setex(self, name: str, time_seconds: int, value: str) -> None:
        expires = _now() + time_seconds
        self._store[name] = (value, expires)

    def set(self, name: str, value: str, ex: int | None = None) -> None:
        expires = _now() + ex if ex else None
        self._store[name] = (value, expires)

    # -- read ------------------------------------------------------------

    def get(self, name: str) -> str | None:
        entry = self._store.get(name)
        if entry is None:
            return None
        value, expires = entry
        if expires is not None and _now() > expires:
            del self._store[name]
            return None
        return value

    def exists(self, name: str) -> int:
        return 1 if self.get(name) is not None else 0


def _now() -> float:
    return time.time()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _inject_fake_redis():
    """Replace the module-level Redis client with the fake before every test."""
    fake = _FakeRedis()
    set_redis_client(fake)
    reset_settings()
    yield
    # Reset so other test modules are not affected
    set_redis_client(None)  # type: ignore[arg-type]
    reset_settings()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _decode_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestIssuePair:
    def test_issue_pair_returns_both_tokens(self):
        pair = issue_pair(user_id=1, agency_id=10)

        assert "access_token" in pair
        assert "refresh_token" in pair
        assert pair["token_type"] == "bearer"

        access = _decode_token(pair["access_token"])
        refresh = _decode_token(pair["refresh_token"])

        assert access["type"] == "access"
        assert access["sub"] == "1"
        assert access["agency_id"] == 10
        assert "jti" in access

        assert refresh["type"] == "refresh"
        assert refresh["sub"] == "1"
        assert refresh["agency_id"] == 10
        assert "jti" in refresh
        assert "family" in refresh


class TestRotate:
    def test_rotate_returns_new_pair(self):
        original = issue_pair(user_id=2, agency_id=20)
        new_pair = rotate(original["refresh_token"])

        assert "access_token" in new_pair
        assert "refresh_token" in new_pair

        # New tokens should be different from the originals
        assert new_pair["access_token"] != original["access_token"]
        assert new_pair["refresh_token"] != original["refresh_token"]

        # Same family
        old_refresh = _decode_token(original["refresh_token"])
        new_refresh = _decode_token(new_pair["refresh_token"])
        assert new_refresh["family"] == old_refresh["family"]

    def test_rotate_revokes_old_token(self):
        original = issue_pair(user_id=3, agency_id=30)
        old_refresh = _decode_token(original["refresh_token"])

        rotate(original["refresh_token"])

        # The old jti should now be revoked
        assert is_revoked(old_refresh["jti"]) is True

    def test_reuse_detection_revokes_family(self):
        original = issue_pair(user_id=4, agency_id=40)
        old_refresh_payload = _decode_token(original["refresh_token"])

        # First rotation succeeds
        rotate(original["refresh_token"])

        # Replaying the *same* refresh token should fail and revoke family
        with pytest.raises(ValueError, match="reuse detected"):
            rotate(original["refresh_token"])

        # The family should be revoked
        assert is_revoked(
            old_refresh_payload["jti"],
            family=old_refresh_payload["family"],
        ) is True


class TestLogout:
    def test_logout_revokes_family(self):
        pair = issue_pair(user_id=5, agency_id=50)
        refresh_payload = _decode_token(pair["refresh_token"])
        family = refresh_payload["family"]

        revoke_family(family)

        # Any token in the family should now be considered revoked
        assert is_revoked(refresh_payload["jti"], family=family) is True

        # Attempting to rotate should fail
        with pytest.raises(ValueError):
            rotate(pair["refresh_token"])


class TestRevokeHelpers:
    def test_revoke_single_jti(self):
        assert is_revoked("some-jti") is False
        revoke("some-jti")
        assert is_revoked("some-jti") is True

    def test_revoke_family_flag(self):
        assert is_revoked("any-jti", family="fam-1") is False
        revoke_family("fam-1")
        assert is_revoked("any-jti", family="fam-1") is True
