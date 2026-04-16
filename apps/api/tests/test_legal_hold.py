"""Tests for legal hold service and DSR erasure guard.

Covers:
- Active agency-wide hold blocks erasure
- Active subject-specific hold blocks erasure
- Released (inactive) hold does not block erasure
- No hold allows erasure
- Mixed-scope holds evaluated correctly
- DSR endpoint returns 409 when hold is active
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from passlib.context import CryptContext

from app.models import Agency, Client, LegalHold, User
from app.services.legal_hold import is_on_hold

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

AUTH_HEADERS = {
    "X-User-Id": "1",
    "X-Agency-Id": "1",
    "X-User-Email": "admin@agency.test",
    "X-User-Role": "admin",
}


def _seed(db) -> dict:
    agency = Agency(name="Hold Agency", slug="hold-agency")
    db.add(agency)
    db.flush()

    client = Client(agency_id=agency.id, name="Hold Client")
    db.add(client)
    db.flush()

    user = User(
        agency_id=agency.id,
        email="held@example.com",
        hashed_password=pwd_context.hash("TestPass123"),
        full_name="Held User",
        role="agent",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return {"agency": agency, "client": client, "user": user}


class TestIsOnHold:
    def test_no_hold_returns_false(self, db):
        seeds = _seed(db)
        assert is_on_hold(db, seeds["agency"].id) is False

    def test_agency_wide_hold_blocks(self, db):
        seeds = _seed(db)
        hold = LegalHold(
            agency_id=seeds["agency"].id,
            reason="Litigation pending",
            active=True,
        )
        db.add(hold)
        db.commit()
        assert is_on_hold(db, seeds["agency"].id) is True

    def test_subject_specific_hold_blocks(self, db):
        seeds = _seed(db)
        hold = LegalHold(
            agency_id=seeds["agency"].id,
            subject_email="held@example.com",
            reason="Subject dispute",
            active=True,
        )
        db.add(hold)
        db.commit()
        assert is_on_hold(db, seeds["agency"].id, subject_email="held@example.com") is True

    def test_subject_hold_does_not_block_other_subjects(self, db):
        seeds = _seed(db)
        hold = LegalHold(
            agency_id=seeds["agency"].id,
            subject_email="held@example.com",
            reason="Subject dispute",
            active=True,
        )
        db.add(hold)
        db.commit()
        assert is_on_hold(db, seeds["agency"].id, subject_email="other@example.com") is False

    def test_client_specific_hold_blocks(self, db):
        seeds = _seed(db)
        hold = LegalHold(
            agency_id=seeds["agency"].id,
            client_id=seeds["client"].id,
            reason="Client audit",
            active=True,
        )
        db.add(hold)
        db.commit()
        assert is_on_hold(db, seeds["agency"].id, client_id=seeds["client"].id) is True

    def test_released_hold_does_not_block(self, db):
        seeds = _seed(db)
        hold = LegalHold(
            agency_id=seeds["agency"].id,
            reason="Resolved",
            active=False,
            released_at=datetime.now(timezone.utc),
        )
        db.add(hold)
        db.commit()
        assert is_on_hold(db, seeds["agency"].id) is False

    def test_mixed_scope_agency_wide_blocks_everything(self, db):
        seeds = _seed(db)
        hold = LegalHold(
            agency_id=seeds["agency"].id,
            reason="Broad freeze",
            active=True,
        )
        db.add(hold)
        db.commit()
        # Agency-wide hold blocks even subject-specific queries
        assert is_on_hold(db, seeds["agency"].id, subject_email="anyone@example.com") is True
        assert is_on_hold(db, seeds["agency"].id, client_id=seeds["client"].id) is True


class TestDsrErasureGuard:
    def test_erasure_blocked_by_active_hold(self, client, db):
        seeds = _seed(db)
        hold = LegalHold(
            agency_id=seeds["agency"].id,
            subject_email="held@example.com",
            reason="Litigation",
            active=True,
        )
        db.add(hold)
        db.commit()

        # Create DSR erasure request
        create_resp = client.post(
            "/api/v1/dsr",
            json={"subject_email": "held@example.com", "request_type": "erasure"},
            headers=AUTH_HEADERS,
        )
        dsr_id = create_resp.json()["id"]

        # Try to process — should be blocked
        resp = client.post(f"/api/v1/dsr/{dsr_id}/process", headers=AUTH_HEADERS)
        assert resp.status_code == 409
        assert "legal hold" in resp.json()["detail"].lower()

    def test_erasure_allowed_after_hold_released(self, client, db):
        seeds = _seed(db)
        hold = LegalHold(
            agency_id=seeds["agency"].id,
            subject_email="held@example.com",
            reason="Resolved",
            active=False,
            released_at=datetime.now(timezone.utc),
        )
        db.add(hold)
        db.commit()

        create_resp = client.post(
            "/api/v1/dsr",
            json={"subject_email": "held@example.com", "request_type": "erasure"},
            headers=AUTH_HEADERS,
        )
        dsr_id = create_resp.json()["id"]

        resp = client.post(f"/api/v1/dsr/{dsr_id}/process", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    def test_access_not_blocked_by_hold(self, client, db):
        seeds = _seed(db)
        hold = LegalHold(
            agency_id=seeds["agency"].id,
            subject_email="held@example.com",
            reason="Litigation",
            active=True,
        )
        db.add(hold)
        db.commit()

        create_resp = client.post(
            "/api/v1/dsr",
            json={"subject_email": "held@example.com", "request_type": "access"},
            headers=AUTH_HEADERS,
        )
        dsr_id = create_resp.json()["id"]

        # Access requests should NOT be blocked by legal holds
        resp = client.post(f"/api/v1/dsr/{dsr_id}/process", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"
