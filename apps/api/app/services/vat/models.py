"""Data classes for the VAT return engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Literal

from app.services.money import Money


VatDirection = Literal["sale", "purchase"]


@dataclass
class VatTransaction:
    """
    A single VAT-relevant transaction. Usually built by the engine from a
    journal line, but the VAT engine is agnostic — tests can construct
    these directly.

    `amount_net` is the ex-VAT amount. `vat_code` is the jurisdiction-
    specific rate code (e.g. NO-25, SE-12, FI-255).
    """
    amount_net: Money
    vat_code: str
    direction: VatDirection        # "sale" → output VAT, "purchase" → input VAT
    description: str = ""
    # Original journal line reference for audit trail
    journal_line_id: int | None = None


@dataclass
class VatReturnInput:
    """Input for building a VAT return."""
    country: str                   # NO / SE / FI
    period_start: date
    period_end: date
    transactions: list[VatTransaction]
    client_id: int | None = None
    organisation_number: str = ""


@dataclass
class VatReturnLine:
    """One row on the VAT return — one VAT rate bracket."""
    code: str                      # e.g. "NO-25"
    rate: Decimal                  # 0.25 for 25%
    direction: VatDirection
    net_total: Money               # sum of amount_net for this code
    vat_total: Money               # net_total * rate


@dataclass
class VatReturnResult:
    """Output of a VAT return calculation."""
    country: str
    period_start: date
    period_end: date
    currency: str
    lines: list[VatReturnLine] = field(default_factory=list)
    # The government-facing payload, lazily generated
    _xml: str | None = None

    @property
    def total_output_vat(self) -> Money:
        """Sum of VAT on sales (what we owe to the tax authority)."""
        total = Money.zero(self.currency)
        for l in self.lines:
            if l.direction == "sale":
                total = total + l.vat_total
        return total

    @property
    def total_input_vat(self) -> Money:
        """Sum of VAT on purchases (what we can claim back)."""
        total = Money.zero(self.currency)
        for l in self.lines:
            if l.direction == "purchase":
                total = total + l.vat_total
        return total

    @property
    def net_vat_payable(self) -> Money:
        """Output - Input. Positive = we pay; negative = refund due."""
        return self.total_output_vat - self.total_input_vat
