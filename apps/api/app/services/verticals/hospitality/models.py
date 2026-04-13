"""Hospitality data classes — value objects, not SQLAlchemy models."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Literal

from app.services.money import Money


OutletType = Literal[
    "rooms",           # accommodation revenue (room nights)
    "food",            # restaurant food
    "beverage_soft",   # non-alcoholic beverages
    "beverage_alcohol", # alcoholic beverages (separate VAT code)
    "spa",
    "conference",
    "retail",
    "other",
]


@dataclass
class Property:
    """A hotel, guesthouse, or venue."""
    id: int
    client_id: int
    name: str
    country: str                   # NO/SE/FI
    total_rooms: int               # capacity for occupancy calcs
    opening_date: date | None = None
    timezone: str = "Europe/Oslo"


@dataclass
class RoomCategory:
    """A room type with its own rate (standard, deluxe, suite, etc.)."""
    id: int
    property_id: int
    code: str                      # "STD", "DLX", "SUITE"
    label: str
    room_count: int                # number of rooms in this category
    base_rate: Money               # published rate per night, ex-VAT


@dataclass
class Outlet:
    """A revenue center at a property (restaurant, bar, spa, etc.)."""
    id: int
    property_id: int
    name: str
    outlet_type: OutletType


@dataclass
class DailyRevenueImport:
    """One day's revenue figures from the PMS, pre-split per outlet."""
    property_id: int
    date: date
    rooms_sold: int                # rooms occupied that night
    rooms_available: int           # capacity that night (for occupancy %)
    line_items: list[RevenueLineItem] = field(default_factory=list)

    @property
    def total_revenue(self) -> Money:
        if not self.line_items:
            raise ValueError("No line items on this import")
        total = Money.zero(self.line_items[0].amount.currency)
        for item in self.line_items:
            total = total + item.amount
        return total


@dataclass
class RevenueLineItem:
    """One outlet's revenue for one day."""
    outlet_type: OutletType
    amount: Money                  # gross of VAT
    cover_count: int = 0           # F&B covers (pax), 0 for rooms
