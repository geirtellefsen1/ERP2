"""
Billing rate resolution.

Resolves the correct hourly rate for a time entry by walking the
billing rate matrix in order of specificity:

  1. Matter-specific override (most specific — always wins)
  2. Client-specific override for this matter's client
  3. Matter-type override (e.g. all litigation matters)
  4. Grade-based default (e.g. all partners)
  5. Fee earner default (least specific — from FeeEarner record)

Multiple matching rates at the same specificity level are resolved by
effective_from (most recent wins). Rates with effective_to < today are
ignored.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from app.services.money import Money

from .models import BillingRate, FeeEarner, Grade, Matter, MatterType


class RateResolutionError(Exception):
    """Raised when no applicable rate can be found."""


@dataclass
class BillingRateMatrix:
    """An in-memory index of billing rates for efficient resolution."""
    rates: list[BillingRate]

    def resolve(
        self,
        fee_earner: FeeEarner,
        matter: Matter,
        on_date: Optional[date] = None,
    ) -> Money:
        return resolve_rate(
            rates=self.rates,
            fee_earner=fee_earner,
            matter=matter,
            on_date=on_date,
        )


def resolve_rate(
    *,
    rates: list[BillingRate],
    fee_earner: FeeEarner,
    matter: Matter,
    on_date: Optional[date] = None,
) -> Money:
    """
    Walk the rate matrix from most to least specific and return the first
    matching rate. Falls back to FeeEarner.default_hourly_rate if nothing
    in the matrix applies.
    """
    target_date = on_date or date.today()

    active = [
        r for r in rates
        if r.effective_from <= target_date
        and (r.effective_to is None or r.effective_to >= target_date)
    ]

    # 1. Matter-specific
    matter_specific = [
        r for r in active
        if r.matter_id == matter.id
    ]
    if matter_specific:
        return _most_recent(matter_specific).hourly_rate

    # 2. Client-specific (any matter for this client)
    client_specific = [
        r for r in active
        if r.client_id == matter.client_id
        and r.matter_id is None
        and (r.grade is None or r.grade == fee_earner.grade)
    ]
    if client_specific:
        return _most_recent(client_specific).hourly_rate

    # 3. Matter-type override
    matter_type_specific = [
        r for r in active
        if r.matter_type == matter.matter_type
        and r.client_id is None
        and r.matter_id is None
        and (r.grade is None or r.grade == fee_earner.grade)
    ]
    if matter_type_specific:
        return _most_recent(matter_type_specific).hourly_rate

    # 4. Grade-based default
    grade_specific = [
        r for r in active
        if r.grade == fee_earner.grade
        and r.matter_type is None
        and r.client_id is None
        and r.matter_id is None
    ]
    if grade_specific:
        return _most_recent(grade_specific).hourly_rate

    # 5. Fee earner default
    if fee_earner.default_hourly_rate and not fee_earner.default_hourly_rate.is_zero():
        return fee_earner.default_hourly_rate

    raise RateResolutionError(
        f"No billing rate found for fee earner {fee_earner.name} "
        f"(grade {fee_earner.grade}) on matter {matter.code} "
        f"(type {matter.matter_type}) as of {target_date}"
    )


def _most_recent(rates: list[BillingRate]) -> BillingRate:
    return max(rates, key=lambda r: r.effective_from)
