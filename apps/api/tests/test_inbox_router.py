"""Inbox router smoke tests."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.models import Account, Agency, Client, InboxItem, User


@pytest.fixture
def setup():
    db = SessionLocal()
    try:
        agency = Agency(name="Demo", slug="demo")
        db.add(agency)
        db.commit()
        db.refresh(agency)

        admin = User(
            email="admin@demo.local",
            hashed_password="x",
            full_name="Admin",
            agency_id=agency.id,
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        client = Client(
            agency_id=agency.id, name="Fjordvik", country="NO",
            industry="Hospitality", is_active=True,
        )
        db.add(client)
        db.commit()
        db.refresh(client)

        # Account 4000 needed for the auto-coding suggestion
        acc = Account(
            client_id=client.id, code="4000", name="Food cost",
            account_type="expense", sub_type="cogs", is_active=True,
        )
        db.add(acc)
        db.commit()

        yield agency.id, client.id, admin.id
    finally:
        db.close()


def _headers(agency_id, user_id):
    return {
        "x-user-id": str(user_id),
        "x-agency-id": str(agency_id),
        "x-user-email": "admin@demo.local",
        "x-user-role": "admin",
    }


def test_upload_extracts_known_supplier(client: TestClient, setup):
    agency_id, client_id, user_id = setup
    res = client.post(
        "/api/v1/inbox/upload",
        json={
            "client_id": client_id,
            "filename": "tine_2026-04-12_3850nok_inv-2389.pdf",
        },
        headers=_headers(agency_id, user_id),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["extracted_vendor"] == "Tine SA"
    assert body["extracted_amount_minor"] == 385_000
    assert body["suggested_account_code"] == "4000"
    assert body["status"] == "extracted"
    assert body["ai_confidence"] >= 0.9


def test_upload_unknown_supplier_pending(client: TestClient, setup):
    agency_id, client_id, user_id = setup
    res = client.post(
        "/api/v1/inbox/upload",
        json={"client_id": client_id, "filename": "scan_001.jpg"},
        headers=_headers(agency_id, user_id),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["extracted_vendor"] is None
    assert body["status"] == "pending"
    assert body["ai_confidence"] < 0.5


def test_approve_creates_transaction(client: TestClient, setup):
    agency_id, client_id, user_id = setup
    res = client.post(
        "/api/v1/inbox/upload",
        json={
            "client_id": client_id,
            "filename": "vinmonopolet_2026-04-10_6500nok.pdf",
        },
        headers=_headers(agency_id, user_id),
    )
    item_id = res.json()["id"]

    res = client.post(
        f"/api/v1/inbox/{item_id}/approve",
        json={},
        headers=_headers(agency_id, user_id),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "approved"
    assert body["transaction_id"] is not None


def test_reject(client: TestClient, setup):
    agency_id, client_id, user_id = setup
    res = client.post(
        "/api/v1/inbox/upload",
        json={"client_id": client_id, "filename": "scan_002.jpg"},
        headers=_headers(agency_id, user_id),
    )
    item_id = res.json()["id"]

    res = client.post(
        f"/api/v1/inbox/{item_id}/reject",
        json={"reason": "Not for this client"},
        headers=_headers(agency_id, user_id),
    )
    assert res.status_code == 200
    assert res.json()["status"] == "rejected"
    assert res.json()["rejection_reason"] == "Not for this client"


def test_list_items_filters_by_status(client: TestClient, setup):
    agency_id, client_id, user_id = setup
    for fname in ["tine_2026-04-01_3000nok.pdf", "scan_x.jpg"]:
        client.post(
            "/api/v1/inbox/upload",
            json={"client_id": client_id, "filename": fname},
            headers=_headers(agency_id, user_id),
        )
    res = client.get(
        "/api/v1/inbox?status=extracted",
        headers=_headers(agency_id, user_id),
    )
    items = res.json()
    assert len(items) == 1
    assert items[0]["extracted_vendor"] == "Tine SA"
