"""
PDF rendering for month-end reports.

Uses ReportLab's high-level Platypus API. Produces a clean A4 portrait
report with:
  - Title block (client name, period, generated-at timestamp)
  - P&L table with prior-period comparatives
  - Balance sheet table with prior-period comparatives
  - AI narrative section (if present)
  - Footer with page number

Returns raw PDF bytes — caller decides whether to write to disk, attach
to an email, store in DO Spaces, or stream to the browser.
"""
from __future__ import annotations

import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from .models import ReportResult


def _money_str(amount, currency: str) -> str:
    """Format a Decimal amount with thousand separators."""
    return f"{amount:,.2f} {currency}"


def render_report_pdf(result: ReportResult) -> bytes:
    """
    Render the report to PDF bytes.

    The output is deterministic apart from the generated-at timestamp
    in the footer, which makes it easy to test by checking that the
    bytes start with %PDF and contain known content strings.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        title=f"Management Report — {result.client_name}",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=4,
        textColor=colors.HexColor("#1E40AF"),
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=12,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=14,
        spaceAfter=8,
        textColor=colors.HexColor("#0F172A"),
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
    )

    story: list = []

    # Title block
    story.append(Paragraph(result.client_name, title_style))
    period_label = (
        f"Management Report — {result.period_start.isoformat()} to "
        f"{result.period_end.isoformat()}"
    )
    story.append(Paragraph(period_label, subtitle_style))
    story.append(
        Paragraph(
            f"Generated {datetime.now(timezone.utc).isoformat()} · "
            f"Currency: {result.currency} · "
            f"Language: {result.language}",
            subtitle_style,
        )
    )

    # ── P&L table ────────────────────────────────────────────────
    story.append(Paragraph("Profit &amp; Loss", section_style))
    pnl_data: list[list] = [
        ["Code", "Account", "Category", "Amount", "Prior", "Variance"],
    ]
    for line in result.pnl_lines:
        prior_str = (
            _money_str(line.prior_amount.amount, line.prior_amount.currency)
            if line.prior_amount
            else "—"
        )
        variance_pct = result.variance_vs_prior(line)
        variance_str = f"{variance_pct:+.1f}%" if variance_pct is not None else "—"
        pnl_data.append([
            line.code,
            line.label,
            line.category,
            _money_str(line.amount.amount, line.amount.currency),
            prior_str,
            variance_str,
        ])

    pnl_data.append([
        "",
        "Total revenue",
        "",
        _money_str(result.total_revenue.amount, result.currency),
        "",
        "",
    ])
    pnl_data.append([
        "",
        "Total expenses",
        "",
        _money_str(result.total_expenses.amount, result.currency),
        "",
        "",
    ])
    pnl_data.append([
        "",
        "Net profit",
        "",
        _money_str(result.net_profit.amount, result.currency),
        "",
        "",
    ])

    pnl_table = Table(pnl_data, colWidths=[18 * mm, 55 * mm, 30 * mm, 30 * mm, 25 * mm, 18 * mm])
    pnl_table.setStyle(_table_style(len(pnl_data)))
    story.append(pnl_table)

    # ── Balance sheet table ─────────────────────────────────────
    story.append(Paragraph("Balance Sheet", section_style))
    bs_data: list[list] = [
        ["Code", "Account", "Category", "Amount", "Prior"],
    ]
    for line in result.balance_sheet_lines:
        prior_str = (
            _money_str(line.prior_amount.amount, line.prior_amount.currency)
            if line.prior_amount
            else "—"
        )
        bs_data.append([
            line.code,
            line.label,
            line.category,
            _money_str(line.amount.amount, line.amount.currency),
            prior_str,
        ])
    bs_data.append([
        "",
        "Total assets",
        "",
        _money_str(result.total_assets.amount, result.currency),
        "",
    ])
    bs_data.append([
        "",
        "Total liabilities",
        "",
        _money_str(result.total_liabilities.amount, result.currency),
        "",
    ])
    bs_data.append([
        "",
        "Total equity",
        "",
        _money_str(result.total_equity.amount, result.currency),
        "",
    ])

    bs_table = Table(bs_data, colWidths=[18 * mm, 70 * mm, 35 * mm, 35 * mm, 18 * mm])
    bs_table.setStyle(_table_style(len(bs_data)))
    story.append(bs_table)

    # ── Narrative ────────────────────────────────────────────────
    if result.narrative:
        story.append(Paragraph("Management Commentary", section_style))
        # ReportLab paragraphs use HTML-ish markup; escape & in narrative
        safe_narrative = result.narrative.replace("&", "&amp;")
        # Convert paragraph breaks to <br/><br/>
        safe_narrative = safe_narrative.replace("\n\n", "<br/><br/>")
        story.append(Paragraph(safe_narrative, body_style))

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes


def _table_style(row_count: int) -> TableStyle:
    """Standard table styling: header row, gridlines, alternating shading."""
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E40AF")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -4), [colors.white, colors.HexColor("#F8FAFC")]),
        ("BACKGROUND", (0, -3), (-1, -1), colors.HexColor("#EFF6FF")),
        ("FONTNAME", (0, -3), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (3, 0), (5, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])
