"""Data classes for the report engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from app.services.money import Money


LineCategory = Literal[
    "revenue",
    "cogs",
    "operating_expense",
    "other_income",
    "other_expense",
    "asset_current",
    "asset_non_current",
    "liability_current",
    "liability_non_current",
    "equity",
]


@dataclass
class PnlLine:
    code: str
    label: str
    category: LineCategory
    amount: Money
    prior_amount: Optional[Money] = None
    budget_amount: Optional[Money] = None


@dataclass
class BalanceSheetLine:
    code: str
    label: str
    category: LineCategory
    amount: Money
    prior_amount: Optional[Money] = None


@dataclass
class Comparatives:
    """Period the report compares against (prior year, prior month, etc.)."""
    label: str
    period_start: date
    period_end: date


@dataclass
class ReportInput:
    client_name: str
    period_start: date
    period_end: date
    currency: str
    language: str = "en"
    industry: str = ""
    pnl_lines: list[PnlLine] = field(default_factory=list)
    balance_sheet_lines: list[BalanceSheetLine] = field(default_factory=list)
    comparatives: Optional[Comparatives] = None


@dataclass
class ReportResult:
    client_name: str
    period_start: date
    period_end: date
    currency: str
    language: str
    pnl_lines: list[PnlLine]
    balance_sheet_lines: list[BalanceSheetLine]
    comparatives: Optional[Comparatives]
    narrative: str = ""

    # ── P&L roll-ups ────────────────────────────────────────────────

    @property
    def total_revenue(self) -> Money:
        return self._sum(self.pnl_lines, ("revenue", "other_income"))

    @property
    def total_expenses(self) -> Money:
        return self._sum(
            self.pnl_lines, ("cogs", "operating_expense", "other_expense")
        )

    @property
    def net_profit(self) -> Money:
        return self.total_revenue - self.total_expenses

    # ── Balance sheet roll-ups ──────────────────────────────────────

    @property
    def total_assets(self) -> Money:
        return self._sum(
            self.balance_sheet_lines, ("asset_current", "asset_non_current")
        )

    @property
    def total_liabilities(self) -> Money:
        return self._sum(
            self.balance_sheet_lines,
            ("liability_current", "liability_non_current"),
        )

    @property
    def total_equity(self) -> Money:
        return self._sum(self.balance_sheet_lines, ("equity",))

    @property
    def is_balanced(self) -> bool:
        """Assets must equal Liabilities + Equity."""
        diff = self.total_assets - (self.total_liabilities + self.total_equity)
        return diff.is_zero()

    # ── Variance helpers ───────────────────────────────────────────

    def variance_vs_prior(self, line: PnlLine) -> Optional[Decimal]:
        """% variance vs prior period. None if no comparative or zero base."""
        if not line.prior_amount or line.prior_amount.is_zero():
            return None
        diff = line.amount - line.prior_amount
        return (diff.amount / line.prior_amount.amount) * Decimal("100")

    # ── Internal ────────────────────────────────────────────────────

    def _sum(self, lines, categories: tuple[str, ...]) -> Money:
        if not lines:
            return Money.zero(self.currency)
        total = Money.zero(self.currency)
        for line in lines:
            if line.category in categories:
                total = total + line.amount
        return total
