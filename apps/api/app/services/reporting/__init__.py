"""
Month-end report narrative engine.

Produces a structured monthly management report:
  - P&L: current period vs. prior period vs. budget
  - Balance Sheet: as-at period end vs. prior period end
  - Claude-generated narrative explaining variances in the client's language
  - PDF rendering via ReportLab
  - Scheduled delivery via the delivery service

Usage:
    from app.services.reporting import build_report, ReportInput

    report = build_report(
        ReportInput(
            client_name="Acme AS",
            period_start=date(2026, 3, 1),
            period_end=date(2026, 3, 31),
            currency="NOK",
            language="nb-NO",
            pnl_lines=[...],
            balance_sheet_lines=[...],
            comparatives=...,
        )
    )
    pdf_bytes = report.to_pdf()
"""
from .models import (
    ReportInput,
    ReportResult,
    PnlLine,
    BalanceSheetLine,
    Comparatives,
    LineCategory,
)
from .engine import build_report
from .narrator import generate_report_narrative
from .pdf import render_report_pdf

__all__ = [
    "ReportInput",
    "ReportResult",
    "PnlLine",
    "BalanceSheetLine",
    "Comparatives",
    "LineCategory",
    "build_report",
    "generate_report_narrative",
    "render_report_pdf",
]
