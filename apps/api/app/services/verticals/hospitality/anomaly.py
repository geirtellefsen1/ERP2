"""Hospitality anomaly detector.

Pure-Python rules that flag unusual movements in revenue/cost ratios.
Used by the AI activity feed on the hospitality dashboard.

This is intentionally simple — no ML, just thresholds. The point is to
demonstrate value in the demo without needing model training data.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from sqlalchemy.orm import Session

from app.models import DailyRevenueImport, DailyRevenueLine
from sqlalchemy import func


Severity = Literal["info", "warning", "critical"]


@dataclass
class Alert:
    severity: Severity
    title: str
    detail: str
    metric: str
    current_value: float
    baseline_value: float
    delta_pct: float


# --- Thresholds --------------------------------------------------------------


VARIANCE_WARN_PCT = 15.0       # >15% deviation from baseline = warning
VARIANCE_CRITICAL_PCT = 25.0   # >25% deviation = critical


# --- Helpers -----------------------------------------------------------------


def _outlet_revenue_for_window(
    db: Session, property_id: int, outlet_type: str, days: int, end_date: date
) -> int:
    """Sum gross revenue for an outlet type over the trailing N days
    ending on end_date (inclusive). Returns minor units."""
    start = end_date.fromordinal(end_date.toordinal() - days + 1)
    result = (
        db.query(func.coalesce(func.sum(DailyRevenueLine.gross_amount_minor), 0))
        .join(
            DailyRevenueImport,
            DailyRevenueImport.id == DailyRevenueLine.import_id,
        )
        .filter(
            DailyRevenueImport.property_id == property_id,
            DailyRevenueLine.outlet_type == outlet_type,
            func.date(DailyRevenueImport.import_date) >= start,
            func.date(DailyRevenueImport.import_date) <= end_date,
        )
        .scalar()
    )
    return int(result or 0)


def _occupancy_for_window(
    db: Session, property_id: int, days: int, end_date: date
) -> float:
    """Average occupancy % for the window."""
    start = end_date.fromordinal(end_date.toordinal() - days + 1)
    rows = (
        db.query(DailyRevenueImport.rooms_sold, DailyRevenueImport.rooms_available)
        .filter(
            DailyRevenueImport.property_id == property_id,
            func.date(DailyRevenueImport.import_date) >= start,
            func.date(DailyRevenueImport.import_date) <= end_date,
        )
        .all()
    )
    if not rows:
        return 0.0
    total_sold = sum(r[0] for r in rows)
    total_avail = sum(r[1] for r in rows)
    return (total_sold / total_avail) * 100 if total_avail > 0 else 0.0


def _classify(delta_pct: float) -> Severity:
    abs_delta = abs(delta_pct)
    if abs_delta >= VARIANCE_CRITICAL_PCT:
        return "critical"
    if abs_delta >= VARIANCE_WARN_PCT:
        return "warning"
    return "info"


# --- Rules -------------------------------------------------------------------


def _check_beverage_ratio(
    db: Session, property_id: int, end_date: date
) -> list[Alert]:
    """Flag if beverage-to-food ratio diverges from the 30-day baseline.

    A sudden ratio shift is a classic pour-cost-leak signal.
    """
    food_7d = _outlet_revenue_for_window(db, property_id, "food", 7, end_date)
    bev_7d = _outlet_revenue_for_window(
        db, property_id, "beverage_alcohol", 7, end_date
    )
    food_30d = _outlet_revenue_for_window(db, property_id, "food", 30, end_date)
    bev_30d = _outlet_revenue_for_window(
        db, property_id, "beverage_alcohol", 30, end_date
    )

    if food_7d == 0 or food_30d == 0:
        return []

    ratio_7d = (bev_7d / food_7d) * 100
    ratio_30d = (bev_30d / food_30d) * 100
    if ratio_30d == 0:
        return []
    delta = ((ratio_7d - ratio_30d) / ratio_30d) * 100

    if abs(delta) < VARIANCE_WARN_PCT:
        return []

    direction = "rose" if delta > 0 else "fell"
    return [
        Alert(
            severity=_classify(delta),
            title=f"Bar-to-food ratio {direction} {abs(delta):.0f}%",
            detail=(
                f"Last 7 days: bar revenue = {ratio_7d:.0f}% of food. "
                f"30-day average: {ratio_30d:.0f}%. "
                "Could indicate a pour-cost leak, a promo running, or a "
                "data import gap — investigate."
            ),
            metric="bar_to_food_ratio",
            current_value=round(ratio_7d, 1),
            baseline_value=round(ratio_30d, 1),
            delta_pct=round(delta, 1),
        )
    ]


def _check_occupancy_drop(
    db: Session, property_id: int, end_date: date
) -> list[Alert]:
    """Flag if 7-day occupancy is well below the 30-day baseline."""
    occ_7d = _occupancy_for_window(db, property_id, 7, end_date)
    occ_30d = _occupancy_for_window(db, property_id, 30, end_date)
    if occ_30d == 0:
        return []
    delta = ((occ_7d - occ_30d) / occ_30d) * 100
    if delta > -VARIANCE_WARN_PCT:    # only flag drops, not gains
        return []

    return [
        Alert(
            severity=_classify(delta),
            title=f"Occupancy down {abs(delta):.0f}%",
            detail=(
                f"Last 7 days averaged {occ_7d:.0f}% occupancy vs 30-day "
                f"average of {occ_30d:.0f}%. Check for cancellations, OTA "
                "ranking issues, or local event calendar gaps."
            ),
            metric="occupancy_pct",
            current_value=round(occ_7d, 1),
            baseline_value=round(occ_30d, 1),
            delta_pct=round(delta, 1),
        )
    ]


def detect_alerts(
    db: Session, property_id: int, end_date: date | None = None
) -> list[Alert]:
    """Run every rule and return all alerts for a property."""
    if end_date is None:
        end_date = date.today()
    alerts: list[Alert] = []
    alerts.extend(_check_beverage_ratio(db, property_id, end_date))
    alerts.extend(_check_occupancy_drop(db, property_id, end_date))
    # Sort: critical first, then warning, then info
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: severity_order[a.severity])
    return alerts
