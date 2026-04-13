"""
Celery background-task tests.

All tests run in EAGER mode so tasks execute synchronously in the
caller's process — no Redis, no worker, no broker. The mode flag is
set via an env var BEFORE `app.celery_app` is imported.
"""
from __future__ import annotations

import os

os.environ["CELERY_TASK_ALWAYS_EAGER"] = "1"

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.celery_app import celery_app, TASK_MODULES
from app.models import (
    Agency,
    BankAccount,
    BankTransaction,
    Client,
    PayrollPeriod,
    ReportDelivery,
)
from app.services import integrations as svc
from app.services.banking.base import BankTransaction as ProviderBankTx
from app.services.money import Money
from app.tasks import banking as banking_tasks
from app.tasks import cashflow as cashflow_tasks
from app.tasks import delivery as delivery_tasks
from app.tasks import filing as filing_tasks


# ── Celery app sanity ─────────────────────────────────────────────────


def test_celery_app_is_eager_in_tests():
    assert celery_app.conf.task_always_eager is True
    assert celery_app.conf.task_eager_propagates is True


def test_celery_app_has_beat_schedule():
    expected = {
        "banking-sync-nightly",
        "cashflow-refresh-morning",
        "delivery-sweep-hourly",
        "filing-reminders-daily",
    }
    assert expected.issubset(set(celery_app.conf.beat_schedule.keys()))


def test_celery_app_registers_every_task_module():
    celery_app.loader.import_default_modules()
    registered = set(celery_app.tasks.keys())
    for module in TASK_MODULES:
        has_any = any(name.startswith(module + ".") for name in registered)
        assert has_any, f"no tasks registered from {module}"


def test_celery_json_only_serialization():
    # Never accept pickle off the wire.
    assert celery_app.conf.task_serializer == "json"
    assert "json" in celery_app.conf.accept_content
    assert "pickle" not in celery_app.conf.accept_content


# ── Shared fixtures ────────────────────────────────────────────────────


@pytest.fixture
def agency_with_client(db):
    agency = Agency(name="Task Test Agency", slug="task-test-agency")
    db.add(agency)
    db.commit()
    db.refresh(agency)
    client = Client(agency_id=agency.id, name="Task Test Client", country="NO")
    db.add(client)
    db.commit()
    db.refresh(client)
    return agency, client


# ── Banking task tests ────────────────────────────────────────────────


def test_sync_agency_returns_no_accounts_when_empty(db, agency_with_client):
    agency, _ = agency_with_client
    result = banking_tasks.sync_agency(agency.id)
    assert result["agency_id"] == agency.id
    assert result["accounts_touched"] == 0
    assert result["transactions_inserted"] == 0


def test_sync_agency_uses_mock_adapter_by_default(db, agency_with_client):
    """
    With no real Aiia credentials the factory returns MockBankingAdapter.
    Set up one local BankAccount whose account_number matches the mock
    adapter's NOK IBAN, then verify transactions are inserted.
    """
    agency, client = agency_with_client
    # MockBankingAdapter's NO account has IBAN NO9386011117947 / mock-acct-no-001
    local = BankAccount(
        client_id=client.id,
        bank_name="DNB",
        account_number="NO9386011117947",
        account_type="checking",
        currency="NOK",
        is_active=True,
    )
    db.add(local)
    db.commit()
    db.refresh(local)

    result = banking_tasks.sync_agency(agency.id)
    assert result["accounts_touched"] == 1
    assert result["transactions_inserted"] > 0

    inserted = (
        db.query(BankTransaction)
        .filter(BankTransaction.account_id == local.id)
        .all()
    )
    assert len(inserted) == result["transactions_inserted"]
    # Outflows should have been stored as negative amounts
    assert any(tx.amount < 0 for tx in inserted)
    assert any(tx.amount > 0 for tx in inserted)


def test_sync_agency_is_idempotent(db, agency_with_client):
    """Running sync twice must not duplicate transactions."""
    agency, client = agency_with_client
    local = BankAccount(
        client_id=client.id,
        bank_name="DNB",
        account_number="NO9386011117947",
        account_type="checking",
        currency="NOK",
        is_active=True,
    )
    db.add(local)
    db.commit()

    first = banking_tasks.sync_agency(agency.id)
    second = banking_tasks.sync_agency(agency.id)
    assert first["transactions_inserted"] > 0
    assert second["transactions_inserted"] == 0  # all already existed
    count = db.query(BankTransaction).count()
    assert count == first["transactions_inserted"]


def test_sync_all_agencies_skips_agencies_without_integration(db, agency_with_client):
    # No integration configured at all → the sweep should report 0 agencies.
    result = banking_tasks.sync_all_agencies()
    assert result["agencies_found"] == 0
    assert result["dispatched"] == 0


def test_sync_all_agencies_dispatches_configured_agencies(db, agency_with_client):
    agency, _ = agency_with_client
    svc.set_config(
        db,
        agency.id,
        "aiia",
        {"client_id": "x", "client_secret": "y", "environment": "sandbox"},
    )
    result = banking_tasks.sync_all_agencies()
    assert result["agencies_found"] == 1
    assert result["dispatched"] == 1


# ── Delivery task tests ──────────────────────────────────────────────


@pytest.fixture
def pending_delivery(db, agency_with_client):
    _, client = agency_with_client
    row = ReportDelivery(
        client_id=client.id,
        report_type="monthly_management",
        period_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        period_end=datetime(2026, 3, 31, tzinfo=timezone.utc),
        currency="NOK",
        language="nb",
        status="pending",
        recipient_email="test@example.invalid",
        scheduled_for=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def test_send_report_delivery_marks_row_sent(db, pending_delivery):
    result = delivery_tasks.send_report_delivery(pending_delivery.id)
    assert result["status"] == "sent"
    db.refresh(pending_delivery)
    assert pending_delivery.status == "sent"
    assert pending_delivery.sent_at is not None
    assert pending_delivery.delivery_provider == "mock"


def test_send_report_delivery_already_sent_is_noop(db, pending_delivery):
    pending_delivery.status = "sent"
    pending_delivery.sent_at = datetime.now(timezone.utc)
    db.commit()
    result = delivery_tasks.send_report_delivery(pending_delivery.id)
    assert result["status"] == "already_sent"


def test_send_report_delivery_missing_row_returns_missing():
    result = delivery_tasks.send_report_delivery(999999)
    assert result["status"] == "missing"


def test_sweep_pending_deliveries_dispatches_eligible_rows(db, pending_delivery):
    result = delivery_tasks.sweep_pending_deliveries()
    assert result["candidates"] >= 1
    # Eager mode means the child task has already run.
    db.refresh(pending_delivery)
    assert pending_delivery.status == "sent"


def test_sweep_ignores_future_scheduled_rows(db, pending_delivery):
    pending_delivery.scheduled_for = datetime.now(timezone.utc) + timedelta(days=1)
    db.commit()
    result = delivery_tasks.sweep_pending_deliveries()
    assert result["candidates"] == 0


# ── Filing task tests ────────────────────────────────────────────────


def test_check_upcoming_deadlines_finds_open_periods_in_window(db, agency_with_client):
    _, client = agency_with_client
    now = datetime.now(timezone.utc)
    db.add(
        PayrollPeriod(
            client_id=client.id,
            year=2026,
            month=4,
            period_start=now - timedelta(days=15),
            period_end=now + timedelta(days=3),  # inside 7-day window
            status="open",
        )
    )
    db.add(
        PayrollPeriod(
            client_id=client.id,
            year=2026,
            month=5,
            period_start=now + timedelta(days=30),
            period_end=now + timedelta(days=60),  # outside window
            status="open",
        )
    )
    db.commit()

    result = filing_tasks.check_upcoming_deadlines()
    assert result["due_count"] == 1
    assert result["due"][0]["client_id"] == client.id


def test_check_upcoming_deadlines_ignores_closed_periods(db, agency_with_client):
    _, client = agency_with_client
    now = datetime.now(timezone.utc)
    db.add(
        PayrollPeriod(
            client_id=client.id,
            year=2026,
            month=4,
            period_start=now - timedelta(days=15),
            period_end=now + timedelta(days=3),
            status="submitted",  # already filed
        )
    )
    db.commit()
    result = filing_tasks.check_upcoming_deadlines()
    assert result["due_count"] == 0


# ── Cashflow task tests ──────────────────────────────────────────────


def test_refresh_all_clients_counts_active_clients(db, agency_with_client):
    _, client = agency_with_client
    # One inactive client should not be counted
    db.add(
        Client(agency_id=client.agency_id, name="Archived", country="NO", is_active=False)
    )
    db.commit()
    result = cashflow_tasks.refresh_all_clients()
    assert result["active_clients"] == 1
    assert result["dispatched"] == 0
