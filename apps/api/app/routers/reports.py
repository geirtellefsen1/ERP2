"""
Standard Financial Reports — P&L, Balance Sheet, Cash Flow, PDF export.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, literal_column
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from io import BytesIO
from app.database import get_db
from app.models import Account, JournalEntry, JournalLine, Invoice, Client
from app.auth import AuthUser, get_current_user
from app.config import get_settings
import re

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])
settings = get_settings()


# ─── Date range helpers ────────────────────────────────────────────────────────

def parse_date_range(year: int, month: int = None, quarter: int = None):
    if quarter:
        q_map = {1: (1, 3), 2: (4, 6), 3: (7, 9), 4: (10, 12)}
        start_m, end_m = q_map[quarter]
        start = datetime(year, start_m, 1)
        end = datetime(year, end_m, 1, 23, 59, 59)
    elif month:
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        end = end.replace(hour=23, minute=59, second=59)
    else:
        start = datetime(year, 1, 1)
        end = datetime(year, 12, 31, 23, 59, 59)
    return start, end


def get_period_totals(db: Session, client_id: int, start: datetime, end: datetime):
    """Return a dict of account_code -> {debit_total, credit_total}"""
    rows = (
        db.query(
            Account.code,
            Account.name,
            Account.account_type,
            func.coalesce(func.sum(JournalLine.debit), literal_column("0")).label("total_debit"),
            func.coalesce(func.sum(JournalLine.credit), literal_column("0")).label("total_credit"),
        )
        .join(JournalLine, JournalLine.account_id == Account.id)
        .join(JournalEntry, JournalEntry.id == JournalLine.entry_id)
        .filter(
            Account.client_id == client_id,
            JournalEntry.is_reversal == False,
            JournalEntry.entry_date >= start,
            JournalEntry.entry_date <= end,
        )
        .group_by(Account.id)
        .all()
    )
    return {
        r.code: {
            "name": r.name,
            "account_type": r.account_type,
            "debit": Decimal(str(r.total_debit or 0)),
            "credit": Decimal(str(r.total_credit or 0)),
        }
        for r in rows
    }


def net_balance(code: str, account_type: str, debit: Decimal, credit: Decimal) -> Decimal:
    if account_type in ("asset", "expense"):
        return debit - credit
    return credit - debit


# ─── P&L ───────────────────────────────────────────────────────────────────────

@router.get("/profit-and-loss")
def profit_and_loss(
    client_id: int = Query(...),
    year: int = Query(default_factory=lambda: date.today().year),
    month: int = Query(default=None),
    quarter: int = Query(default=None),
    format: str = Query(default="json"),  # json or pdf
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """P&L — Revenue - Expenses for the period."""
    client = _verify_client_access(db, client_id, current_user)
    start, end = parse_date_range(year, month, quarter)
    totals = get_period_totals(db, client_id, start, end)

    revenue_lines, expense_lines, other_lines = [], [], []
    total_revenue = Decimal("0")
    total_expense = Decimal("0")

    for code, data in sorted(totals.items()):
        net = net_balance(code, data["account_type"], data["debit"], data["credit"])
        line = {
            "code": code, "name": data["name"],
            "amount": abs(net),
            "type": data["account_type"],
        }
        if data["account_type"] == "revenue":
            revenue_lines.append(line)
            total_revenue += abs(net)
        elif data["account_type"] == "expense":
            expense_lines.append(line)
            total_expense += abs(net)
        else:
            other_lines.append(line)

    net_profit = total_revenue - total_expense

    result = {
        "report": "Profit & Loss",
        "client": client.name,
        "period": f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}",
        "revenue": {"lines": revenue_lines, "total": total_revenue},
        "expenses": {"lines": expense_lines, "total": total_expense},
        "net_profit": net_profit,
        "margin": float(net_profit / total_revenue) if total_revenue else 0,
        "generated_at": datetime.utcnow().isoformat(),
    }

    if format == "pdf":
        return _generate_pdf_report(result, "Profit & Loss")
    return result


# ─── Balance Sheet ─────────────────────────────────────────────────────────────

@router.get("/balance-sheet")
def balance_sheet(
    client_id: int = Query(...),
    as_of_date: date = Query(default_factory=date.today),
    format: str = Query(default="json"),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Balance Sheet — Assets = Liabilities + Equity as of a date."""
    client = _verify_client_access(db, client_id, current_user)
    as_of_dt = datetime.combine(as_of_date, datetime.max.time())
    year_end = datetime(as_of_date.year, 12, 31, 23, 59, 59)
    start_of_year = datetime(as_of_date.year, 1, 1, 0, 0, 0)

    ytd_totals = get_period_totals(db, client_id, start_of_year, as_of_dt)
    cumulative_totals = get_period_totals(db, client_id, datetime(2000, 1, 1), as_of_dt)

    def section_total(codes: list[str], atype: str) -> tuple[list, Decimal]:
        lines, total = [], Decimal("0")
        for code, data in sorted(cumulative_totals.items()):
            if data["account_type"] == atype:
                net = net_balance(code, atype, data["debit"], data["credit"])
                lines.append({"code": code, "name": data["name"], "amount": net})
                total += net
        return lines, total

    assets, total_assets = section_total([], "asset")
    liabilities, total_liabilities = section_total([], "liability")
    equity_lines, total_equity = section_total([], "equity")

    # P&L YTD net profit/ loss
    net_pnl_ytd = Decimal("0")
    for code, data in ytd_totals.items():
        if data["account_type"] == "revenue":
            net_pnl_ytd += net_balance(code, data["account_type"], data["debit"], data["credit"])
        elif data["account_type"] == "expense":
            net_pnl_ytd -= net_balance(code, data["account_type"], data["debit"], data["credit"])

    total_equity_adjusted = total_equity + net_pnl_ytd

    result = {
        "report": "Balance Sheet",
        "client": client.name,
        "as_of_date": as_of_date.isoformat(),
        "assets": {"lines": assets, "total": total_assets},
        "liabilities": {"lines": liabilities, "total": total_liabilities},
        "equity": {"lines": equity_lines, "total": total_equity_adjusted},
        "liabilities_and_equity": total_liabilities + total_equity_adjusted,
        "check": abs(total_assets - (total_liabilities + total_equity_adjusted)) < Decimal("0.01"),
        "generated_at": datetime.utcnow().isoformat(),
    }

    if format == "pdf":
        return _generate_pdf_report(result, "Balance Sheet")
    return result


# ─── Cash Flow ─────────────────────────────────────────────────────────────────

@router.get("/cash-flow")
def cash_flow(
    client_id: int = Query(...),
    year: int = Query(default_factory=lambda: date.today().year),
    month: int = Query(default=None),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """13-week cash flow or monthly cash flow summary."""
    client = _verify_client_access(db, client_id, current_user)
    start, end = parse_date_range(year, month)

    totals = get_period_totals(db, client_id, start, end)

    operating, investing, financing = [], [], []
    total_operating = total_investing = total_financing = Decimal("0")

    for code, data in sorted(totals.items()):
        net = net_balance(code, data["account_type"], data["debit"], data["credit"])
        # Simple heuristic — in practice map accounts to categories
        if data["account_type"] == "asset":
            operating.append({"code": code, "name": data["name"], "amount": net})
            total_operating += net
        elif data["account_type"] == "liability":
            financing.append({"code": code, "name": data["name"], "amount": net})
            total_financing += net
        elif data["account_type"] == "revenue":
            operating.append({"code": code, "name": data["name"], "amount": net})
            total_operating += net
        elif data["account_type"] == "expense":
            operating.append({"code": code, "name": data["name"], "amount": net})
            total_operating += net

    return {
        "report": "Cash Flow",
        "client": client.name,
        "period": f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}",
        "operating": {"lines": operating, "total": total_operating},
        "net_cash": total_operating + total_investing + total_financing,
        "generated_at": datetime.utcnow().isoformat(),
    }


# ─── PDF generation ──────────────────────────────────────────────────────────────

def _generate_pdf_report(data: dict, report_title: str) -> StreamingResponse:
    """Generate a simple PDF report using ReportLab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="PDF generation requires reportlab — pip install reportlab",
        )

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(report_title, styles["Title"]))
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph(f"Client: {data.get('client', 'N/A')}", styles["Normal"]))
    elements.append(Paragraph(f"Period: {data.get('period', data.get('as_of_date', 'N/A'))}", styles["Normal"]))
    elements.append(Spacer(1, 1 * cm))

    # Revenue section
    if "revenue" in data:
        rev = data["revenue"]
        elements.append(Paragraph("Revenue", styles["Heading2"]))
        rows = [[p["code"], p["name"], f"R {p['amount']:,.2f}"] for p in rev.get("lines", [])]
        rows.append(["", "Total Revenue", f"R {rev['total']:,.2f}"])
        t = Table(rows, colWidths=[2*cm, 10*cm, 4*cm])
        t.setStyle(TableStyle([("FONTSIZE", (0,0), (-1,-1), 9)]))
        elements.append(t)
        elements.append(Spacer(1, 0.5*cm))

    # Expenses
    if "expenses" in data:
        exp = data["expenses"]
        elements.append(Paragraph("Expenses", styles["Heading2"]))
        rows = [[p["code"], p["name"], f"R {p['amount']:,.2f}"] for p in exp.get("lines", [])]
        rows.append(["", "Total Expenses", f"R {exp['total']:,.2f}"])
        t = Table(rows, colWidths=[2*cm, 10*cm, 4*cm])
        t.setStyle(TableStyle([("FONTSIZE", (0,0), (-1,-1), 9)]))
        elements.append(t)
        elements.append(Spacer(1, 0.5*cm))

    # Net Profit / Balance
    if "net_profit" in data:
        net = data["net_profit"]
        color = colors.green if net >= 0 else colors.red
        rows = [["", "Net Profit / (Loss)", f"R {net:,.2f}"]]
        t = Table(rows, colWidths=[2*cm, 10*cm, 4*cm])
        t.setStyle(TableStyle([("FONTSIZE", (0,0), (-1,-1), 12), ("TEXTCOLOR", (2,0), (2,0), color)]))
        elements.append(t)

    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"{report_title.replace(' ', '_')}.pdf\""},
    )


def _verify_client_access(db, client_id, current_user):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.agency_id == current_user.agency_id,
    ).first()
    if not client:
        raise HTTPException(status_code=403, detail="Client not found or access denied")
    return client
