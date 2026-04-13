"""
Hospitality vertical module.

Extends the core platform with hotel/venue-specific data models and
operations: properties, room categories, outlets (restaurant/bar/spa),
daily revenue imports from PMS systems, and KPI calculations (RevPAR,
ADR, occupancy).

Nordic compliance built in:
  Norway:  accommodation 12% VAT, F&B 25%, alcohol separate
  Sweden:  accommodation 12%, restaurant 12% (from 2024), alcohol 25%
  Finland: accommodation 14%, restaurant 14%, alcohol 25.5%

Core use case:
  1. PMS adapter imports daily_revenue_import rows from Mews/Opera/etc.
  2. Revenue splitter allocates each day's total across outlet types
     (rooms, F&B, beverages) using the configured ratios
  3. Auto-journal creates accounting entries with the correct VAT code
     per outlet, per country
  4. KPI calculator exposes RevPAR, ADR, occupancy for dashboards
"""
from .models import (
    Property,
    RoomCategory,
    Outlet,
    DailyRevenueImport,
    RevenueLineItem,
    OutletType,
)
from .kpi import (
    calculate_revpar,
    calculate_adr,
    calculate_occupancy,
    RoomStats,
)
from .pms_adapter import (
    PMSAdapter,
    MockPMSAdapter,
    DailyRevenue,
    get_pms_adapter,
)
from .vat_split import split_revenue_by_country, VatSplitResult

__all__ = [
    "Property",
    "RoomCategory",
    "Outlet",
    "DailyRevenueImport",
    "RevenueLineItem",
    "OutletType",
    "calculate_revpar",
    "calculate_adr",
    "calculate_occupancy",
    "RoomStats",
    "PMSAdapter",
    "MockPMSAdapter",
    "DailyRevenue",
    "get_pms_adapter",
    "split_revenue_by_country",
    "VatSplitResult",
]
