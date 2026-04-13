"""Tests for migration 007 — cashflow_snapshots and report_deliveries."""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from sqlalchemy import inspect, text

from app.database import engine
from app.models import (
    Agency,
    Client,
    CashflowSnapshot,
    ReportDelivery,
)


# ── Schema presence ────────────────────────────────────────────────────────


def test_cashflow_snapshots_table_exists():
    inspector = inspect(engine)
    assert "cashflow_snapshots" in inspector.get_table_names()


def test_report_deliveries_table_exists():
    inspector = inspect(engine)
    assert "report_deliveries" in inspector.get_table_names()


def test_cashflow_snapshots_columns():
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("cashflow_snapshots")}
    expected = {
        "id", "client_id", "snapshot_date", "currency",
        "opening_balance_minor", "closing_balance_minor",
        "weeks_count", "threshold_minor", "breach_week_count",
        "weeks_json", "narrative", "narrative_language",
        "created_at",
    }
    assert expected.issubset(cols)


def test_report_deliveries_columns():
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("report_deliveries")}
    expected = {
        "id", "client_id", "report_type", "period_start", "period_end",
        "currency", "language", "pdf_path", "pdf_size_bytes",
        "status", "recipient_email", "delivery_provider",
        "delivery_message_id", "delivery_error",
        "scheduled_for", "sent_at", "created_at",
    }
    assert expected.issubset(cols)


# ── ORM smoke tests ────────────────────────────────────────────────────────


@pytest.fixture
def sample_client(db):
    agency = Agency(name="Tier3 Agency", slug="tier3-agency")
    db.add(agency)
    db.flush()
    client = Client(agency_id=agency.id, name="Tier3 Client", country="NO")
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def test_create_cashflow_snapshot(db, sample_client):
    snap = CashflowSnapshot(
        client_id=sample_client.id,
        snapshot_date=datetime(2026, 4, 12, tzinfo=timezone.utc),
        currency="NOK",
        opening_balance_minor=10_000_000,  # 100,000 NOK in øre
        closing_balance_minor=8_500_000,
        weeks_count=13,
        threshold_minor=5_000_000,
        breach_week_count=2,
        weeks_json='[{"week":0,"close":95000}]',
        narrative="Cash dipping from week 5 onwards.",
        narrative_language="nb-NO",
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    assert snap.id is not None
    assert snap.opening_balance_minor == 10_000_000
    assert snap.breach_week_count == 2


def test_create_report_delivery(db, sample_client):
    delivery = ReportDelivery(
        client_id=sample_client.id,
        report_type="monthly_management",
        period_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        period_end=datetime(2026, 3, 31, tzinfo=timezone.utc),
        currency="NOK",
        language="nb-NO",
        pdf_path="reports/acme/2026-03.pdf",
        pdf_size_bytes=156000,
        status="sent",
        recipient_email="admin@acme.no",
        delivery_provider="mock",
        delivery_message_id="mock-00000001",
        sent_at=datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc),
    )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    assert delivery.id is not None
    assert delivery.status == "sent"


def test_cashflow_snapshot_cascades_on_client_delete(db, sample_client):
    snap = CashflowSnapshot(
        client_id=sample_client.id,
        snapshot_date=datetime(2026, 4, 12, tzinfo=timezone.utc),
        currency="NOK",
        opening_balance_minor=0,
        closing_balance_minor=0,
        weeks_json="[]",
    )
    db.add(snap)
    db.commit()
    snap_id = snap.id

    db.delete(sample_client)
    db.commit()

    remaining = db.query(CashflowSnapshot).filter(CashflowSnapshot.id == snap_id).first()
    assert remaining is None


# ── RLS check (against superuser bypass) ──────────────────────────────────


def test_cashflow_snapshots_has_rls_policy():
    """Verify the RLS policy exists, even though our test connection bypasses it."""
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT polname FROM pg_policy WHERE polrelid = "
                "'public.cashflow_snapshots'::regclass"
            )
        ).fetchall()
    policy_names = {r[0] for r in result}
    assert "tenant_isolation" in policy_names


def test_report_deliveries_has_rls_policy():
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT polname FROM pg_policy WHERE polrelid = "
                "'public.report_deliveries'::regclass"
            )
        ).fetchall()
    policy_names = {r[0] for r in result}
    assert "tenant_isolation" in policy_names
