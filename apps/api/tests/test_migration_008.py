"""Tests for migration 008 — hospitality + professional services tables."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import inspect, text

from app.database import engine
from app.models import (
    Agency,
    Client,
    Property,
    RoomCategory,
    Outlet,
    DailyRevenueImport,
    DailyRevenueLine,
    Matter,
    FeeEarner,
    BillingRate,
    WipEntry,
)


# ── Schema presence ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "table",
    [
        "properties",
        "room_categories",
        "outlets",
        "daily_revenue_imports",
        "daily_revenue_lines",
        "matters",
        "fee_earners",
        "billing_rates",
        "wip_entries",
    ],
)
def test_vertical_table_exists(table):
    inspector = inspect(engine)
    assert table in inspector.get_table_names()


def test_properties_columns():
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("properties")}
    assert {
        "id", "client_id", "name", "country", "total_rooms",
        "opening_date", "timezone", "created_at",
    }.issubset(cols)


def test_wip_entries_columns():
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("wip_entries")}
    assert {
        "id", "matter_id", "fee_earner_id", "worked_on", "hours",
        "hourly_rate_minor", "currency", "description", "status",
        "logged_at", "billed_at", "written_off_at",
    }.issubset(cols)


# ── ORM smoke tests ────────────────────────────────────────────────────────


@pytest.fixture
def sample_client(db):
    agency = Agency(name="Tier4 Agency", slug="tier4-agency")
    db.add(agency)
    db.flush()
    client = Client(agency_id=agency.id, name="Tier4 Client", country="NO")
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def test_create_property(db, sample_client):
    prop = Property(
        client_id=sample_client.id,
        name="Molteno Estate Lodge",
        country="NO",
        total_rooms=12,
        timezone="Europe/Oslo",
    )
    db.add(prop)
    db.commit()
    db.refresh(prop)
    assert prop.id is not None
    assert prop.total_rooms == 12


def test_create_matter_with_fee_earner(db, sample_client):
    matter = Matter(
        client_id=sample_client.id,
        code="ACME-2026-001",
        title="Acme acquisition due diligence",
        matter_type="corporate",
        status="open",
        opened_on=datetime(2026, 1, 1, tzinfo=timezone.utc),
        currency="NOK",
    )
    db.add(matter)
    db.flush()

    fe = FeeEarner(
        client_id=sample_client.id,
        name="Nils Hansen",
        email="nils@firm.no",
        grade="partner",
        default_hourly_rate_minor=500000,  # NOK 5000 in øre
        currency="NOK",
    )
    db.add(fe)
    db.commit()
    db.refresh(matter)
    db.refresh(fe)

    wip = WipEntry(
        matter_id=matter.id,
        fee_earner_id=fe.id,
        worked_on=datetime(2026, 4, 13, tzinfo=timezone.utc),
        hours=Decimal("2.5"),
        hourly_rate_minor=500000,
        currency="NOK",
        description="Reviewed draft SPA",
        status="unbilled",
    )
    db.add(wip)
    db.commit()
    db.refresh(wip)
    assert wip.id is not None
    assert wip.status == "unbilled"


def test_property_cascades_to_room_categories(db, sample_client):
    prop = Property(
        client_id=sample_client.id,
        name="Cascade Test",
        country="NO",
        total_rooms=10,
    )
    db.add(prop)
    db.flush()
    db.add(
        RoomCategory(
            property_id=prop.id,
            code="STD",
            label="Standard",
            room_count=8,
            base_rate_minor=80000,
            currency="NOK",
        )
    )
    db.commit()

    db.delete(prop)
    db.commit()

    remaining = db.query(RoomCategory).filter(RoomCategory.code == "STD").all()
    assert remaining == []


# ── RLS policy check ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "table",
    [
        "properties",
        "room_categories",
        "outlets",
        "daily_revenue_imports",
        "daily_revenue_lines",
        "matters",
        "fee_earners",
        "billing_rates",
        "wip_entries",
    ],
)
def test_vertical_table_has_rls_policy(table):
    with engine.connect() as conn:
        result = conn.execute(
            text(
                f"SELECT polname FROM pg_policy WHERE polrelid = "
                f"'public.{table}'::regclass"
            )
        ).fetchall()
    names = {r[0] for r in result}
    assert "tenant_isolation" in names
