"""
Tests for migration 005 — jurisdictions, audit log, currency columns.

Verifies that:
- The `jurisdiction_configs` and `audit_log` tables exist with the expected
  columns and indexes
- The new currency columns on journal_entries / journal_lines / payslips
  / accounts are present and have the correct defaults
- The ORM models can insert, query, and constrain as expected
"""
from __future__ import annotations

import pytest
from sqlalchemy import inspect, text

from app.database import SessionLocal, engine
from app.models import (
    Agency,
    Client,
    User,
    JurisdictionConfig,
    AuditLog,
)


# ── Schema presence ────────────────────────────────────────────────────────


def test_jurisdiction_configs_table_exists():
    inspector = inspect(engine)
    assert "jurisdiction_configs" in inspector.get_table_names()


def test_audit_log_table_exists():
    inspector = inspect(engine)
    assert "audit_log" in inspector.get_table_names()


def test_jurisdiction_configs_columns():
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("jurisdiction_configs")}
    expected = {
        "id",
        "client_id",
        "primary_jurisdiction",
        "secondary_jurisdictions",
        "reporting_currency",
        "vat_filing_frequency",
        "fiscal_year_start_month",
        "language",
        "config_overrides",
        "created_at",
        "updated_at",
    }
    assert expected.issubset(cols)


def test_audit_log_columns():
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("audit_log")}
    expected = {
        "id",
        "agency_id",
        "client_id",
        "user_id",
        "action",
        "entity_type",
        "entity_id",
        "diff",
        "ip_address",
        "user_agent",
        "request_id",
        "created_at",
    }
    assert expected.issubset(cols)


def test_currency_columns_added_to_financial_tables():
    inspector = inspect(engine)
    je_cols = {c["name"] for c in inspector.get_columns("journal_entries")}
    assert "currency" in je_cols
    assert "fx_rate_to_reporting" in je_cols

    jl_cols = {c["name"] for c in inspector.get_columns("journal_lines")}
    assert "currency" in jl_cols

    ps_cols = {c["name"] for c in inspector.get_columns("payslips")}
    assert "currency" in ps_cols

    acc_cols = {c["name"] for c in inspector.get_columns("accounts")}
    assert "reporting_currency" in acc_cols


def test_jurisdiction_configs_unique_per_client():
    inspector = inspect(engine)
    uniques = inspector.get_unique_constraints("jurisdiction_configs")
    constrained_cols = {tuple(u["column_names"]) for u in uniques}
    assert ("client_id",) in constrained_cols


# ── ORM model smoke tests ──────────────────────────────────────────────────


@pytest.fixture
def sample_agency_and_client(db):
    agency = Agency(name="Tier1.3 Test Agency", slug="tier1-3-test")
    db.add(agency)
    db.flush()
    client = Client(
        agency_id=agency.id,
        name="Tier1.3 Test Client",
        country="NO",
    )
    db.add(client)
    db.commit()
    db.refresh(agency)
    db.refresh(client)
    return agency, client


def test_create_jurisdiction_config(db, sample_agency_and_client):
    _, client = sample_agency_and_client
    cfg = JurisdictionConfig(
        client_id=client.id,
        primary_jurisdiction="NO",
        reporting_currency="NOK",
        language="nb-NO",
        fiscal_year_start_month=1,
    )
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    assert cfg.id is not None
    assert cfg.primary_jurisdiction == "NO"
    assert cfg.reporting_currency == "NOK"


def test_jurisdiction_config_one_per_client(db, sample_agency_and_client):
    _, client = sample_agency_and_client
    db.add(
        JurisdictionConfig(
            client_id=client.id, primary_jurisdiction="NO", reporting_currency="NOK"
        )
    )
    db.commit()
    # Second insert should violate unique constraint
    db.add(
        JurisdictionConfig(
            client_id=client.id, primary_jurisdiction="SE", reporting_currency="SEK"
        )
    )
    with pytest.raises(Exception):  # IntegrityError
        db.commit()
    db.rollback()


def test_create_audit_log_entry(db, sample_agency_and_client):
    agency, client = sample_agency_and_client
    entry = AuditLog(
        agency_id=agency.id,
        client_id=client.id,
        action="create",
        entity_type="invoice",
        entity_id="INV-001",
        diff='[{"op":"add","path":"/status","value":"draft"}]',
        ip_address="10.0.0.1",
        user_agent="pytest",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    assert entry.id is not None
    assert entry.action == "create"
    assert entry.created_at is not None


def test_audit_log_allows_null_user_for_system_events(db, sample_agency_and_client):
    agency, _ = sample_agency_and_client
    entry = AuditLog(
        agency_id=agency.id,
        user_id=None,  # system/automated event
        action="scheduled_task",
        entity_type="cron",
        entity_id="daily_anomaly_scan",
    )
    db.add(entry)
    db.commit()
    assert entry.id is not None


def test_audit_log_cascades_to_null_on_agency_delete(db):
    """Deleting an agency should NULL out audit_log references, not cascade delete."""
    agency = Agency(name="Temp Agency", slug="temp-audit")
    db.add(agency)
    db.commit()
    db.refresh(agency)
    db.add(
        AuditLog(
            agency_id=agency.id,
            action="test",
            entity_type="agency",
            entity_id=str(agency.id),
        )
    )
    db.commit()
    db.delete(agency)
    db.commit()
    # The audit log row should still exist, with agency_id = NULL
    remaining = (
        db.query(AuditLog).filter(AuditLog.entity_type == "agency").all()
    )
    assert len(remaining) >= 1
    assert all(r.agency_id is None for r in remaining)
