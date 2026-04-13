"""
Tier 5 Phase 1+2 tests — encryption, integrations service, JWT signing,
rate limiting.

These cover the security foundations of Tier 5 that every downstream
phase (Aiia, BankID, storage, Celery) depends on.
"""
from __future__ import annotations

import os
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text, inspect

from app.database import engine, SessionLocal
from app.main import app
from app.models import Agency, IntegrationConfig, User
from app.services import integrations as svc
from app.services.secrets import decrypt, encrypt, mask, reset_cache as reset_secrets
from app.services.jwt_signing import get_signing_key, reset_cache as reset_jwt
from app.services.rate_limit import reset as reset_rate_limit
from passlib.context import CryptContext
from jose import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─── Secrets encryption ────────────────────────────────────────────────


def test_encrypt_decrypt_round_trip():
    token = encrypt("sk-ant-secret-value")
    assert token != "sk-ant-secret-value"  # actually encrypted
    assert decrypt(token) == "sk-ant-secret-value"


def test_encrypt_produces_different_ciphertexts_for_same_plaintext():
    """Fernet uses a random IV, so the same plaintext encrypts differently."""
    a = encrypt("hello")
    b = encrypt("hello")
    assert a != b
    assert decrypt(a) == "hello"
    assert decrypt(b) == "hello"


def test_decrypt_tampered_token_raises():
    from app.services.secrets import SecretsError
    token = encrypt("important")
    # Flip a byte in the middle of the ciphertext
    tampered = token[:20] + "X" + token[21:]
    with pytest.raises(SecretsError):
        decrypt(tampered)


def test_mask_shows_first_four_then_bullets():
    assert mask("sk-ant-abcdef") == "sk-a•••••••••"


def test_mask_short_strings_fully_obscured():
    assert mask("abc") == "•••"
    assert mask("") == ""


def test_secrets_key_comes_from_env_when_set(monkeypatch):
    monkeypatch.setenv("INTEGRATION_SECRETS_KEY", "some-test-master-key-value")
    reset_secrets()
    token = encrypt("x")
    assert decrypt(token) == "x"
    reset_secrets()


# ─── Integration service ───────────────────────────────────────────────


def test_provider_catalogue_contains_all_expected_providers():
    keys = {p.key for p in svc.list_providers()}
    # Representative sample across every category
    expected = {
        "google_oauth", "microsoft_oauth",
        "aiia", "tink",
        "bankid_no", "bankid_se", "ftn_fi",
        "do_spaces", "resend", "openclaw_whatsapp", "claude",
        "altinn", "skatteverket", "omavero", "tulorekisteri",
        "mews", "opera_cloud", "apaleo",
    }
    missing = expected - keys
    assert not missing, f"Missing providers: {missing}"


def test_provider_fields_have_secret_flags():
    """Every password-type field must have is_secret=True."""
    for p in svc.list_providers():
        for f in p.fields:
            if f.type == "password":
                assert f.is_secret, (
                    f"{p.key}.{f.key} is a password field but is_secret=False"
                )


def test_provider_has_docs_url_when_external():
    """Every external integration should point to vendor docs."""
    for p in svc.list_providers():
        if p.key in ("google_oauth", "microsoft_oauth", "aiia", "claude"):
            assert p.docs_url, f"{p.key} missing docs_url"


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        svc.get_provider("nonexistent-provider")


@pytest.fixture
def sample_agency(db):
    agency = Agency(name="Tier 5 Test Agency", slug="tier5-agency")
    db.add(agency)
    db.commit()
    db.refresh(agency)
    return agency


def test_set_and_get_config_round_trip(db, sample_agency):
    svc.set_config(
        db,
        agency_id=sample_agency.id,
        provider="google_oauth",
        values={
            "client_id": "public-client-id.apps.googleusercontent.com",
            "client_secret": "GOCSPX-very-secret-token",
        },
    )
    values = svc.get_config(db, sample_agency.id, "google_oauth")
    assert values["client_id"] == "public-client-id.apps.googleusercontent.com"
    assert values["client_secret"] == "GOCSPX-very-secret-token"


def test_set_config_encrypts_at_rest(db, sample_agency):
    svc.set_config(
        db,
        agency_id=sample_agency.id,
        provider="google_oauth",
        values={"client_secret": "plaintext-never-lands-in-db"},
    )
    # Read the raw row and confirm it's NOT plaintext
    row = (
        db.query(IntegrationConfig)
        .filter(
            IntegrationConfig.agency_id == sample_agency.id,
            IntegrationConfig.provider == "google_oauth",
            IntegrationConfig.key == "client_secret",
        )
        .first()
    )
    assert row is not None
    assert "plaintext" not in row.value_encrypted
    assert "never" not in row.value_encrypted
    # Now decrypt and confirm it round-trips
    assert decrypt(row.value_encrypted) == "plaintext-never-lands-in-db"


def test_set_config_empty_string_leaves_value_unchanged(db, sample_agency):
    """UI should be able to PUT a partial form without re-entering secrets."""
    svc.set_config(
        db,
        agency_id=sample_agency.id,
        provider="google_oauth",
        values={
            "client_id": "initial-id",
            "client_secret": "initial-secret",
        },
    )
    svc.set_config(
        db,
        agency_id=sample_agency.id,
        provider="google_oauth",
        values={
            "client_id": "updated-id",
            "client_secret": "",  # empty = unchanged
        },
    )
    values = svc.get_config(db, sample_agency.id, "google_oauth")
    assert values["client_id"] == "updated-id"
    assert values["client_secret"] == "initial-secret"


def test_set_config_rejects_unknown_keys(db, sample_agency):
    with pytest.raises(ValueError) as exc:
        svc.set_config(
            db,
            agency_id=sample_agency.id,
            provider="google_oauth",
            values={"nonexistent_key": "whatever"},
        )
    assert "nonexistent_key" in str(exc.value)


def test_mask_for_display_hides_secret_fields(db, sample_agency):
    svc.set_config(
        db,
        agency_id=sample_agency.id,
        provider="google_oauth",
        values={
            "client_id": "public.apps.googleusercontent.com",
            "client_secret": "GOCSPX-secret-do-not-display",
        },
    )
    values = svc.get_config(db, sample_agency.id, "google_oauth")
    masked = svc.mask_for_display("google_oauth", values)
    assert masked["client_id"] == "public.apps.googleusercontent.com"  # public field shown
    assert "GOCSPX-secret" not in masked["client_secret"]  # secret field masked
    assert "•" in masked["client_secret"]


def test_delete_config_removes_all_rows(db, sample_agency):
    svc.set_config(
        db,
        agency_id=sample_agency.id,
        provider="google_oauth",
        values={"client_id": "a", "client_secret": "b"},
    )
    assert svc.get_config(db, sample_agency.id, "google_oauth")
    svc.delete_config(db, sample_agency.id, "google_oauth")
    assert not svc.get_config(db, sample_agency.id, "google_oauth")


def test_integration_configs_table_has_rls_policy():
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT polname FROM pg_policy WHERE polrelid = "
                "'public.integration_configs'::regclass"
            )
        ).fetchall()
    names = {r[0] for r in result}
    assert "tenant_isolation" in names


# ─── JWT signing ──────────────────────────────────────────────────────


def test_signing_key_always_32_bytes():
    key = get_signing_key()
    assert len(key) == 32


def test_signing_key_is_cached():
    reset_jwt()
    a = get_signing_key()
    b = get_signing_key()
    assert a == b


def test_signing_key_uses_env_when_set(monkeypatch):
    from app.config import get_settings
    # Clear the lru_cache on settings
    get_settings.cache_clear()
    monkeypatch.setenv("JWT_SIGNING_KEY", "my-custom-production-key-abc123")
    reset_jwt()
    key1 = get_signing_key()

    monkeypatch.setenv("JWT_SIGNING_KEY", "different-key-xyz")
    get_settings.cache_clear()
    reset_jwt()
    key2 = get_signing_key()

    assert key1 != key2
    # Reset for the next test
    get_settings.cache_clear()


def test_internal_token_round_trip_verifies():
    """Token signed by routers/auth.py must be verifiable by app/auth.py."""
    from app.routers.auth import create_access_token
    reset_jwt()  # clear any monkey-patched key from earlier tests

    user = User(
        id=42, email="verify@test", hashed_password="x",
        full_name="T", role="admin", is_active=True, agency_id=99,
    )
    token = create_access_token(user)

    # Decode using the same key
    key = get_signing_key()
    claims = jwt.decode(token, key, algorithms=["HS256"])
    assert claims["sub"] == "42"
    assert claims["agency_id"] == 99
    assert claims["role"] == "admin"


def test_login_issues_internal_token_that_dashboard_accepts(db, sample_agency):
    """End-to-end: login → receive JWT → authenticated endpoint accepts it.

    This was broken before Tier 5 because the signer used
    claude_api_key[:32] but the verifier expected Auth0 RS256 JWKS.
    """
    reset_rate_limit()
    reset_jwt()

    # Create a user to log in as
    user = User(
        email="logged-in@example.com",
        hashed_password=pwd_context.hash("password-abc-123"),
        full_name="Verified User",
        agency_id=sample_agency.id,
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()

    client = TestClient(app)
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "logged-in@example.com", "password": "password-abc-123"},
    )
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]

    # Use the token to hit an authenticated endpoint
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200, me_resp.text
    me = me_resp.json()
    assert me["agency_id"] == sample_agency.id
    assert me["role"] == "admin"


def test_invalid_token_rejected_with_401():
    client = TestClient(app)
    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer obviously-not-a-valid-token"},
    )
    assert resp.status_code == 401


# ─── Rate limiting ─────────────────────────────────────────────────────


def test_login_rate_limit_blocks_after_threshold(db, sample_agency):
    """Login endpoint should 429 after N attempts per minute."""
    reset_rate_limit()
    client = TestClient(app)
    payload = {"email": "rate-limit@example.com", "password": "wrong"}

    # Settings default is 10 per minute — burn through them
    for _ in range(10):
        resp = client.post("/api/v1/auth/login", json=payload)
        # Could be 401 (wrong creds) or 429 (limit) but NOT 500
        assert resp.status_code in (401, 429)

    # Next request should definitely be 429
    resp = client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 429
    assert "rate limit" in resp.json()["detail"].lower()
    assert resp.headers.get("Retry-After") == "60"


def test_rate_limit_scopes_are_independent(db, sample_agency):
    """Different rate-limit scopes shouldn't share a bucket."""
    from app.services.rate_limit import _consume, reset
    reset()
    # Burn through the "login" bucket
    for i in range(10):
        _consume("login", "127.0.0.1", limit=10, window_seconds=60)
    assert not _consume("login", "127.0.0.1", limit=10, window_seconds=60)
    # "other" bucket for the same client should be fresh
    assert _consume("other", "127.0.0.1", limit=10, window_seconds=60)


# ─── Integration router (live HTTP) ───────────────────────────────────


@pytest.fixture
def admin_token(db, sample_agency):
    """Create an admin user and return a valid bearer token."""
    reset_jwt()
    reset_rate_limit()
    user = User(
        email="admin@tier5.example",
        hashed_password=pwd_context.hash("test-password-abc123"),
        full_name="Admin Tester",
        agency_id=sample_agency.id,
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    client = TestClient(app)
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@tier5.example", "password": "test-password-abc123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def test_integrations_router_lists_providers(admin_token):
    client = TestClient(app)
    resp = client.get(
        "/api/v1/integrations/providers",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    providers = resp.json()
    assert len(providers) >= 10
    keys = {p["key"] for p in providers}
    assert "google_oauth" in keys
    assert "aiia" in keys


def test_integrations_router_requires_auth():
    client = TestClient(app)
    resp = client.get("/api/v1/integrations/providers")
    assert resp.status_code == 401


def test_integrations_router_put_and_get_round_trip(admin_token):
    client = TestClient(app)
    put_resp = client.put(
        "/api/v1/integrations/google_oauth",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "values": {
                "client_id": "e2e-public-id",
                "client_secret": "e2e-secret-should-be-masked",
            }
        },
    )
    assert put_resp.status_code == 200, put_resp.text
    body = put_resp.json()
    assert body["provider"] == "google_oauth"
    assert body["is_configured"] is True
    assert body["values"]["client_id"] == "e2e-public-id"
    assert "e2e-secret" not in body["values"]["client_secret"]

    get_resp = client.get(
        "/api/v1/integrations/google_oauth",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert get_resp.status_code == 200
    assert "e2e-secret" not in get_resp.json()["values"]["client_secret"]


def test_integrations_router_rejects_non_admin_writes(db, sample_agency):
    reset_jwt()
    reset_rate_limit()
    user = User(
        email="regular@tier5.example",
        hashed_password=pwd_context.hash("test-password-abc123"),
        full_name="Regular User",
        agency_id=sample_agency.id,
        role="agent",
        is_active=True,
    )
    db.add(user)
    db.commit()
    client = TestClient(app)
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "regular@tier5.example", "password": "test-password-abc123"},
    )
    token = login.json()["access_token"]

    resp = client.put(
        "/api/v1/integrations/google_oauth",
        headers={"Authorization": f"Bearer {token}"},
        json={"values": {"client_id": "should-be-blocked"}},
    )
    assert resp.status_code == 403
