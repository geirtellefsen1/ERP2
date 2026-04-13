"""
13-week rolling cashflow forecaster.

Produces a week-by-week projection of bank balance from:
  - opening balance
  - expected AR collections (open invoices + estimated DSO)
  - expected AP payments (open purchase invoices + payment terms)
  - scheduled payroll runs
  - known one-off future items
  - historical seasonality (optional adjustment)

Per-week output:
  week_start, week_end, opening_balance, inflows, outflows, closing_balance,
  below_threshold_flag

Plus a Claude-generated narrative explaining the forecast in plain
business language, in the client's preferred language.

Usage:
    from app.services.cashflow import forecast, ForecastInput

    result = forecast(
        ForecastInput(
            opening_balance=Money("250000", "NOK"),
            forecast_start=date(2026, 4, 14),
            ar_items=[...],
            ap_items=[...],
            payroll_schedule=[...],
            threshold=Money("50000", "NOK"),
        )
    )
"""
from .models import (
    ForecastInput,
    ForecastResult,
    ForecastWeek,
    CashflowItem,
    CashflowDirection,
)
from .forecaster import forecast
from .narrator import generate_narrative

__all__ = [
    "ForecastInput",
    "ForecastResult",
    "ForecastWeek",
    "CashflowItem",
    "CashflowDirection",
    "forecast",
    "generate_narrative",
]
