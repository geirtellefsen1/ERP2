"""
Work In Progress (WIP) calculations and aging.

"WIP" is unbilled time — the hours logged against matters that have
not yet been converted into an invoice. Professional services firms
watch WIP closely because aged unbilled time is a leading indicator of
collection problems.

Aging buckets (in days since logged_at):
  0-30 days
  31-60 days
  61-90 days
  91-120 days
  120+ days
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from app.services.money import Money

from .models import WipEntry


# ── Aging buckets ─────────────────────────────────────────────────────────


AGING_BUCKETS: list[tuple[str, int, Optional[int]]] = [
    ("0-30", 0, 30),
    ("31-60", 31, 60),
    ("61-90", 61, 90),
    ("91-120", 91, 120),
    ("120+", 121, None),
]


@dataclass
class WipAgingBucket:
    label: str                   # "0-30", "31-60", etc.
    days_from: int
    days_to: Optional[int]       # None for the open-ended 120+ bucket
    entry_count: int
    total_hours: Decimal
    total_value: Money


@dataclass
class WipAgingReport:
    currency: str
    as_of: date
    buckets: list[WipAgingBucket]

    @property
    def total_entries(self) -> int:
        return sum(b.entry_count for b in self.buckets)

    @property
    def total_hours(self) -> Decimal:
        return sum((b.total_hours for b in self.buckets), start=Decimal("0"))

    @property
    def total_value(self) -> Money:
        if not self.buckets:
            return Money.zero(self.currency)
        total = Money.zero(self.currency)
        for b in self.buckets:
            total = total + b.total_value
        return total


# ── Core calculations ─────────────────────────────────────────────────────


def calculate_wip(entries: list[WipEntry]) -> Money:
    """
    Return the total value of unbilled WIP entries.
    Raises if entries span multiple currencies — WIP reports are always
    single-currency per client.
    """
    unbilled = [e for e in entries if e.status == "unbilled"]
    if not unbilled:
        return Money.zero("NOK")
    currency = unbilled[0].hourly_rate.currency
    total = Money.zero(currency)
    for e in unbilled:
        if e.hourly_rate.currency != currency:
            raise ValueError(
                f"WIP entries must share a currency. Got {currency} and "
                f"{e.hourly_rate.currency}"
            )
        total = total + e.value
    return total


def age_wip_entries(
    entries: list[WipEntry],
    as_of: Optional[date] = None,
) -> WipAgingReport:
    """
    Bucket unbilled WIP entries by age in days as of the given date.
    Only considers entries with status="unbilled".
    """
    cutoff = as_of or date.today()
    unbilled = [e for e in entries if e.status == "unbilled"]

    if not unbilled:
        return WipAgingReport(
            currency="NOK",
            as_of=cutoff,
            buckets=[
                WipAgingBucket(
                    label=label,
                    days_from=from_d,
                    days_to=to_d,
                    entry_count=0,
                    total_hours=Decimal("0"),
                    total_value=Money.zero("NOK"),
                )
                for label, from_d, to_d in AGING_BUCKETS
            ],
        )

    currency = unbilled[0].hourly_rate.currency
    for e in unbilled:
        if e.hourly_rate.currency != currency:
            raise ValueError(
                f"WIP entries must share a currency. Got {currency} and "
                f"{e.hourly_rate.currency}"
            )

    buckets: list[WipAgingBucket] = []
    for label, from_d, to_d in AGING_BUCKETS:
        in_bucket = [
            e for e in unbilled
            if _is_in_bucket(e, cutoff, from_d, to_d)
        ]
        total_hours = sum(
            (e.hours for e in in_bucket),
            start=Decimal("0"),
        )
        total_value = Money.zero(currency)
        for e in in_bucket:
            total_value = total_value + e.value
        buckets.append(
            WipAgingBucket(
                label=label,
                days_from=from_d,
                days_to=to_d,
                entry_count=len(in_bucket),
                total_hours=total_hours,
                total_value=total_value,
            )
        )

    return WipAgingReport(
        currency=currency,
        as_of=cutoff,
        buckets=buckets,
    )


def _is_in_bucket(
    entry: WipEntry,
    cutoff: date,
    from_d: int,
    to_d: Optional[int],
) -> bool:
    age = (cutoff - entry.worked_on).days
    if age < from_d:
        return False
    if to_d is not None and age > to_d:
        return False
    return True
