"""
Hospitality VAT splitting — the critical Nordic compliance piece.

Different outlet types get different VAT rates in each country, and
this module maps (country, outlet_type) → (vat_code, rate) so the auto-
journal posts to the right accounts.

Sources (2026 rates):

  Norway (NO):
    rooms:             12% (reduced — accommodation)
    food:              25% (standard)
    beverage_alcohol:  25% (standard, but licensing rules apply separately)
    beverage_soft:     25%
    spa:               25%
    conference:        25%

  Sweden (SE):
    rooms:             12% (reduced — accommodation)
    food:              12% (reduced from 2024 — restaurant food)
    beverage_alcohol:  25% (standard — alcohol is always full rate)
    beverage_soft:     25% (unless served with food, then 12% — simplified to 25% here)
    spa:               25%
    conference:        25%

  Finland (FI):
    rooms:             14% (reduced — accommodation)
    food:              14% (reduced — restaurant food)
    beverage_alcohol:  25.5% (standard)
    beverage_soft:     14% (when served, simplified)
    spa:               25.5%
    conference:        25.5%

These rates are simplifications — real-world hotels have edge cases
around takeaway vs. dine-in, alcohol service licensing, spa treatments
classed as medical, etc. Configurable per client overrides belong in
jurisdiction_configs.config_overrides JSON (Tier 1 migration 005).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.services.money import Money

from .models import RevenueLineItem, OutletType


# ── Rate lookup ─────────────────────────────────────────────────────────────


VAT_BY_COUNTRY_AND_OUTLET: dict[str, dict[OutletType, tuple[str, Decimal]]] = {
    "NO": {
        "rooms": ("NO-12", Decimal("0.12")),
        "food": ("NO-25", Decimal("0.25")),
        "beverage_soft": ("NO-25", Decimal("0.25")),
        "beverage_alcohol": ("NO-25", Decimal("0.25")),
        "spa": ("NO-25", Decimal("0.25")),
        "conference": ("NO-25", Decimal("0.25")),
        "retail": ("NO-25", Decimal("0.25")),
        "other": ("NO-25", Decimal("0.25")),
    },
    "SE": {
        "rooms": ("SE-12", Decimal("0.12")),
        "food": ("SE-12", Decimal("0.12")),
        "beverage_soft": ("SE-25", Decimal("0.25")),
        "beverage_alcohol": ("SE-25", Decimal("0.25")),
        "spa": ("SE-25", Decimal("0.25")),
        "conference": ("SE-25", Decimal("0.25")),
        "retail": ("SE-25", Decimal("0.25")),
        "other": ("SE-25", Decimal("0.25")),
    },
    "FI": {
        "rooms": ("FI-14", Decimal("0.14")),
        "food": ("FI-14", Decimal("0.14")),
        "beverage_soft": ("FI-14", Decimal("0.14")),
        "beverage_alcohol": ("FI-255", Decimal("0.255")),
        "spa": ("FI-255", Decimal("0.255")),
        "conference": ("FI-255", Decimal("0.255")),
        "retail": ("FI-255", Decimal("0.255")),
        "other": ("FI-255", Decimal("0.255")),
    },
}


# ── Result value objects ─────────────────────────────────────────────────────


@dataclass
class VatSplitLine:
    outlet_type: OutletType
    vat_code: str
    rate: Decimal
    gross: Money
    net: Money
    vat: Money


@dataclass
class VatSplitResult:
    country: str
    currency: str
    lines: list[VatSplitLine]

    @property
    def total_gross(self) -> Money:
        if not self.lines:
            return Money.zero(self.currency)
        total = Money.zero(self.currency)
        for l in self.lines:
            total = total + l.gross
        return total

    @property
    def total_net(self) -> Money:
        if not self.lines:
            return Money.zero(self.currency)
        total = Money.zero(self.currency)
        for l in self.lines:
            total = total + l.net
        return total

    @property
    def total_vat(self) -> Money:
        if not self.lines:
            return Money.zero(self.currency)
        total = Money.zero(self.currency)
        for l in self.lines:
            total = total + l.vat
        return total


# ── Splitter ────────────────────────────────────────────────────────────────


def split_revenue_by_country(
    country: str,
    line_items: list[RevenueLineItem],
) -> VatSplitResult:
    """
    Split a list of gross-revenue line items into their VAT components
    for the given country.

    Each input line is gross (VAT-inclusive). The splitter calculates
    net = gross / (1 + rate) and vat = gross - net, so downstream
    auto-journal can post net to revenue and vat to the VAT liability
    account with the correct code.
    """
    cc = country.upper()
    if cc not in VAT_BY_COUNTRY_AND_OUTLET:
        raise ValueError(
            f"Unsupported country {country}. Supported: "
            f"{sorted(VAT_BY_COUNTRY_AND_OUTLET.keys())}"
        )
    if not line_items:
        raise ValueError("Cannot split empty line item list")

    currency = line_items[0].amount.currency
    for item in line_items[1:]:
        if item.amount.currency != currency:
            raise ValueError(
                f"Line items must share a currency. Got {currency} and "
                f"{item.amount.currency}"
            )

    rate_map = VAT_BY_COUNTRY_AND_OUTLET[cc]
    out_lines: list[VatSplitLine] = []
    for item in line_items:
        if item.outlet_type not in rate_map:
            raise ValueError(
                f"No VAT mapping for {cc} + {item.outlet_type}"
            )
        vat_code, rate = rate_map[item.outlet_type]
        gross = item.amount
        # net = gross / (1 + rate)
        net_amount = gross.amount / (Decimal("1") + rate)
        net = Money(net_amount, currency)
        vat = gross - net
        out_lines.append(
            VatSplitLine(
                outlet_type=item.outlet_type,
                vat_code=vat_code,
                rate=rate,
                gross=gross,
                net=net,
                vat=vat,
            )
        )

    return VatSplitResult(
        country=cc,
        currency=currency,
        lines=out_lines,
    )
