"""
6-minute increment time tracking.

Every professional services firm bills in units of 0.1 hours (6 minutes).
This module validates that raw hour inputs round to that grid, reject
obviously-wrong entries (zero hours, >24 hours in a day, negative), and
produces WipEntry objects ready for the WIP aging pipeline.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from app.services.money import Money

from .models import WipEntry


MINIMUM_INCREMENT = Decimal("0.1")   # 6 minutes
MAX_HOURS_PER_ENTRY = Decimal("24")


class TimeEntryError(ValueError):
    """Raised when a time entry fails validation."""


def validate_time_entry(
    hours: Decimal,
    worked_on: date,
    description: str,
) -> None:
    """Raise TimeEntryError if the input is invalid."""
    if hours <= Decimal("0"):
        raise TimeEntryError(f"Hours must be positive, got {hours}")
    if hours > MAX_HOURS_PER_ENTRY:
        raise TimeEntryError(
            f"Hours cannot exceed {MAX_HOURS_PER_ENTRY} in a single entry, "
            f"got {hours}. Split into multiple entries if work spans days."
        )
    # Check the value is a clean multiple of 0.1
    remainder = (hours / MINIMUM_INCREMENT) % Decimal("1")
    if remainder != Decimal("0"):
        raise TimeEntryError(
            f"Hours must be in 6-minute increments (0.1), got {hours}. "
            f"Round to the nearest 0.1."
        )
    if worked_on > date.today():
        raise TimeEntryError(
            f"Cannot log time for a future date ({worked_on})"
        )
    if not description or not description.strip():
        raise TimeEntryError(
            "Description is required — professional conduct rules in all "
            "three Nordic jurisdictions require a narrative per entry."
        )


def log_time(
    *,
    wip_id: int,
    matter_id: int,
    fee_earner_id: int,
    worked_on: date,
    hours: Decimal,
    hourly_rate: Money,
    description: str,
) -> WipEntry:
    """
    Validate and build a WipEntry. Does NOT persist — the caller is
    responsible for passing the entry to the repository layer.
    """
    validate_time_entry(hours, worked_on, description)
    return WipEntry(
        id=wip_id,
        matter_id=matter_id,
        fee_earner_id=fee_earner_id,
        worked_on=worked_on,
        hours=hours,
        hourly_rate=hourly_rate,
        description=description.strip(),
        status="unbilled",
        logged_at=datetime.now(),
    )
