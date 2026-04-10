from decimal import Decimal, ROUND_HALF_UP
from datetime import time, date, timedelta
from typing import List


def calculate_units(start_time: time, end_time: time) -> Decimal:
    """Convert time range to 0.1-hour units (6-min increments).

    Each unit is 6 minutes (0.1 hour).
    E.g., 30 mins = 5.0 units, 18 mins = 3.0 units, 6 mins = 1.0 unit.
    Rounds to nearest 6-minute block.
    """
    start_minutes = start_time.hour * 60 + start_time.minute
    end_minutes = end_time.hour * 60 + end_time.minute
    total_minutes = end_minutes - start_minutes

    if total_minutes <= 0:
        return Decimal("0")

    # Round to nearest 6-minute block
    blocks = Decimal(str(total_minutes)) / Decimal("6")
    rounded_blocks = blocks.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    return rounded_blocks


def calculate_wip(matter_id: int, hourly_rate: Decimal, units: Decimal) -> Decimal:
    """Calculate WIP value from units and hourly rate.

    units * (hourly_rate / 10) since each unit is 0.1 hour.
    """
    rate_per_unit = Decimal(str(hourly_rate)) / Decimal("10")
    return (Decimal(str(units)) * rate_per_unit).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_wip_aging(wip_entries: list, today: date) -> dict:
    """Bucket WIP entries into aging categories based on period_end date.

    Returns dict with keys: 0_30, 31_60, 61_90, over_90
    Each value is the total wip_value for that bucket.
    """
    buckets = {
        "0_30": Decimal("0"),
        "31_60": Decimal("0"),
        "61_90": Decimal("0"),
        "over_90": Decimal("0"),
    }

    for entry in wip_entries:
        period_end = entry.period_end if isinstance(entry.period_end, date) else entry.period_end
        days_old = (today - period_end).days

        wip_value = Decimal(str(entry.wip_value)) if entry.wip_value else Decimal("0")

        if days_old <= 30:
            buckets["0_30"] += wip_value
        elif days_old <= 60:
            buckets["31_60"] += wip_value
        elif days_old <= 90:
            buckets["61_90"] += wip_value
        else:
            buckets["over_90"] += wip_value

    return buckets


def calculate_utilisation(total_units: Decimal, billable_units: Decimal) -> Decimal:
    """Calculate utilisation percentage.

    (billable / total * 100)
    """
    if not total_units or Decimal(str(total_units)) == 0:
        return Decimal("0")

    total = Decimal(str(total_units))
    billable = Decimal(str(billable_units))

    return (billable / total * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
