"""Report builder — assembles a ReportResult from input data."""
from __future__ import annotations

from .models import ReportInput, ReportResult


def build_report(input: ReportInput) -> ReportResult:
    """
    Build a structured report result from raw P&L and Balance Sheet lines.

    This is a pure transformation: it does not call Claude, write to the
    database, or generate PDFs. Those are downstream concerns.

    Validates that all amounts are in the declared currency.
    """
    for line in input.pnl_lines:
        if line.amount.currency != input.currency:
            raise ValueError(
                f"P&L line {line.code} has currency {line.amount.currency}, "
                f"expected {input.currency}"
            )
        if line.prior_amount and line.prior_amount.currency != input.currency:
            raise ValueError(
                f"P&L line {line.code} prior period has currency "
                f"{line.prior_amount.currency}, expected {input.currency}"
            )

    for line in input.balance_sheet_lines:
        if line.amount.currency != input.currency:
            raise ValueError(
                f"Balance sheet line {line.code} has currency "
                f"{line.amount.currency}, expected {input.currency}"
            )

    return ReportResult(
        client_name=input.client_name,
        period_start=input.period_start,
        period_end=input.period_end,
        currency=input.currency,
        language=input.language,
        pnl_lines=list(input.pnl_lines),
        balance_sheet_lines=list(input.balance_sheet_lines),
        comparatives=input.comparatives,
    )
