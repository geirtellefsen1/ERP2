"""Tests for password reset flow.

Covers:
- request-reset returns 202 for both existing and non-existing emails
- valid token resets password
- expired token is rejected
- used token is rejected (single-use)
- invalid/unknown token is rejected
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from passlib.context import CryptContext

from app.models import Agency, User, PasswordResetToken

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_user(db, email: str = "reset@example.com", password: str = "OldPass123") -> User:
    """Create a test agency + user and return the user."""
    agency = Agency(name="Test Agency", slug="test-agency-reset")
    db.add(agency)
    db.flush()
    user = User(
        agency_id=agency.id,
        email=email,
        hashed_password=pwd_context.hash(password),
        full_name="Reset Tester",
        role="agent",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRequestReset:
    def test_request_reset_returns_202_for_existing_user(self, client, db):
        _seed_user(db)
        resp = client.post(
            "/api/v1/auth/password/request-reset",
            json={"email": "reset@example.com"},
        )
        assert resp.status_code == 202
        assert "reset link" in resp.json()["detail"].lower()

        # A token should have been created in the DB
        token = db.query(PasswordResetToken).first()
        assert token is not None
        assert token.jti is not None
        assert token.used_at is None

    def test_request_reset_returns_202_for_nonexistent_user(self, client):
        resp = client.post(
            "/api/v1/auth/password/request-reset",
            json={"email": "nobody@example.com"},
        )
        assert resp.status_code == 202
        assert "reset link" in resp.json()["detail"].lower()


class TestResetPassword:
    def test_reset_with_valid_token_changes_password(self, client, db):
        user = _seed_user(db)
        old_hash = user.hashed_password

        # Request reset to generate a token
        client.post(
            "/api/v1/auth/password/request-reset",
            json={"email": user.email},
        )
        token = db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
        ).first()
        assert token is not None

        # Use the token to reset password
        resp = client.post(
            "/api/v1/auth/password/reset",
            json={"token": token.jti, "new_password": "NewSecurePass456"},
        )
        assert resp.status_code == 200
        assert "reset successfully" in resp.json()["detail"].lower()

        # Verify password actually changed
        db.refresh(user)
        assert user.hashed_password != old_hash
        assert pwd_context.verify("NewSecurePass456", user.hashed_password)

        # Verify token is now marked as used
        db.refresh(token)
        assert token.used_at is not None

    def test_reset_with_expired_token_fails(self, client, db):
        user = _seed_user(db)

        # Manually create an expired token
        token = PasswordResetToken(
            jti="expired-token-jti",
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.add(token)
        db.commit()

        resp = client.post(
            "/api/v1/auth/password/reset",
            json={"token": "expired-token-jti", "new_password": "NewSecurePass456"},
        )
        assert resp.status_code == 400
        assert "expired" in resp.json()["detail"].lower()

    def test_reset_with_used_token_fails(self, client, db):
        user = _seed_user(db)

        # Create a token that was already used
        token = PasswordResetToken(
            jti="used-token-jti",
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            used_at=datetime.now(timezone.utc),
        )
        db.add(token)
        db.commit()

        resp = client.post(
            "/api/v1/auth/password/reset",
            json={"token": "used-token-jti", "new_password": "NewSecurePass456"},
        )
        assert resp.status_code == 400
        assert "already been used" in resp.json()["detail"].lower()

    def test_reset_with_invalid_token_fails(self, client):
        resp = client.post(
            "/api/v1/auth/password/reset",
            json={"token": "nonexistent-token", "new_password": "NewSecurePass456"},
        )
        assert resp.status_code == 400
        assert "invalid" in resp.json()["detail"].lower()
