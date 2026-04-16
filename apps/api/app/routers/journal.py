"""
Journal Engine — double-entry journal posting, validation, reversals.
Also provides: Trial Balance, P&L, Balance Sheet.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, literal_column
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from app.database import get_db
from app.models import JournalEntry, JournalLine, Account
from app.auth import AuthUser, get_current_user

router = APIRouter(prefix="/api/v1/journal", tags=["journal"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class JournalLineCreate(BaseModel):
    account_id: int
    debit: Decimal = Field(default=Decimal("0"))
    credit: Decimal = Field(default=Decimal("0"))
    description: str | None = None

    @field_validator("debit", "credit")
    @classmethod
    def not_negative(cls, v):
        if v < 0:
            raise ValueError("Amount cannot be negative")
        return v


class JournalEntryCreate(BaseModel):
    client_id: int
    entry_date: datetime
    description: str | None = None
    reference: str | None = None
    lines: list[JournalLineCreate] = Field(..., min_length=2)

    @field_validator("lines")
    @classmethod
    def must_balance(cls, lines):
        total_debit = sum(l.debit for l in lines)
        total_credit = sum(l.credit for l in lines)
        if abs(total_debit - total_credit) > Decimal("0.01"):
            raise ValueError(
                f"Journal entry must balance — debits={total_debit}, credits={total_credit}"
            )
        if total_debit == 0 and total_credit == 0:
            raise ValueError("Journal entry must have at least one debit or credit")
        return lines


class JournalEntryOut(BaseModel):
    id: int
    client_id: int
    entry_date: datetime
    description: str | None
    reference: str | None
    is_reversal: bool
    reversed_id: int | None
    created_at: datetime
    lines: list

    class Config:
        from_attributes = True


class AccountBalance(BaseModel):
    account_id: int
    code: str
    name: str
    account_type: str
    debit_balance: Decimal
    credit_balance: Decimal
    net_balance: Decimal


class TrialBalanceResponse(BaseModel):
    client_id: int
    as_of_date: date
    accounts: list[AccountBalance]
    total_debits: Decimal
    total_credits: Decimal
    is_balanced: bool


# ─── Validation helpers ─────────────────────────────────────────────────────────

def validate_accounts_exist(db: Session, client_id: int, line_account_ids: list[int]) -> None:
    existing = {
        r[0] for r in
        db.query(Account.id)
          .filter(Account.client_id == client_id, Account.id.in_(line_account_ids))
          .all()
    }
    missing = set(line_account_ids) - existing
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Account IDs not found: {missing}",
        )


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("", response_model=JournalEntryOut, status_code=201)
def create_journal_entry(
    data: JournalEntryCreate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    Create and post a journal entry.
    Validates: debits == credits, accounts exist, accounts belong to client.
    """
    # Validate client access
    from app.models import Client
    client = db.query(Client).filter(
        Client.id == data.client_id,
        Client.agency_id == current_user.agency_id,
    ).first()
    if not client:
        raise HTTPException(status_code=403, detail="Client not found or access denied")

    # Validate accounts
    account_ids = [line.account_id for line in data.lines]
    validate_accounts_exist(db, data.client_id, account_ids)

    # Build entry + lines
    entry = JournalEntry(
        client_id=data.client_id,
        entry_date=data.entry_date,
        description=data.description,
        reference=data.reference,
        posted_by=current_user.id,
    )
    db.add(entry)
    db.flush()  # get entry.id

    for line_data in data.lines:
        line = JournalLine(
            entry_id=entry.id,
            account_id=line_data.account_id,
            debit=line_data.debit,
            credit=line_data.credit,
            description=line_data.description,
        )
        db.add(line)

    db.commit()
    db.refresh(entry)
    return entry


@router.get("/{entry_id}", response_model=JournalEntryOut)
def get_journal_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return entry


@router.get("")
def list_journal_entries(
    client_id: int = Query(...),
    skip: int = 0,
    limit: int = 100,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """List journal entries for a client."""
    from app.models import Client
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.agency_id == current_user.agency_id,
    ).first()
    if not client:
        raise HTTPException(status_code=403, detail="Client not found or access denied")

    q = db.query(JournalEntry).filter(JournalEntry.client_id == client_id)
    if from_date:
        q = q.filter(JournalEntry.entry_date >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        q = q.filter(JournalEntry.entry_date <= datetime.combine(to_date, datetime.max.time()))

    total = q.count()
    entries = q.order_by(JournalEntry.entry_date.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "entries": [
            JournalEntryOut.model_validate(e) for e in entries
        ],
    }


@router.post("/{entry_id}/reverse")
def reverse_journal_entry(
    entry_id: int,
    reversal_date: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    Create a reversing entry — debits become credits and vice versa.
    """
    original = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    # Verify agency access
    from app.models import Client
    client = db.query(Client).filter(
        Client.id == original.client_id,
        Client.agency_id == current_user.agency_id,
    ).first()
    if not client:
        raise HTTPException(status_code=403, detail="Access denied")

    if original.is_reversal:
        raise HTTPException(status_code=400, detail="Entry is already a reversal")

    if original.reversed_id:
        raise HTTPException(status_code=400, detail="Entry has already been reversed")

    reversal = JournalEntry(
        client_id=original.client_id,
        entry_date=reversal_date or datetime.now(),
        description=f"REVERSAL of #{original.id}: {original.description or ''}",
        reference=original.reference,
        posted_by=current_user.id,
        is_reversal=True,
        reversed_id=original.id,
    )
    db.add(reversal)
    db.flush()

    for line in db.query(JournalLine).filter(JournalLine.entry_id == original.id).all():
        reversal_line = JournalLine(
            entry_id=reversal.id,
            account_id=line.account_id,
            debit=line.credit,
            credit=line.debit,
            description=f"Reversal: {line.description or ''}",
        )
        db.add(reversal_line)

    db.commit()
    db.refresh(reversal)
    return reversal


# ─── Reports ──────────────────────────────────────────────────────────────────

@router.get("/reports/trial-balance", response_model=TrialBalanceResponse)
def trial_balance(
    client_id: int = Query(...),
    as_of_date: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    Trial Balance — sum of all debits and credits per account up to as_of_date.
    """
    from app.models import Client
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.agency_id == current_user.agency_id,
    ).first()
    if not client:
        raise HTTPException(status_code=403, detail="Client not found")

    as_of_dt = datetime.combine(as_of_date, datetime.max.time())

    balances = (
        db.query(
            Account.id.label("account_id"),
            Account.code,
            Account.name,
            Account.account_type,
            func.coalesce(func.sum(JournalLine.debit), literal_column("0")).label("total_debit"),
            func.coalesce(func.sum(JournalLine.credit), literal_column("0")).label("total_credit"),
        )
        .outerjoin(JournalLine, JournalLine.account_id == Account.id)
        .outerjoin(
            JournalEntry,
            JournalEntry.id == JournalLine.entry_id,
        )
        .filter(
            Account.client_id == client_id,
            Account.is_active == True,
            JournalEntry.is_reversal == False,
            (JournalEntry.entry_date <= as_of_dt) | (JournalEntry.entry_date == None),
        )
        .group_by(Account.id, Account.code, Account.name, Account.account_type)
        .all()
    )

    result = []
    total_debits = Decimal("0")
    total_credits = Decimal("0")

    for b in balances:
        debit_bal = Decimal(str(b.total_debit or 0))
        credit_bal = Decimal(str(b.total_credit or 0))

        # For debit-type accounts: balance = debits - credits
        # For credit-type accounts: balance = credits - debits
        if b.account_type in ("asset", "expense"):
            net = debit_bal - credit_bal
        else:
            net = credit_bal - debit_bal

        result.append(AccountBalance(
            account_id=b.account_id,
            code=b.code,
            name=b.name,
            account_type=b.account_type,
            debit_balance=max(debit_bal - credit_bal, Decimal("0")) if b.account_type in ("asset", "expense") else max(credit_bal - debit_bal, Decimal("0")),
            credit_balance=max(credit_bal - debit_bal, Decimal("0")) if b.account_type in ("liability", "equity", "revenue") else max(debit_bal - credit_bal, Decimal("0")),
            net_balance=net,
        ))

        if b.account_type in ("asset", "expense"):
            total_debits += net
        else:
            total_credits += net

    return TrialBalanceResponse(
        client_id=client_id,
        as_of_date=as_of_date,
        accounts=result,
        total_debits=total_debits,
        total_credits=total_credits,
        is_balanced=abs(total_debits - total_credits) < Decimal("0.01"),
    )


@router.get("/reports/balance-sheet")
def balance_sheet(
    client_id: int = Query(...),
    as_of_date: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    Balance Sheet — assets, liabilities, equity as of a date.
    Equity = Assets - Liabilities
    """
    from app.models import Client
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.agency_id == current_user.agency_id,
    ).first()
    if not client:
        raise HTTPException(status_code=403, detail="Client not found")

    as_of_dt = datetime.combine(as_of_date, datetime.max.time())

    def get_type_total(type_: str) -> Decimal:
        rows = (
            db.query(
                func.coalesce(func.sum(JournalLine.debit), literal_column("0")).label("debit"),
                func.coalesce(func.sum(JournalLine.credit), literal_column("0")).label("credit"),
            )
            .join(Account, Account.id == JournalLine.account_id)
            .join(JournalEntry, JournalEntry.id == JournalLine.entry_id)
            .filter(
                Account.client_id == client_id,
                Account.account_type == type_,
                Account.is_active == True,
                JournalEntry.is_reversal == False,
                JournalEntry.entry_date <= as_of_dt,
            )
            .first()
        )
        dr = Decimal(str(rows.debit or 0))
        cr = Decimal(str(rows.credit or 0))
        if type_ in ("asset", "expense"):
            return dr - cr
        else:
            return cr - dr

    assets = get_type_total("asset")
    liabilities = get_type_total("liability")
    equity = get_type_total("equity")
    revenue = get_type_total("revenue")
    expenses = get_type_total("expense")

    # Equity = Assets - Liabilities
    computed_equity = assets - liabilities
    net_profit = revenue - expenses

    return {
        "as_of_date": as_of_date,
        "assets": assets,
        "liabilities": liabilities,
        "equity": computed_equity + net_profit,
        "liabilities_and_equity": liabilities + computed_equity + net_profit,
        "check": abs(assets - (liabilities + computed_equity + net_profit)) < Decimal("0.01"),
    }
