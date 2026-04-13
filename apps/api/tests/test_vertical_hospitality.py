"""Hospitality vertical tests — KPI math, PMS adapter, VAT splitting."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.services.money import Money
from app.services.verticals.hospitality import (
    Property,
    RoomCategory,
    RevenueLineItem,
    RoomStats,
    calculate_revpar,
    calculate_adr,
    calculate_occupancy,
    MockPMSAdapter,
    get_pms_adapter,
    split_revenue_by_country,
)
from app.services.verticals.hospitality.models import OutletType


# ── KPI calculations ─────────────────────────────────────────────────────


def test_revpar_rooms_available_vs_rooms_sold():
    """RevPAR = revenue / rooms AVAILABLE, not rooms sold.
    This is the single most commonly-confused hospitality metric."""
    stats = RoomStats(
        room_revenue=Money("60000.00", "NOK"),
        rooms_sold=45,
        rooms_available=60,
    )
    # RevPAR = 60000 / 60 = 1000
    assert calculate_revpar(stats) == Money("1000.00", "NOK")


def test_revpar_zero_capacity_returns_zero_not_error():
    """Seasonal closures — zero rooms available means zero RevPAR, not crash."""
    stats = RoomStats(
        room_revenue=Money("0", "NOK"),
        rooms_sold=0,
        rooms_available=0,
    )
    assert calculate_revpar(stats) == Money.zero("NOK")


def test_adr_uses_rooms_sold_not_available():
    """ADR = revenue / rooms SOLD."""
    stats = RoomStats(
        room_revenue=Money("60000.00", "NOK"),
        rooms_sold=45,
        rooms_available=60,
    )
    # ADR = 60000 / 45 = 1333.33
    adr = calculate_adr(stats)
    assert adr is not None
    assert adr.amount == Decimal("1333.33")


def test_adr_zero_rooms_sold_returns_none():
    """ADR is undefined when no rooms were sold — must return None."""
    stats = RoomStats(
        room_revenue=Money("0", "NOK"),
        rooms_sold=0,
        rooms_available=60,
    )
    assert calculate_adr(stats) is None


def test_occupancy_returns_decimal_fraction():
    stats = RoomStats(
        room_revenue=Money("60000", "NOK"),
        rooms_sold=45,
        rooms_available=60,
    )
    # 45/60 = 0.75
    assert calculate_occupancy(stats) == Decimal("0.75")


def test_occupancy_zero_capacity_returns_zero():
    stats = RoomStats(
        room_revenue=Money("0", "NOK"),
        rooms_sold=0,
        rooms_available=0,
    )
    assert calculate_occupancy(stats) == Decimal("0")


def test_revpar_equals_adr_times_occupancy():
    """Industry identity: RevPAR ≡ ADR × Occupancy."""
    stats = RoomStats(
        room_revenue=Money("60000.00", "NOK"),
        rooms_sold=45,
        rooms_available=60,
    )
    revpar = calculate_revpar(stats)
    adr = calculate_adr(stats)
    occupancy = calculate_occupancy(stats)
    # ADR * occupancy should equal RevPAR (within rounding tolerance)
    derived = Money(adr.amount * occupancy, "NOK")
    # Allow 1 øre tolerance for rounding
    diff = abs(derived.amount - revpar.amount)
    assert diff <= Decimal("0.01")


# ── PMS adapter ──────────────────────────────────────────────────────────


def test_mock_pms_adapter_returns_daily_revenue():
    adapter = MockPMSAdapter()
    result = adapter.fetch_daily_revenue(property_id=42, day=date(2026, 4, 13))
    assert result.property_id == 42
    assert result.date == date(2026, 4, 13)
    assert result.rooms_sold == 45
    assert result.rooms_available == 60
    assert result.pms_name == "mock"
    assert len(result.line_items) == 4


def test_mock_pms_split_sums_to_daily_total():
    adapter = MockPMSAdapter(
        currency="NOK",
        daily_total=Money("100000", "NOK"),
    )
    result = adapter.fetch_daily_revenue(property_id=1, day=date(2026, 4, 13))
    total = Money.zero("NOK")
    for item in result.line_items:
        total = total + item.amount
    # Allow 1 øre rounding tolerance
    diff = abs(total.amount - Decimal("100000"))
    assert diff <= Decimal("0.10")


def test_mock_pms_default_split_weights_rooms_at_60_percent():
    adapter = MockPMSAdapter(daily_total=Money("100000", "NOK"))
    result = adapter.fetch_daily_revenue(property_id=1, day=date(2026, 4, 13))
    rooms = next(i for i in result.line_items if i.outlet_type == "rooms")
    assert rooms.amount == Money("60000.00", "NOK")


def test_mock_pms_split_must_sum_to_one():
    with pytest.raises(ValueError):
        MockPMSAdapter(
            split={"rooms": 0.5, "food": 0.3}  # sums to 0.8, invalid
        )


def test_get_pms_adapter_mock():
    adapter = get_pms_adapter("mock")
    assert isinstance(adapter, MockPMSAdapter)


def test_get_pms_adapter_unknown_raises():
    with pytest.raises(ValueError):
        get_pms_adapter("nonexistent-pms")


# ── VAT splitting ────────────────────────────────────────────────────────


def test_vat_split_norway_rooms_12_percent():
    """Norwegian hotel rooms are 12% VAT."""
    items = [
        RevenueLineItem(outlet_type="rooms", amount=Money("1120.00", "NOK")),
    ]
    result = split_revenue_by_country("NO", items)
    assert len(result.lines) == 1
    line = result.lines[0]
    assert line.vat_code == "NO-12"
    assert line.rate == Decimal("0.12")
    # Gross 1120 = Net 1000 + VAT 120
    assert line.net == Money("1000.00", "NOK")
    assert line.vat == Money("120.00", "NOK")


def test_vat_split_norway_food_25_percent():
    """Norwegian hotel F&B is 25% VAT (different from rooms)."""
    items = [
        RevenueLineItem(outlet_type="food", amount=Money("1250.00", "NOK")),
    ]
    result = split_revenue_by_country("NO", items)
    line = result.lines[0]
    assert line.vat_code == "NO-25"
    assert line.rate == Decimal("0.25")
    # Gross 1250 = Net 1000 + VAT 250
    assert line.net == Money("1000.00", "NOK")
    assert line.vat == Money("250.00", "NOK")


def test_vat_split_sweden_restaurant_food_12_percent():
    """Swedish restaurant food is 12% since 2024."""
    items = [
        RevenueLineItem(outlet_type="food", amount=Money("1120.00", "SEK")),
    ]
    result = split_revenue_by_country("SE", items)
    line = result.lines[0]
    assert line.rate == Decimal("0.12")


def test_vat_split_sweden_alcohol_25_percent():
    """Swedish alcoholic beverages are always 25% regardless of venue."""
    items = [
        RevenueLineItem(outlet_type="beverage_alcohol", amount=Money("1250.00", "SEK")),
    ]
    result = split_revenue_by_country("SE", items)
    line = result.lines[0]
    assert line.rate == Decimal("0.25")


def test_vat_split_finland_food_14_percent():
    """Finnish restaurant food is 14%."""
    items = [
        RevenueLineItem(outlet_type="food", amount=Money("1140.00", "EUR")),
    ]
    result = split_revenue_by_country("FI", items)
    line = result.lines[0]
    assert line.rate == Decimal("0.14")


def test_vat_split_finland_alcohol_25_5_percent():
    """Finnish alcohol gets the new 25.5% standard rate."""
    items = [
        RevenueLineItem(outlet_type="beverage_alcohol", amount=Money("1255.00", "EUR")),
    ]
    result = split_revenue_by_country("FI", items)
    line = result.lines[0]
    assert line.rate == Decimal("0.255")


def test_vat_split_totals_correct_across_multiple_outlets():
    """Mixed-outlet day: totals should reconcile across rooms+food+alcohol."""
    items = [
        RevenueLineItem(outlet_type="rooms", amount=Money("11200", "NOK")),
        RevenueLineItem(outlet_type="food", amount=Money("6250", "NOK")),
        RevenueLineItem(outlet_type="beverage_alcohol", amount=Money("3750", "NOK")),
    ]
    result = split_revenue_by_country("NO", items)
    assert result.total_gross == Money("21200.00", "NOK")
    # Rooms: 11200 → net 10000 + vat 1200
    # Food: 6250 → net 5000 + vat 1250
    # Alcohol: 3750 → net 3000 + vat 750
    assert result.total_net == Money("18000.00", "NOK")
    assert result.total_vat == Money("3200.00", "NOK")


def test_vat_split_currency_mismatch_rejected():
    items = [
        RevenueLineItem(outlet_type="rooms", amount=Money("1000", "NOK")),
        RevenueLineItem(outlet_type="food", amount=Money("500", "EUR")),
    ]
    with pytest.raises(ValueError):
        split_revenue_by_country("NO", items)


def test_vat_split_unknown_country_rejected():
    items = [
        RevenueLineItem(outlet_type="rooms", amount=Money("1000", "USD")),
    ]
    with pytest.raises(ValueError):
        split_revenue_by_country("US", items)


def test_vat_split_empty_list_rejected():
    with pytest.raises(ValueError):
        split_revenue_by_country("NO", [])
