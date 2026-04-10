"""Tests for Sprint 19 – Professional Services Vertical."""
from datetime import time, date, timedelta
from decimal import Decimal
from types import SimpleNamespace

from fastapi.testclient import TestClient
from app.main import app
from app.routers.professional_services import router as ps_router
from app.services.time_tracking_service import (
    calculate_units,
    calculate_wip,
    get_wip_aging,
    calculate_utilisation,
)

# Register the PS router if not already included
_registered = False
for route in app.routes:
    if hasattr(route, "path") and str(route.path).startswith("/ps/"):
        _registered = True
        break
if not _registered:
    app.include_router(ps_router)

client = TestClient(app)


# ------------------------------------------------------------------ #
#  Auth guard tests – every endpoint must return 401 without a token  #
# ------------------------------------------------------------------ #

def test_create_matter_requires_auth():
    response = client.post("/ps/matters", json={"client_id": 1, "name": "Test"})
    assert response.status_code in (401, 403)


def test_list_matters_requires_auth():
    response = client.get("/ps/matters")
    assert response.status_code in (401, 403)


def test_get_matter_requires_auth():
    response = client.get("/ps/matters/1")
    assert response.status_code in (401, 403)


def test_create_time_entry_requires_auth():
    response = client.post("/ps/time-entries", json={"matter_id": 1, "date": "2026-01-01"})
    assert response.status_code in (401, 403)


def test_list_time_entries_requires_auth():
    response = client.get("/ps/time-entries")
    assert response.status_code in (401, 403)


def test_create_billing_rate_requires_auth():
    response = client.post("/ps/billing-rates", json={"client_id": 1, "hourly_rate": "100.00"})
    assert response.status_code in (401, 403)


def test_list_billing_rates_requires_auth():
    response = client.get("/ps/billing-rates")
    assert response.status_code in (401, 403)


def test_wip_aging_requires_auth():
    response = client.get("/ps/wip/aging")
    assert response.status_code in (401, 403)


def test_create_trust_transaction_requires_auth():
    response = client.post(
        "/ps/trust-transactions",
        json={"client_id": 1, "transaction_type": "receipt", "amount": "500", "transaction_date": "2026-01-01"},
    )
    assert response.status_code in (401, 403)


def test_list_trust_transactions_requires_auth():
    response = client.get("/ps/trust-transactions")
    assert response.status_code in (401, 403)


def test_create_disbursement_requires_auth():
    response = client.post(
        "/ps/disbursements",
        json={"matter_id": 1, "date": "2026-01-01", "amount": "100.00"},
    )
    assert response.status_code in (401, 403)


def test_utilisation_requires_auth():
    response = client.get("/ps/utilisation")
    assert response.status_code in (401, 403)


# ------------------------------------------------------------------ #
#  Unit calculation tests                                              #
# ------------------------------------------------------------------ #

def test_calculate_units_30_mins():
    """30 minutes = 5.0 units (five 6-minute blocks)."""
    result = calculate_units(time(9, 0), time(9, 30))
    assert result == Decimal("5")


def test_calculate_units_6_mins():
    """6 minutes = 1.0 unit."""
    result = calculate_units(time(9, 0), time(9, 6))
    assert result == Decimal("1")


def test_calculate_units_18_mins():
    """18 minutes = 3.0 units."""
    result = calculate_units(time(9, 0), time(9, 18))
    assert result == Decimal("3")


def test_calculate_units_zero():
    """Same start and end time = 0 units."""
    result = calculate_units(time(9, 0), time(9, 0))
    assert result == Decimal("0")


def test_calculate_units_60_mins():
    """60 minutes = 10.0 units."""
    result = calculate_units(time(10, 0), time(11, 0))
    assert result == Decimal("10")


def test_calculate_units_rounding():
    """7 minutes should round to 1 unit (nearest 6-min block)."""
    result = calculate_units(time(9, 0), time(9, 7))
    assert result == Decimal("1")


# ------------------------------------------------------------------ #
#  WIP calculation tests                                               #
# ------------------------------------------------------------------ #

def test_calculate_wip_basic():
    """5 units at R200/hr => 5 * 20 = R100."""
    result = calculate_wip(matter_id=1, hourly_rate=Decimal("200"), units=Decimal("5"))
    assert result == Decimal("100.00")


# ------------------------------------------------------------------ #
#  WIP aging bucket tests                                              #
# ------------------------------------------------------------------ #

def test_wip_aging_buckets():
    """Test that WIP entries are bucketed correctly."""
    today = date(2026, 4, 10)

    entries = [
        SimpleNamespace(period_end=today - timedelta(days=10), wip_value=Decimal("100")),   # 0-30
        SimpleNamespace(period_end=today - timedelta(days=25), wip_value=Decimal("200")),   # 0-30
        SimpleNamespace(period_end=today - timedelta(days=45), wip_value=Decimal("300")),   # 31-60
        SimpleNamespace(period_end=today - timedelta(days=75), wip_value=Decimal("400")),   # 61-90
        SimpleNamespace(period_end=today - timedelta(days=120), wip_value=Decimal("500")),  # over_90
    ]

    buckets = get_wip_aging(entries, today)

    assert buckets["0_30"] == Decimal("300")
    assert buckets["31_60"] == Decimal("300")
    assert buckets["61_90"] == Decimal("400")
    assert buckets["over_90"] == Decimal("500")


def test_wip_aging_empty():
    """Empty list should produce all-zero buckets."""
    buckets = get_wip_aging([], date.today())
    assert buckets["0_30"] == Decimal("0")
    assert buckets["31_60"] == Decimal("0")
    assert buckets["61_90"] == Decimal("0")
    assert buckets["over_90"] == Decimal("0")


# ------------------------------------------------------------------ #
#  Utilisation calculation tests                                       #
# ------------------------------------------------------------------ #

def test_utilisation_basic():
    """total=100, billable=75 => 75%."""
    result = calculate_utilisation(Decimal("100"), Decimal("75"))
    assert result == Decimal("75.00")


def test_utilisation_zero_total():
    """Zero total should return 0."""
    result = calculate_utilisation(Decimal("0"), Decimal("0"))
    assert result == Decimal("0")


def test_utilisation_full():
    """total=50, billable=50 => 100%."""
    result = calculate_utilisation(Decimal("50"), Decimal("50"))
    assert result == Decimal("100.00")
