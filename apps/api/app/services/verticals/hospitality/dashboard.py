"""Hospitality dashboard service.

Aggregates today's snapshot KPIs + 30-day trend + alerts for a single
property. Calls into the existing kpi.py and vat_split.py modules and
adds the SQL queries that load actual DailyRevenueImport rows.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models import (
    DailyRevenueImport,
    DailyRevenueLine,
    Outlet,
    Property,
    RoomCategory,
)
from app.services.money import Money


# --- Result shapes -----------------------------------------------------------


@dataclass
class DaySnapshot:
    snapshot_date: date
    rooms_sold: int
    rooms_available: int
    occupancy_pct: float          # 0-100
    adr_minor: Optional[int]      # average daily rate in minor units, None if no rooms sold
    revpar_minor: int             # revenue per available room, minor units
    food_revenue_minor: int
    beverage_revenue_minor: int
    food_covers: int
    rooms_revenue_minor: int
    total_revenue_minor: int
    currency: str


@dataclass
class TrendPoint:
    point_date: date
    occupancy_pct: float
    revpar_minor: int
    total_revenue_minor: int


@dataclass
class DashboardPayload:
    property_id: int
    property_name: str
    country: str
    currency: str
    today: Optional[DaySnapshot]
    yesterday: Optional[DaySnapshot]
    trend_30d: list[TrendPoint] = field(default_factory=list)


# --- Queries -----------------------------------------------------------------


def _load_day(
    db: Session, property_id: int, target_date: date, currency: str
) -> Optional[DaySnapshot]:
    """Load one day's import + lines and convert to a DaySnapshot.

    Returns None if the property has no import for that date.
    """
    imp = (
        db.query(DailyRevenueImport)
        .filter(
            DailyRevenueImport.property_id == property_id,
            func.date(DailyRevenueImport.import_date) == target_date,
        )
        .first()
    )
    if imp is None:
        return None

    lines = (
        db.query(DailyRevenueLine)
        .filter(DailyRevenueLine.import_id == imp.id)
        .all()
    )

    rooms_revenue = 0
    food_revenue = 0
    beverage_revenue = 0
    food_covers = 0
    for ln in lines:
        if ln.outlet_type == "rooms":
            rooms_revenue += ln.gross_amount_minor
        elif ln.outlet_type == "food":
            food_revenue += ln.gross_amount_minor
            food_covers += ln.cover_count or 0
        elif ln.outlet_type in ("beverage_alcohol", "beverage_soft"):
            beverage_revenue += ln.gross_amount_minor

    total = rooms_revenue + food_revenue + beverage_revenue

    occupancy = (
        (imp.rooms_sold / imp.rooms_available) * 100
        if imp.rooms_available > 0
        else 0.0
    )
    adr = (
        rooms_revenue // imp.rooms_sold
        if imp.rooms_sold > 0
        else None
    )
    revpar = (
        rooms_revenue // imp.rooms_available
        if imp.rooms_available > 0
        else 0
    )

    return DaySnapshot(
        snapshot_date=target_date,
        rooms_sold=imp.rooms_sold,
        rooms_available=imp.rooms_available,
        occupancy_pct=round(occupancy, 1),
        adr_minor=adr,
        revpar_minor=revpar,
        food_revenue_minor=food_revenue,
        beverage_revenue_minor=beverage_revenue,
        food_covers=food_covers,
        rooms_revenue_minor=rooms_revenue,
        total_revenue_minor=total,
        currency=currency,
    )


def _load_trend(
    db: Session, property_id: int, days: int, currency: str
) -> list[TrendPoint]:
    """Load N days of imports as a sparse trend (only days with data)."""
    cutoff = date.today() - timedelta(days=days)
    imports = (
        db.query(DailyRevenueImport)
        .filter(
            DailyRevenueImport.property_id == property_id,
            func.date(DailyRevenueImport.import_date) >= cutoff,
        )
        .order_by(DailyRevenueImport.import_date.asc())
        .all()
    )

    points: list[TrendPoint] = []
    for imp in imports:
        lines = (
            db.query(DailyRevenueLine)
            .filter(DailyRevenueLine.import_id == imp.id)
            .all()
        )
        rooms_rev = sum(
            ln.gross_amount_minor for ln in lines if ln.outlet_type == "rooms"
        )
        total = sum(ln.gross_amount_minor for ln in lines)
        occupancy = (
            (imp.rooms_sold / imp.rooms_available) * 100
            if imp.rooms_available > 0
            else 0.0
        )
        revpar = (
            rooms_rev // imp.rooms_available
            if imp.rooms_available > 0
            else 0
        )
        points.append(
            TrendPoint(
                point_date=imp.import_date.date()
                if hasattr(imp.import_date, "date")
                else imp.import_date,
                occupancy_pct=round(occupancy, 1),
                revpar_minor=revpar,
                total_revenue_minor=total,
            )
        )
    return points


def get_dashboard(db: Session, property_id: int) -> DashboardPayload:
    """Build the full dashboard payload for one property."""
    prop = db.query(Property).filter(Property.id == property_id).first()
    if prop is None:
        raise ValueError(f"Property {property_id} not found")

    cat = (
        db.query(RoomCategory)
        .filter(RoomCategory.property_id == property_id)
        .first()
    )
    currency = cat.currency if cat else "NOK"

    today = date.today()
    yesterday = today - timedelta(days=1)

    return DashboardPayload(
        property_id=prop.id,
        property_name=prop.name,
        country=prop.country,
        currency=currency,
        today=_load_day(db, property_id, today, currency),
        yesterday=_load_day(db, property_id, yesterday, currency),
        trend_30d=_load_trend(db, property_id, 30, currency),
    )
