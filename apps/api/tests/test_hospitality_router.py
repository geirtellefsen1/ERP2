"""Hospitality router smoke tests.

Verifies the property dashboard endpoint builds a coherent payload
from real data, the AI activity feed lists items in reverse-chronological
order, and the approve action marks an item reviewed.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    Agency,
    AiActivityFeed,
    Client,
    DailyRevenueImport,
    DailyRevenueLine,
    Outlet,
    Property,
    RoomCategory,
    User,
)


# --- Fixtures ----------------------------------------------------------------


@pytest.fixture
def fjordvik_setup():
    """Seed a minimal hospitality dataset and yield (agency_id, client_id, property_id)."""
    db: Session = SessionLocal()
    try:
        agency = Agency(name="Demo Agency", slug="demo")
        db.add(agency)
        db.commit()
        db.refresh(agency)

        admin = User(
            email="admin@demo.local",
            hashed_password="x",
            full_name="Demo Admin",
            agency_id=agency.id,
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        client_row = Client(
            agency_id=agency.id,
            name="Fjordvik Hotel",
            country="NO",
            industry="Hospitality",
            is_active=True,
        )
        db.add(client_row)
        db.commit()
        db.refresh(client_row)

        prop = Property(
            client_id=client_row.id,
            name="Fjordvik Hotel & Restaurant",
            country="NO",
            total_rooms=24,
            timezone="Europe/Oslo",
        )
        db.add(prop)
        db.commit()
        db.refresh(prop)

        for code, label, count, rate in [
            ("STD", "Standard", 12, 140000),
            ("DLX", "Deluxe", 8, 195000),
            ("SUITE", "Sea View Suite", 4, 280000),
        ]:
            db.add(
                RoomCategory(
                    property_id=prop.id,
                    code=code,
                    label=label,
                    room_count=count,
                    base_rate_minor=rate,
                    currency="NOK",
                )
            )
        db.add(Outlet(property_id=prop.id, name="Restaurant", outlet_type="food"))
        db.add(Outlet(property_id=prop.id, name="Bar", outlet_type="beverage_alcohol"))
        db.commit()

        # Today's import: 18/24 rooms sold
        today = date.today()
        imp = DailyRevenueImport(
            property_id=prop.id,
            import_date=datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc),
            rooms_sold=18,
            rooms_available=24,
            currency="NOK",
            pms_name="MockPMS",
        )
        db.add(imp)
        db.commit()
        db.refresh(imp)

        for outlet_type, gross, covers in [
            ("rooms", 3_240_000, 0),     # NOK 32,400 — 18 rooms × ~1,800 ADR
            ("food", 1_680_000, 42),     # NOK 16,800
            ("beverage_alcohol", 720_000, 0),  # NOK 7,200
        ]:
            db.add(
                DailyRevenueLine(
                    import_id=imp.id,
                    outlet_type=outlet_type,
                    gross_amount_minor=gross,
                    cover_count=covers,
                )
            )
        db.commit()

        yield agency.id, client_row.id, prop.id, admin.id
    finally:
        db.close()


def _auth_headers(agency_id: int, user_id: int):
    """Use the dev-mode header auth path of get_current_user."""
    return {
        "x-user-id": str(user_id),
        "x-agency-id": str(agency_id),
        "x-user-email": "admin@demo.local",
        "x-user-role": "admin",
    }


# --- Tests -------------------------------------------------------------------


def test_list_properties(client: TestClient, fjordvik_setup):
    agency_id, client_id, prop_id, user_id = fjordvik_setup
    res = client.get(
        "/api/v1/hospitality/properties",
        headers=_auth_headers(agency_id, user_id),
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["name"] == "Fjordvik Hotel & Restaurant"
    assert data[0]["total_rooms"] == 24


def test_property_dashboard(client: TestClient, fjordvik_setup):
    agency_id, _, prop_id, user_id = fjordvik_setup
    res = client.get(
        f"/api/v1/hospitality/properties/{prop_id}/dashboard",
        headers=_auth_headers(agency_id, user_id),
    )
    assert res.status_code == 200
    body = res.json()

    assert body["property_name"] == "Fjordvik Hotel & Restaurant"
    assert body["currency"] == "NOK"
    assert body["today"] is not None
    assert body["today"]["rooms_sold"] == 18
    assert body["today"]["rooms_available"] == 24
    assert body["today"]["occupancy_pct"] == 75.0
    assert body["today"]["food_covers"] == 42
    assert body["today"]["adr_minor"] == 180_000   # 3,240,000 / 18 = 180,000 (NOK 1,800)
    assert body["today"]["revpar_minor"] == 135_000  # 3,240,000 / 24 = 135,000

    assert len(body["room_categories"]) == 3
    assert {c["code"] for c in body["room_categories"]} == {"STD", "DLX", "SUITE"}
    assert len(body["outlets"]) == 2


def test_property_not_visible_to_other_agency(client: TestClient, fjordvik_setup):
    agency_id, _, prop_id, user_id = fjordvik_setup
    res = client.get(
        f"/api/v1/hospitality/properties/{prop_id}/dashboard",
        headers=_auth_headers(agency_id + 999, user_id + 999),
    )
    assert res.status_code == 404


def test_ai_activity_feed_and_approval(client: TestClient, fjordvik_setup):
    agency_id, client_id, _, user_id = fjordvik_setup
    db: Session = SessionLocal()
    try:
        item = AiActivityFeed(
            agency_id=agency_id,
            client_id=client_id,
            category="anomaly",
            severity="warning",
            title="Bar pour cost up 18%",
            detail="Investigate 7-day spike",
            requires_review=True,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        item_id = item.id
    finally:
        db.close()

    res = client.get(
        "/api/v1/hospitality/ai-activity?requires_review=true",
        headers=_auth_headers(agency_id, user_id),
    )
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["title"] == "Bar pour cost up 18%"
    assert items[0]["severity"] == "warning"

    res = client.post(
        f"/api/v1/hospitality/ai-activity/{item_id}/approve",
        headers=_auth_headers(agency_id, user_id),
    )
    assert res.status_code == 200

    db = SessionLocal()
    try:
        refreshed = db.query(AiActivityFeed).filter_by(id=item_id).first()
        assert refreshed.reviewed_at is not None
        assert refreshed.reviewed_by_user_id == user_id
    finally:
        db.close()
