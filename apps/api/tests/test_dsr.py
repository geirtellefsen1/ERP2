"""Tests for GDPR Data Subject Rights (DSR) endpoints.

Covers:
- Creating DSR requests (access, erasure, portability, rectification)
- Listing DSR requests with status filter
- Getting a single DSR request
- Processing access/portability (export)
- Processing erasure (pseudonymisation)
- Processing rectification (manual → in_progress)
- Cannot process an already-completed request
- 404 for non-existent DSR
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from passlib.context import CryptContext

from app.models import Agency, Client, ClientContact, DsrRequest, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Auth headers — matches the header-based auth stub in app/auth.py
AUTH_HEADERS = {
    "X-User-Id": "1",
    "X-Agency-Id": "1",
    "X-User-Email": "admin@agency.test",
    "X-User-Role": "admin",
}


def _seed(db) -> dict:
    """Create agency, user, client, contact for DSR tests."""
    agency = Agency(name="DSR Agency", slug="dsr-agency")
    db.add(agency)
    db.flush()

    user = User(
        agency_id=agency.id,
        email="subject@example.com",
        hashed_password=pwd_context.hash("TestPass123"),
        full_name="Data Subject",
        role="agent",
        is_active=True,
    )
    db.add(user)
    db.flush()

    client = Client(agency_id=agency.id, name="Client Co")
    db.add(client)
    db.flush()

    contact = ClientContact(
        client_id=client.id,
        name="Data Subject",
        email="subject@example.com",
        phone="+1234567890",
        role="Manager",
    )
    db.add(contact)
    db.commit()

    return {"agency": agency, "user": user, "client": client, "contact": contact}


class TestCreateDsr:
    def test_create_access_request(self, client, db):
        _seed(db)
        resp = client.post(
            "/api/v1/dsr",
            json={
                "subject_email": "subject@example.com",
                "subject_name": "Data Subject",
                "request_type": "access",
            },
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["request_type"] == "access"
        assert data["status"] == "pending"
        assert data["subject_email"] == "subject@example.com"
        assert data["deadline_at"] is not None

    def test_create_erasure_request(self, client, db):
        _seed(db)
        resp = client.post(
            "/api/v1/dsr",
            json={
                "subject_email": "subject@example.com",
                "request_type": "erasure",
                "notes": "User requested full deletion",
            },
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201
        assert resp.json()["request_type"] == "erasure"
        assert resp.json()["notes"] == "User requested full deletion"

    def test_create_invalid_type_rejected(self, client, db):
        _seed(db)
        resp = client.post(
            "/api/v1/dsr",
            json={
                "subject_email": "subject@example.com",
                "request_type": "invalid_type",
            },
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 422


class TestListDsr:
    def test_list_returns_agency_requests(self, client, db):
        _seed(db)
        # Create two requests
        client.post(
            "/api/v1/dsr",
            json={"subject_email": "a@example.com", "request_type": "access"},
            headers=AUTH_HEADERS,
        )
        client.post(
            "/api/v1/dsr",
            json={"subject_email": "b@example.com", "request_type": "erasure"},
            headers=AUTH_HEADERS,
        )
        resp = client.get("/api/v1/dsr", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_filter_by_status(self, client, db):
        _seed(db)
        client.post(
            "/api/v1/dsr",
            json={"subject_email": "a@example.com", "request_type": "access"},
            headers=AUTH_HEADERS,
        )
        resp = client.get("/api/v1/dsr?status=completed", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert len(resp.json()) == 0


class TestGetDsr:
    def test_get_existing(self, client, db):
        _seed(db)
        create_resp = client.post(
            "/api/v1/dsr",
            json={"subject_email": "subject@example.com", "request_type": "access"},
            headers=AUTH_HEADERS,
        )
        dsr_id = create_resp.json()["id"]
        resp = client.get(f"/api/v1/dsr/{dsr_id}", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["id"] == dsr_id

    def test_get_nonexistent_returns_404(self, client, db):
        resp = client.get("/api/v1/dsr/9999", headers=AUTH_HEADERS)
        assert resp.status_code == 404


class TestProcessDsr:
    def test_process_access_creates_export(self, client, db):
        seeds = _seed(db)
        create_resp = client.post(
            "/api/v1/dsr",
            json={"subject_email": "subject@example.com", "request_type": "access"},
            headers=AUTH_HEADERS,
        )
        dsr_id = create_resp.json()["id"]

        resp = client.post(f"/api/v1/dsr/{dsr_id}/process", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None
        assert len(data["artifacts"]) == 1
        assert data["artifacts"][0]["artifact_type"] == "export_json"

    def test_process_erasure_pseudonymises_data(self, client, db):
        seeds = _seed(db)
        create_resp = client.post(
            "/api/v1/dsr",
            json={"subject_email": "subject@example.com", "request_type": "erasure"},
            headers=AUTH_HEADERS,
        )
        dsr_id = create_resp.json()["id"]

        resp = client.post(f"/api/v1/dsr/{dsr_id}/process", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert len(data["artifacts"]) == 1
        assert data["artifacts"][0]["artifact_type"] == "erasure_confirmation"

        # Verify user was deactivated
        db.expire_all()
        user = db.query(User).filter(User.id == seeds["user"].id).first()
        assert user.is_active is False
        assert "erased" in user.email

        # Verify contact was deleted
        contact = db.query(ClientContact).filter(ClientContact.id == seeds["contact"].id).first()
        assert contact is None

    def test_process_rectification_sets_in_progress(self, client, db):
        _seed(db)
        create_resp = client.post(
            "/api/v1/dsr",
            json={"subject_email": "subject@example.com", "request_type": "rectification"},
            headers=AUTH_HEADERS,
        )
        dsr_id = create_resp.json()["id"]

        resp = client.post(f"/api/v1/dsr/{dsr_id}/process", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"

    def test_process_already_completed_fails(self, client, db):
        _seed(db)
        create_resp = client.post(
            "/api/v1/dsr",
            json={"subject_email": "subject@example.com", "request_type": "access"},
            headers=AUTH_HEADERS,
        )
        dsr_id = create_resp.json()["id"]

        # Process once
        client.post(f"/api/v1/dsr/{dsr_id}/process", headers=AUTH_HEADERS)
        # Try again
        resp = client.post(f"/api/v1/dsr/{dsr_id}/process", headers=AUTH_HEADERS)
        assert resp.status_code == 400
        assert "already completed" in resp.json()["detail"].lower()

    def test_process_nonexistent_returns_404(self, client, db):
        resp = client.post("/api/v1/dsr/9999/process", headers=AUTH_HEADERS)
        assert resp.status_code == 404
