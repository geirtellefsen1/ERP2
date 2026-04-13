"""
Pure cashflow calculation. No AI, no DB, no network.

The forecaster takes an opening balance and a list of expected cashflow
events with dates and rolls them up into 13 weekly buckets, calculating
opening/closing balances and flagging weeks that breach the alert
threshold.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from app.services.money import Money

from .models import (
    CashflowItem,
    ForecastInput,
    ForecastResult,
    ForecastWeek,
)


def _week_start(d: date) -> date:
    """Return the Monday of the week containing `d` (ISO weekday)."""
    return d - timedelta(days=d.weekday())


def forecast(input: ForecastInput) -> ForecastResult:
    """
    Build a 13-week (or N-week) forecast from the input items.

    The week buckets are anchored to the Monday of the week containing
    forecast_start. Items dated before the start fall into the first
    bucket; items dated after the end fall into the last bucket.
    """
    if input.weeks < 1:
        raise ValueError("weeks must be >= 1")
    if input.weeks > 52:
        raise ValueError("weeks must be <= 52 (this is a rolling forecast, not annual)")

    currency = input.opening_balance.currency

    # Validate every item is in the same currency as the opening balance
    for item in input.items:
        if item.amount.currency != currency:
            raise ValueError(
                f"Item currency {item.amount.currency} does not match opening "
                f"balance currency {currency}"
            )
    if input.threshold and input.threshold.currency != currency:
        raise ValueError(
            f"Threshold currency {input.threshold.currency} does not match "
            f"opening balance currency {currency}"
        )

    # Build week buckets anchored to Monday
    start_monday = _week_start(input.forecast_start)
    week_buckets: list[ForecastWeek] = []
    for i in range(input.weeks):
        week_start = start_monday + timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        week_buckets.append(
            ForecastWeek(
                week_index=i,
                week_start=week_start,
                week_end=week_end,
                opening_balance=Money.zero(currency),
                inflows=Money.zero(currency),
                outflows=Money.zero(currency),
                closing_balance=Money.zero(currency),
            )
        )

    forecast_end = week_buckets[-1].week_end

    # Drop items into buckets, applying confidence discount
    for item in input.items:
        idx = _bucket_index(item.expected_date, start_monday, input.weeks)
        bucket = week_buckets[idx]
        discounted = item.amount * Decimal(str(item.confidence))
        if item.direction == "inflow":
            bucket.inflows = bucket.inflows + discounted
        else:
            bucket.outflows = bucket.outflows + discounted
        bucket.item_count += 1

    # Roll forward the running balance
    running = input.opening_balance
    breach_weeks: list[int] = []
    for week in week_buckets:
        week.opening_balance = running
        week.closing_balance = running + week.inflows - week.outflows
        if input.threshold and week.closing_balance < input.threshold:
            week.below_threshold = True
            breach_weeks.append(week.week_index)
        running = week.closing_balance

    return ForecastResult(
        currency=currency,
        forecast_start=input.forecast_start,
        forecast_end=forecast_end,
        opening_balance=input.opening_balance,
        weeks=week_buckets,
        threshold=input.threshold,
        breach_weeks=breach_weeks,
    )


def _bucket_index(item_date: date, start_monday: date, weeks: int) -> int:
    """Map an item date to a bucket index, clamping to first/last."""
    days = (item_date - start_monday).days
    idx = days // 7
    if idx < 0:
        return 0
    if idx >= weeks:
        return weeks - 1
    return idx
