"""Professional Services vertical tests — time tracking, WIP aging, billing rates."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from app.services.money import Money
from app.services.verticals.professional import (
    BillingRate,
    FeeEarner,
    Matter,
    WipEntry,
    log_time,
    validate_time_entry,
    TimeEntryError,
    MINIMUM_INCREMENT,
    calculate_wip,
    age_wip_entries,
    resolve_rate,
    RateResolutionError,
    BillingRateMatrix,
)


# ── Time tracking validation ─────────────────────────────────────────────


def test_validate_accepts_valid_entry():
    validate_time_entry(
        hours=Decimal("1.5"),
        worked_on=date.today(),
        description="Drafted memo re: acquisition",
    )


def test_validate_rejects_zero_hours():
    with pytest.raises(TimeEntryError):
        validate_time_entry(
            hours=Decimal("0"),
            worked_on=date.today(),
            description="x",
        )


def test_validate_rejects_negative_hours():
    with pytest.raises(TimeEntryError):
        validate_time_entry(
            hours=Decimal("-1"),
            worked_on=date.today(),
            description="x",
        )


def test_validate_rejects_more_than_24_hours():
    with pytest.raises(TimeEntryError):
        validate_time_entry(
            hours=Decimal("25"),
            worked_on=date.today(),
            description="x",
        )


def test_validate_rejects_non_six_minute_increment():
    """0.13 hours is 7.8 minutes — not a clean 0.1 increment."""
    with pytest.raises(TimeEntryError) as exc:
        validate_time_entry(
            hours=Decimal("0.13"),
            worked_on=date.today(),
            description="x",
        )
    assert "6-minute" in str(exc.value) or "0.1" in str(exc.value)


def test_validate_accepts_zero_point_one():
    """0.1 hours = 6 minutes = the smallest valid increment."""
    validate_time_entry(
        hours=Decimal("0.1"),
        worked_on=date.today(),
        description="Quick call",
    )


def test_validate_accepts_eight_hours():
    validate_time_entry(
        hours=Decimal("8.0"),
        worked_on=date.today(),
        description="Full day on Smith matter",
    )


def test_validate_rejects_future_date():
    with pytest.raises(TimeEntryError):
        validate_time_entry(
            hours=Decimal("1"),
            worked_on=date.today() + timedelta(days=1),
            description="x",
        )


def test_validate_rejects_empty_description():
    with pytest.raises(TimeEntryError) as exc:
        validate_time_entry(
            hours=Decimal("1"),
            worked_on=date.today(),
            description="",
        )
    assert "conduct" in str(exc.value).lower() or "required" in str(exc.value).lower()


def test_validate_rejects_whitespace_only_description():
    with pytest.raises(TimeEntryError):
        validate_time_entry(
            hours=Decimal("1"),
            worked_on=date.today(),
            description="   ",
        )


def test_minimum_increment_constant():
    assert MINIMUM_INCREMENT == Decimal("0.1")


# ── log_time factory ──────────────────────────────────────────────────────


def test_log_time_builds_entry():
    entry = log_time(
        wip_id=1,
        matter_id=42,
        fee_earner_id=7,
        worked_on=date(2026, 4, 13),
        hours=Decimal("2.5"),
        hourly_rate=Money("3500", "NOK"),
        description="Reviewed agreement",
    )
    assert entry.matter_id == 42
    assert entry.fee_earner_id == 7
    assert entry.hours == Decimal("2.5")
    assert entry.status == "unbilled"
    assert entry.value == Money("8750.00", "NOK")  # 2.5 * 3500


def test_log_time_strips_description():
    entry = log_time(
        wip_id=1,
        matter_id=42,
        fee_earner_id=7,
        worked_on=date.today(),
        hours=Decimal("1"),
        hourly_rate=Money("3000", "NOK"),
        description="  Drafted memo  ",
    )
    assert entry.description == "Drafted memo"


# ── WIP total ─────────────────────────────────────────────────────────────


@pytest.fixture
def sample_wip_entries():
    """Create a mix of unbilled and billed entries."""
    return [
        WipEntry(
            id=1, matter_id=1, fee_earner_id=1,
            worked_on=date.today() - timedelta(days=5),
            hours=Decimal("2"),
            hourly_rate=Money("3000", "NOK"),
            description="Recent work",
            status="unbilled",
        ),
        WipEntry(
            id=2, matter_id=1, fee_earner_id=1,
            worked_on=date.today() - timedelta(days=45),
            hours=Decimal("1.5"),
            hourly_rate=Money("3000", "NOK"),
            description="Month-old work",
            status="unbilled",
        ),
        WipEntry(
            id=3, matter_id=1, fee_earner_id=1,
            worked_on=date.today() - timedelta(days=100),
            hours=Decimal("4"),
            hourly_rate=Money("3500", "NOK"),
            description="Old work",
            status="unbilled",
        ),
        WipEntry(
            id=4, matter_id=1, fee_earner_id=1,
            worked_on=date.today() - timedelta(days=30),
            hours=Decimal("3"),
            hourly_rate=Money("3000", "NOK"),
            description="Already billed",
            status="billed",
        ),
    ]


def test_calculate_wip_sums_only_unbilled(sample_wip_entries):
    total = calculate_wip(sample_wip_entries)
    # 2*3000 + 1.5*3000 + 4*3500 = 6000 + 4500 + 14000 = 24500
    assert total == Money("24500.00", "NOK")


def test_calculate_wip_empty_list():
    assert calculate_wip([]) == Money.zero("NOK")


def test_calculate_wip_rejects_mixed_currency():
    entries = [
        WipEntry(
            id=1, matter_id=1, fee_earner_id=1,
            worked_on=date.today(), hours=Decimal("1"),
            hourly_rate=Money("3000", "NOK"),
            description="x", status="unbilled",
        ),
        WipEntry(
            id=2, matter_id=1, fee_earner_id=1,
            worked_on=date.today(), hours=Decimal("1"),
            hourly_rate=Money("300", "EUR"),
            description="y", status="unbilled",
        ),
    ]
    with pytest.raises(ValueError):
        calculate_wip(entries)


# ── WIP aging ─────────────────────────────────────────────────────────────


def test_age_wip_entries_bucketizes_correctly(sample_wip_entries):
    report = age_wip_entries(sample_wip_entries)
    assert report.currency == "NOK"
    assert len(report.buckets) == 5  # 0-30, 31-60, 61-90, 91-120, 120+

    # Recent work (5 days) → 0-30 bucket
    bucket_0_30 = next(b for b in report.buckets if b.label == "0-30")
    assert bucket_0_30.entry_count == 1
    assert bucket_0_30.total_value == Money("6000.00", "NOK")

    # Month-old work (45 days) → 31-60 bucket
    bucket_31_60 = next(b for b in report.buckets if b.label == "31-60")
    assert bucket_31_60.entry_count == 1
    assert bucket_31_60.total_value == Money("4500.00", "NOK")

    # Old work (100 days) → 91-120 bucket
    bucket_91_120 = next(b for b in report.buckets if b.label == "91-120")
    assert bucket_91_120.entry_count == 1
    assert bucket_91_120.total_value == Money("14000.00", "NOK")

    # 61-90 and 120+ are empty
    bucket_61_90 = next(b for b in report.buckets if b.label == "61-90")
    assert bucket_61_90.entry_count == 0


def test_age_wip_excludes_billed_entries(sample_wip_entries):
    report = age_wip_entries(sample_wip_entries)
    assert report.total_entries == 3  # 4 total, 1 billed → 3 unbilled


def test_age_wip_empty_entries_returns_empty_buckets():
    report = age_wip_entries([])
    assert report.total_entries == 0
    assert report.total_value == Money.zero("NOK")


def test_age_wip_total_value_matches_calculate_wip(sample_wip_entries):
    report = age_wip_entries(sample_wip_entries)
    total_from_aging = report.total_value
    total_from_wip = calculate_wip(sample_wip_entries)
    assert total_from_aging == total_from_wip


# ── Billing rate resolution ──────────────────────────────────────────────


@pytest.fixture
def sample_fee_earner():
    return FeeEarner(
        id=1,
        client_id=1,
        name="Anna Karlsson",
        email="anna@firm.se",
        grade="senior",
        default_hourly_rate=Money("3000", "SEK"),
    )


@pytest.fixture
def sample_matter():
    return Matter(
        id=10,
        client_id=1,
        code="ACME-2026-001",
        title="Acme acquisition",
        matter_type="corporate",
        status="open",
        opened_on=date(2026, 1, 1),
    )


def test_resolve_falls_back_to_fee_earner_default(sample_fee_earner, sample_matter):
    """Empty rate matrix — uses the fee earner's default rate."""
    rate = resolve_rate(
        rates=[],
        fee_earner=sample_fee_earner,
        matter=sample_matter,
    )
    assert rate == Money("3000.00", "SEK")


def test_resolve_matter_specific_wins(sample_fee_earner, sample_matter):
    """Matter-specific rate overrides everything else."""
    rates = [
        BillingRate(
            id=1,
            grade="senior",
            hourly_rate=Money("3500", "SEK"),
            effective_from=date(2026, 1, 1),
        ),
        BillingRate(
            id=2,
            matter_id=10,
            hourly_rate=Money("5000", "SEK"),
            effective_from=date(2026, 1, 1),
        ),
    ]
    rate = resolve_rate(
        rates=rates,
        fee_earner=sample_fee_earner,
        matter=sample_matter,
    )
    assert rate == Money("5000.00", "SEK")


def test_resolve_client_specific_beats_grade(sample_fee_earner, sample_matter):
    rates = [
        BillingRate(
            id=1,
            grade="senior",
            hourly_rate=Money("3500", "SEK"),
            effective_from=date(2026, 1, 1),
        ),
        BillingRate(
            id=2,
            client_id=1,
            grade="senior",
            hourly_rate=Money("4000", "SEK"),
            effective_from=date(2026, 1, 1),
        ),
    ]
    rate = resolve_rate(
        rates=rates,
        fee_earner=sample_fee_earner,
        matter=sample_matter,
    )
    assert rate == Money("4000.00", "SEK")


def test_resolve_matter_type_override(sample_fee_earner, sample_matter):
    rates = [
        BillingRate(
            id=1,
            grade="senior",
            hourly_rate=Money("3500", "SEK"),
            effective_from=date(2026, 1, 1),
        ),
        BillingRate(
            id=2,
            matter_type="corporate",
            grade="senior",
            hourly_rate=Money("4500", "SEK"),
            effective_from=date(2026, 1, 1),
        ),
    ]
    rate = resolve_rate(
        rates=rates,
        fee_earner=sample_fee_earner,
        matter=sample_matter,
    )
    assert rate == Money("4500.00", "SEK")


def test_resolve_most_recent_wins_at_same_specificity(sample_fee_earner, sample_matter):
    rates = [
        BillingRate(
            id=1,
            grade="senior",
            hourly_rate=Money("3000", "SEK"),
            effective_from=date(2025, 1, 1),
        ),
        BillingRate(
            id=2,
            grade="senior",
            hourly_rate=Money("3500", "SEK"),
            effective_from=date(2026, 1, 1),
        ),
    ]
    rate = resolve_rate(
        rates=rates,
        fee_earner=sample_fee_earner,
        matter=sample_matter,
    )
    assert rate == Money("3500.00", "SEK")


def test_resolve_expired_rates_ignored(sample_fee_earner, sample_matter):
    rates = [
        BillingRate(
            id=1,
            grade="senior",
            hourly_rate=Money("9999", "SEK"),
            effective_from=date(2025, 1, 1),
            effective_to=date(2025, 12, 31),
        ),
    ]
    # Expired rate should be skipped; fall back to fee earner default
    rate = resolve_rate(
        rates=rates,
        fee_earner=sample_fee_earner,
        matter=sample_matter,
    )
    assert rate == Money("3000.00", "SEK")


def test_resolve_raises_when_no_fallback():
    """Zero-rate fee earner + empty matrix = cannot resolve."""
    fe = FeeEarner(
        id=1,
        client_id=1,
        name="Broken",
        email="x@x",
        grade="senior",
        default_hourly_rate=Money.zero("SEK"),
    )
    matter = Matter(
        id=1,
        client_id=1,
        code="X-1",
        title="X",
        matter_type="corporate",
        status="open",
        opened_on=date(2026, 1, 1),
    )
    with pytest.raises(RateResolutionError):
        resolve_rate(rates=[], fee_earner=fe, matter=matter)


def test_matrix_helper_delegates_to_resolve_rate(sample_fee_earner, sample_matter):
    matrix = BillingRateMatrix(rates=[])
    assert matrix.resolve(sample_fee_earner, sample_matter) == Money("3000.00", "SEK")
