"""Data classes for the cashflow forecaster."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from app.services.money import Money


CashflowDirection = Literal["inflow", "outflow"]


@dataclass
class CashflowItem:
    """A single expected future cashflow event."""
    expected_date: date
    amount: Money
    direction: CashflowDirection
    description: str = ""
    source: str = ""        # "AR", "AP", "Payroll", "Manual", "Recurring"
    confidence: float = 1.0  # 0-1, used to discount uncertain items


@dataclass
class ForecastInput:
    """Inputs for a 13-week forecast."""
    opening_balance: Money
    forecast_start: date
    items: list[CashflowItem] = field(default_factory=list)
    weeks: int = 13
    threshold: Money | None = None  # Alert if any week closes below this
    client_id: int | None = None
    client_language: str = "en"
    client_industry: str = ""


@dataclass
class ForecastWeek:
    """One week of the forecast."""
    week_index: int
    week_start: date
    week_end: date
    opening_balance: Money
    inflows: Money
    outflows: Money
    closing_balance: Money
    below_threshold: bool = False
    item_count: int = 0


@dataclass
class ForecastResult:
    currency: str
    forecast_start: date
    forecast_end: date
    opening_balance: Money
    weeks: list[ForecastWeek]
    threshold: Money | None
    breach_weeks: list[int] = field(default_factory=list)
    narrative: str = ""

    @property
    def closing_balance(self) -> Money:
        if not self.weeks:
            return self.opening_balance
        return self.weeks[-1].closing_balance

    @property
    def total_inflows(self) -> Money:
        if not self.weeks:
            return Money.zero(self.currency)
        total = Money.zero(self.currency)
        for w in self.weeks:
            total = total + w.inflows
        return total

    @property
    def total_outflows(self) -> Money:
        if not self.weeks:
            return Money.zero(self.currency)
        total = Money.zero(self.currency)
        for w in self.weeks:
            total = total + w.outflows
        return total

    @property
    def lowest_balance(self) -> tuple[int, Money] | None:
        if not self.weeks:
            return None
        lowest_week = min(self.weeks, key=lambda w: w.closing_balance.amount)
        return (lowest_week.week_index, lowest_week.closing_balance)

    @property
    def has_breach(self) -> bool:
        return len(self.breach_weeks) > 0
