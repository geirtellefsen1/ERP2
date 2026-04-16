"""Tests for TOTP-based Multi-Factor Authentication.

Covers:
- /setup returns secret + provisioning URI
- /enable with valid TOTP code activates MFA
- /verify with correct code succeeds
- /verify with incorrect code fails
- /disable deactivates MFA
"""

from __future__ import annotations

import pyotp
import pytest

from app.models import Agency, User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

AUTH_HEADERS = {
    "X-User-Id": "1",
    "X-Agency-Id": "1",
    "X-User-Email": "mfa@example.com",
    "X-User-Role": "admin",
}


def _seed_user(db, email: str = "mfa@example.com") -> User:
    """Create a test agency + user and return the user."""
    agency = Agency(name="MFA Agency", slug="mfa-agency")
    db.add(agency)
    db.flush()
    user = User(
        agency_id=agency.id,
        email=email,
        hashed_password="not-used",
        full_name="MFA Tester",
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestMFASetup:
    def test_setup_returns_secret_and_uri(self, client, db):
        user = _seed_user(db)
        headers = {**AUTH_HEADERS, "X-User-Id": str(user.id), "X-Agency-Id": str(user.agency_id)}
        resp = client.post("/api/v1/mfa/setup", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "secret" in data
        assert "provisioning_uri" in data
        assert "qr_data" in data
        assert data["provisioning_uri"].startswith("otpauth://totp/")
        assert "BPO%20Nexus" in data["provisioning_uri"] or "BPO+Nexus" in data["provisioning_uri"]


class TestMFAEnable:
    def test_enable_with_valid_code(self, client, db):
        user = _seed_user(db)
        headers = {**AUTH_HEADERS, "X-User-Id": str(user.id), "X-Agency-Id": str(user.agency_id)}

        # Call setup to get a secret
        setup_resp = client.post("/api/v1/mfa/setup", headers=headers)
        secret = setup_resp.json()["secret"]

        # Store the secret on the user (simulates the flow)
        user.mfa_secret = secret
        db.commit()

        # Generate a valid TOTP code
        code = pyotp.TOTP(secret).now()

        resp = client.post(
            "/api/v1/mfa/enable",
            headers=headers,
            json={"code": code},
        )
        assert resp.status_code == 200
        assert "enabled" in resp.json()["detail"].lower()

        # Verify mfa_enabled is True in the DB
        db.refresh(user)
        assert user.mfa_enabled is True


class TestMFAVerify:
    def test_verify_with_correct_code(self, client, db):
        user = _seed_user(db)
        secret = pyotp.random_base32()
        user.mfa_secret = secret
        user.mfa_enabled = True
        db.commit()

        code = pyotp.TOTP(secret).now()
        resp = client.post(
            "/api/v1/mfa/verify",
            json={"user_id": user.id, "code": code},
        )
        assert resp.status_code == 200
        assert "successful" in resp.json()["detail"].lower()

    def test_verify_with_incorrect_code_fails(self, client, db):
        user = _seed_user(db)
        secret = pyotp.random_base32()
        user.mfa_secret = secret
        user.mfa_enabled = True
        db.commit()

        resp = client.post(
            "/api/v1/mfa/verify",
            json={"user_id": user.id, "code": "000000"},
        )
        assert resp.status_code == 400
        assert "invalid" in resp.json()["detail"].lower()


class TestMFADisable:
    def test_disable_mfa(self, client, db):
        user = _seed_user(db)
        secret = pyotp.random_base32()
        user.mfa_secret = secret
        user.mfa_enabled = True
        db.commit()

        headers = {**AUTH_HEADERS, "X-User-Id": str(user.id), "X-Agency-Id": str(user.agency_id)}
        code = pyotp.TOTP(secret).now()

        resp = client.post(
            "/api/v1/mfa/disable",
            headers=headers,
            json={"code": code},
        )
        assert resp.status_code == 200
        assert "disabled" in resp.json()["detail"].lower()

        # Verify MFA is off in the DB
        db.refresh(user)
        assert user.mfa_enabled is False
        assert user.mfa_secret is None
