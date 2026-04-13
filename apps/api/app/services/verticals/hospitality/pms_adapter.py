"""
PMS (Property Management System) adapter interface.

Production will have MewsAdapter, OperaCloudAdapter, ApaleoAdapter, etc.
— each talks to a different hotel PMS REST API and produces a common
DailyRevenue result. For Tier 4 we ship the interface and a
MockPMSAdapter so the rest of the pipeline can be tested end-to-end.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from app.services.money import Money

from .models import RevenueLineItem, OutletType


@dataclass
class DailyRevenue:
    """Output of a PMS import for a single day at a single property."""
    property_id: int
    date: date
    rooms_sold: int
    rooms_available: int
    line_items: list[RevenueLineItem] = field(default_factory=list)
    pms_name: str = ""
    raw_reference: str = ""  # PMS-side ID for reconciliation


class PMSAdapter(ABC):
    """Every PMS adapter implements this."""

    pms_name: str

    @abstractmethod
    def fetch_daily_revenue(
        self,
        property_id: int,
        day: date,
    ) -> DailyRevenue: ...


class MockPMSAdapter(PMSAdapter):
    """
    Deterministic PMS adapter for tests and dev.

    Returns a fixed split: 60% rooms, 25% food, 10% alcoholic beverages,
    5% spa. Configurable via constructor for tests that need different
    shapes.
    """

    pms_name = "mock"

    def __init__(
        self,
        currency: str = "NOK",
        daily_total: Money | None = None,
        rooms_sold: int = 45,
        rooms_available: int = 60,
        split: dict[OutletType, float] | None = None,
    ):
        self.currency = currency
        self.daily_total = daily_total or Money("120000", currency)
        self.rooms_sold = rooms_sold
        self.rooms_available = rooms_available
        self.split: dict[OutletType, float] = split or {
            "rooms": 0.60,
            "food": 0.25,
            "beverage_alcohol": 0.10,
            "spa": 0.05,
        }
        total = sum(self.split.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f"Split must sum to 1.0, got {total}. "
                f"Shares: {self.split}"
            )

    def fetch_daily_revenue(
        self,
        property_id: int,
        day: date,
    ) -> DailyRevenue:
        line_items: list[RevenueLineItem] = []
        for outlet_type, share in self.split.items():
            portion = self.daily_total * share
            cover_count = 0
            if outlet_type in ("food", "beverage_soft", "beverage_alcohol"):
                # Rough guess: NOK 750 per cover
                if portion.amount > 0:
                    cover_count = int(portion.amount / 750)
            line_items.append(
                RevenueLineItem(
                    outlet_type=outlet_type,
                    amount=portion,
                    cover_count=cover_count,
                )
            )
        return DailyRevenue(
            property_id=property_id,
            date=day,
            rooms_sold=self.rooms_sold,
            rooms_available=self.rooms_available,
            line_items=line_items,
            pms_name=self.pms_name,
            raw_reference=f"mock-{property_id}-{day.isoformat()}",
        )


_REGISTRY: dict[str, type[PMSAdapter]] = {
    "mock": MockPMSAdapter,
    # "mews": MewsAdapter,       # Tier 5
    # "opera": OperaCloudAdapter, # Tier 5
}


def get_pms_adapter(pms_name: str = "mock") -> PMSAdapter:
    if pms_name not in _REGISTRY:
        raise ValueError(
            f"Unknown PMS: {pms_name}. Supported: {sorted(_REGISTRY.keys())}"
        )
    return _REGISTRY[pms_name]()
