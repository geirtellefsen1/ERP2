"""
VAT return engine — aggregates transactions by VAT code and dispatches to
the correct country module to produce the statutory XML/JSON payload.
"""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from app.jurisdictions import JurisdictionEngine
from app.services.money import Money

from .models import (
    VatReturnInput,
    VatReturnLine,
    VatReturnResult,
    VatTransaction,
)


def build_vat_return(input: VatReturnInput) -> VatReturnResult:
    """
    Build a VAT return by aggregating transactions into one line per
    (vat_code, direction) pair.

    Currency is derived from the first transaction — all transactions in
    a single return must be in the same currency, matching the client's
    jurisdiction currency.
    """
    country = input.country.upper()

    if not input.transactions:
        currency = JurisdictionEngine.get_currency(country)
        return VatReturnResult(
            country=country,
            period_start=input.period_start,
            period_end=input.period_end,
            currency=currency,
        )

    # Validate currency consistency
    currency = input.transactions[0].amount_net.currency
    for t in input.transactions[1:]:
        if t.amount_net.currency != currency:
            raise ValueError(
                f"All transactions in a VAT return must share the same currency. "
                f"Got {currency} and {t.amount_net.currency}."
            )

    expected = JurisdictionEngine.get_currency(country)
    if currency != expected:
        raise ValueError(
            f"VAT return currency {currency} does not match {country} "
            f"jurisdiction currency {expected}"
        )

    # Look up this country's VAT rate table for the period end date so we
    # pick up Finland's 24% → 25.5% switch correctly.
    rates_table = JurisdictionEngine.get_vat_rates(country, input.period_end)
    rate_map: dict[str, Decimal] = {r.code: r.rate for r in rates_table}

    # Group by (code, direction)
    groups: dict[tuple[str, str], list[VatTransaction]] = defaultdict(list)
    for t in input.transactions:
        groups[(t.vat_code, t.direction)].append(t)

    lines: list[VatReturnLine] = []
    for (vat_code, direction), txs in sorted(groups.items()):
        if vat_code not in rate_map:
            raise ValueError(
                f"Unknown VAT code '{vat_code}' for {country}. "
                f"Known codes: {sorted(rate_map.keys())}"
            )
        rate = rate_map[vat_code]

        net_total = Money.zero(currency)
        for t in txs:
            net_total = net_total + t.amount_net
        vat_total = net_total * rate

        lines.append(
            VatReturnLine(
                code=vat_code,
                rate=rate,
                direction=direction,
                net_total=net_total,
                vat_total=vat_total,
            )
        )

    return VatReturnResult(
        country=country,
        period_start=input.period_start,
        period_end=input.period_end,
        currency=currency,
        lines=lines,
    )
