from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from decimal import Decimal

from app.db.session import get_db
from app.auth.middleware import get_current_user, security
from app.models import Client, Account
from app.models.journal_entry import JournalEntry, JournalEntryLine
from app.models.invoice import Invoice
from app.schemas.report import (
    ProfitLossResponse,
    BalanceSheetResponse,
    BalanceSheetSection,
    TrialBalanceResponse,
    TrialBalanceRow,
    AgedDebtorsResponse,
    AgedBucket,
    AccountTotal,
)

router = APIRouter(prefix="/reports", tags=["reports"])


def _validate_client(db: Session, client_id: int, agency_id: int) -> Client:
    """Validate client belongs to agency."""
    client = db.query(Client).filter(
        Client.id == client_id, Client.agency_id == agency_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.get("/profit-loss", response_model=ProfitLossResponse)
async def profit_loss(
    client_id: int = Query(..., description="Client ID"),
    period_start: datetime = Query(..., description="Period start date"),
    period_end: datetime = Query(..., description="Period end date"),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Generate Profit & Loss report for a client and date range."""
    ctx = await get_current_user(credentials)
    _validate_client(db, client_id, ctx.agency_id)

    # Query posted journal entry lines grouped by account for revenue/expense
    results = (
        db.query(
            Account.id,
            Account.account_number,
            Account.name,
            Account.account_type,
            func.coalesce(func.sum(JournalEntryLine.debit_amount), 0).label("total_debit"),
            func.coalesce(func.sum(JournalEntryLine.credit_amount), 0).label("total_credit"),
        )
        .join(JournalEntryLine, JournalEntryLine.account_id == Account.id)
        .join(JournalEntry, JournalEntry.id == JournalEntryLine.entry_id)
        .filter(
            JournalEntry.client_id == client_id,
            JournalEntry.agency_id == ctx.agency_id,
            JournalEntry.status == "posted",
            JournalEntry.entry_date >= period_start,
            JournalEntry.entry_date <= period_end,
            Account.account_type.in_(["revenue", "expense"]),
        )
        .group_by(Account.id, Account.account_number, Account.name, Account.account_type)
        .all()
    )

    revenue_items = []
    expense_items = []
    total_revenue = Decimal("0")
    total_expenses = Decimal("0")

    for row in results:
        # Revenue accounts: credits increase, debits decrease
        # Expense accounts: debits increase, credits decrease
        if row.account_type == "revenue":
            net = row.total_credit - row.total_debit
            total_revenue += net
            revenue_items.append(AccountTotal(
                account_id=row.id,
                account_number=row.account_number,
                account_name=row.name,
                total=float(net),
            ))
        elif row.account_type == "expense":
            net = row.total_debit - row.total_credit
            total_expenses += net
            expense_items.append(AccountTotal(
                account_id=row.id,
                account_number=row.account_number,
                account_name=row.name,
                total=float(net),
            ))

    return ProfitLossResponse(
        client_id=client_id,
        period_start=period_start,
        period_end=period_end,
        revenue=revenue_items,
        expenses=expense_items,
        total_revenue=float(total_revenue),
        total_expenses=float(total_expenses),
        net_income=float(total_revenue - total_expenses),
    )


@router.get("/balance-sheet", response_model=BalanceSheetResponse)
async def balance_sheet(
    client_id: int = Query(..., description="Client ID"),
    as_at: datetime = Query(..., description="Balance sheet date"),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Generate Balance Sheet report for a client as at a specific date."""
    ctx = await get_current_user(credentials)
    _validate_client(db, client_id, ctx.agency_id)

    results = (
        db.query(
            Account.id,
            Account.account_number,
            Account.name,
            Account.account_type,
            func.coalesce(func.sum(JournalEntryLine.debit_amount), 0).label("total_debit"),
            func.coalesce(func.sum(JournalEntryLine.credit_amount), 0).label("total_credit"),
        )
        .join(JournalEntryLine, JournalEntryLine.account_id == Account.id)
        .join(JournalEntry, JournalEntry.id == JournalEntryLine.entry_id)
        .filter(
            JournalEntry.client_id == client_id,
            JournalEntry.agency_id == ctx.agency_id,
            JournalEntry.status == "posted",
            JournalEntry.entry_date <= as_at,
            Account.account_type.in_(["asset", "liability", "equity"]),
        )
        .group_by(Account.id, Account.account_number, Account.name, Account.account_type)
        .all()
    )

    assets = []
    liabilities = []
    equity = []
    total_assets = Decimal("0")
    total_liabilities = Decimal("0")
    total_equity = Decimal("0")

    for row in results:
        if row.account_type == "asset":
            net = row.total_debit - row.total_credit
            total_assets += net
            assets.append(AccountTotal(
                account_id=row.id,
                account_number=row.account_number,
                account_name=row.name,
                total=float(net),
            ))
        elif row.account_type == "liability":
            net = row.total_credit - row.total_debit
            total_liabilities += net
            liabilities.append(AccountTotal(
                account_id=row.id,
                account_number=row.account_number,
                account_name=row.name,
                total=float(net),
            ))
        elif row.account_type == "equity":
            net = row.total_credit - row.total_debit
            total_equity += net
            equity.append(AccountTotal(
                account_id=row.id,
                account_number=row.account_number,
                account_name=row.name,
                total=float(net),
            ))

    return BalanceSheetResponse(
        client_id=client_id,
        as_at=as_at,
        assets=BalanceSheetSection(accounts=assets, total=float(total_assets)),
        liabilities=BalanceSheetSection(accounts=liabilities, total=float(total_liabilities)),
        equity=BalanceSheetSection(accounts=equity, total=float(total_equity)),
    )


@router.get("/trial-balance", response_model=TrialBalanceResponse)
async def trial_balance(
    client_id: int = Query(..., description="Client ID"),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Generate Trial Balance report for a client."""
    ctx = await get_current_user(credentials)
    _validate_client(db, client_id, ctx.agency_id)

    results = (
        db.query(
            Account.id,
            Account.account_number,
            Account.name,
            func.coalesce(func.sum(JournalEntryLine.debit_amount), 0).label("total_debit"),
            func.coalesce(func.sum(JournalEntryLine.credit_amount), 0).label("total_credit"),
        )
        .join(JournalEntryLine, JournalEntryLine.account_id == Account.id)
        .join(JournalEntry, JournalEntry.id == JournalEntryLine.entry_id)
        .filter(
            JournalEntry.client_id == client_id,
            JournalEntry.agency_id == ctx.agency_id,
            JournalEntry.status == "posted",
        )
        .group_by(Account.id, Account.account_number, Account.name)
        .order_by(Account.account_number)
        .all()
    )

    rows = []
    total_debits = Decimal("0")
    total_credits = Decimal("0")

    for row in results:
        total_debits += row.total_debit
        total_credits += row.total_credit
        rows.append(TrialBalanceRow(
            account_id=row.id,
            account_number=row.account_number,
            account_name=row.name,
            debit_total=float(row.total_debit),
            credit_total=float(row.total_credit),
        ))

    return TrialBalanceResponse(
        client_id=client_id,
        rows=rows,
        total_debits=float(total_debits),
        total_credits=float(total_credits),
    )


@router.get("/aged-debtors", response_model=AgedDebtorsResponse)
async def aged_debtors(
    client_id: int = Query(..., description="Client ID"),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Generate Aged Debtors report — group AR invoices by 30/60/90/90+ days."""
    ctx = await get_current_user(credentials)
    _validate_client(db, client_id, ctx.agency_id)

    now = datetime.now(timezone.utc)

    # Get outstanding invoices (not paid)
    invoices = (
        db.query(Invoice)
        .filter(
            Invoice.client_id == client_id,
            Invoice.status.in_(["sent", "overdue"]),
        )
        .order_by(Invoice.due_date)
        .all()
    )

    current = []
    days_30 = []
    days_60 = []
    days_90 = []
    days_90_plus = []
    total = Decimal("0")

    for inv in invoices:
        due = inv.due_date
        if due is None:
            continue

        days_overdue = (now - due).days if now > due else 0
        bucket_item = AgedBucket(
            invoice_id=inv.id,
            invoice_number=inv.invoice_number,
            amount=float(inv.amount),
            due_date=due,
            days_overdue=max(days_overdue, 0),
        )
        total += inv.amount

        if days_overdue <= 0:
            current.append(bucket_item)
        elif days_overdue <= 30:
            days_30.append(bucket_item)
        elif days_overdue <= 60:
            days_60.append(bucket_item)
        elif days_overdue <= 90:
            days_90.append(bucket_item)
        else:
            days_90_plus.append(bucket_item)

    return AgedDebtorsResponse(
        client_id=client_id,
        as_at=now,
        current=current,
        days_30=days_30,
        days_60=days_60,
        days_90=days_90,
        days_90_plus=days_90_plus,
        total=float(total),
    )
