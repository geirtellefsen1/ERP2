"""
Hospitality KPI calculations — RevPAR, ADR, occupancy.

These are the three headline metrics every hotel operator watches every
day. All are pure functions — no DB, no network.

RevPAR = Revenue Per Available Room
       = Total room revenue / rooms available (not rooms sold)
       = ADR × Occupancy
ADR    = Average Daily Rate
       = Total room revenue / rooms sold
Occupancy = rooms sold / rooms available
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.services.money import Money


@dataclass
class RoomStats:
    """Aggregated rooms-division stats for a period."""
    room_revenue: Money
    rooms_sold: int
    rooms_available: int

    @property
    def revpar(self) -> Money:
        return calculate_revpar(self)

    @property
    def adr(self) -> Money | None:
        return calculate_adr(self)

    @property
    def occupancy(self) -> Decimal:
        return calculate_occupancy(self)


def calculate_revpar(stats: RoomStats) -> Money:
    """
    Revenue per available room.
    Returns zero Money if rooms_available is 0 (rather than raising)
    so dashboards don't crash on empty periods.
    """
    if stats.rooms_available <= 0:
        return Money.zero(stats.room_revenue.currency)
    return Money(
        stats.room_revenue.amount / Decimal(stats.rooms_available),
        stats.room_revenue.currency,
    )


def calculate_adr(stats: RoomStats) -> Money | None:
    """
    Average daily rate.
    Returns None if rooms_sold is 0 — ADR is undefined, not zero, when
    no rooms were sold. Callers should display "—" in that case.
    """
    if stats.rooms_sold <= 0:
        return None
    return Money(
        stats.room_revenue.amount / Decimal(stats.rooms_sold),
        stats.room_revenue.currency,
    )


def calculate_occupancy(stats: RoomStats) -> Decimal:
    """
    Occupancy as a decimal fraction (0.0–1.0). Dashboard code multiplies
    by 100 for percentage display.
    Returns 0 for zero-capacity periods (rather than raising) so
    seasonal closures don't break reports.
    """
    if stats.rooms_available <= 0:
        return Decimal("0")
    return Decimal(stats.rooms_sold) / Decimal(stats.rooms_available)
