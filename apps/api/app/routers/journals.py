from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from datetime import datetime, timezone
import uuid

from app.db.session import get_db
from app.auth.middleware import get_current_user, security
from app.models import Account, Client
from app.models.journal_entry import JournalEntry, JournalEntryLine
from app.models.posting_period import PostingPeriod
from app.schemas.journal import (
    JournalEntryCreate,
    JournalEntryResponse,
    JournalEntryDetailResponse,
)
from app.services.journal_validator import validate_entry

router = APIRouter(prefix="/journals", tags=["journals"])


def _generate_entry_number() -> str:
    """Generate a unique journal entry number."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    short_id = uuid.uuid4().hex[:6].upper()
    return f"JE-{timestamp}-{short_id}"


@router.get("", response_model=list[JournalEntryResponse])
async def list_journals(
    client_id: int = Query(..., description="Client ID to filter journals"),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List journal entries for a client."""
    ctx = await get_current_user(credentials)
    client = db.query(Client).filter(
        Client.id == client_id, Client.agency_id == ctx.agency_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    entries = (
        db.query(JournalEntry)
        .filter(JournalEntry.client_id == client_id, JournalEntry.agency_id == ctx.agency_id)
        .order_by(JournalEntry.entry_date.desc())
        .all()
    )
    return entries


@router.get("/{entry_id}", response_model=JournalEntryDetailResponse)
async def get_journal(
    entry_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get a journal entry with its lines."""
    ctx = await get_current_user(credentials)
    entry = db.query(JournalEntry).filter(
        JournalEntry.id == entry_id, JournalEntry.agency_id == ctx.agency_id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return entry


@router.post("", response_model=JournalEntryResponse, status_code=201)
async def create_journal(
    data: JournalEntryCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Create a new journal entry."""
    ctx = await get_current_user(credentials)

    # Validate client belongs to agency
    client = db.query(Client).filter(
        Client.id == data.client_id, Client.agency_id == ctx.agency_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Validate posting period
    period = db.query(PostingPeriod).filter(
        PostingPeriod.id == data.posting_period_id,
        PostingPeriod.agency_id == ctx.agency_id,
    ).first()
    if not period:
        raise HTTPException(status_code=404, detail="Posting period not found")
    if period.status != "open":
        raise HTTPException(status_code=400, detail="Posting period is not open")

    # Validate lines
    is_valid, errors = validate_entry(data.lines)
    if not is_valid:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    # Calculate totals
    debit_total = sum(Decimal(str(line.debit_amount)) for line in data.lines)
    credit_total = sum(Decimal(str(line.credit_amount)) for line in data.lines)

    entry = JournalEntry(
        agency_id=ctx.agency_id,
        client_id=data.client_id,
        posting_period_id=data.posting_period_id,
        entry_number=_generate_entry_number(),
        entry_date=data.entry_date,
        description=data.description,
        debit_total=debit_total,
        credit_total=credit_total,
        status="balanced" if debit_total == credit_total else "draft",
        is_balanced=debit_total == credit_total,
    )
    db.add(entry)
    db.flush()

    for i, line_data in enumerate(data.lines):
        line = JournalEntryLine(
            entry_id=entry.id,
            account_id=line_data.account_id,
            debit_amount=Decimal(str(line_data.debit_amount)),
            credit_amount=Decimal(str(line_data.credit_amount)),
            description=line_data.description,
            line_number=i + 1,
        )
        db.add(line)

    db.commit()
    db.refresh(entry)
    return entry


@router.post("/{entry_id}/post", response_model=JournalEntryResponse)
async def post_journal(
    entry_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Post a journal entry, updating account balances."""
    ctx = await get_current_user(credentials)
    entry = db.query(JournalEntry).filter(
        JournalEntry.id == entry_id, JournalEntry.agency_id == ctx.agency_id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    if entry.status == "posted":
        raise HTTPException(status_code=400, detail="Entry is already posted")
    if entry.status == "reversed":
        raise HTTPException(status_code=400, detail="Cannot post a reversed entry")
    if not entry.is_balanced:
        raise HTTPException(status_code=400, detail="Entry is not balanced")

    # Update account balances
    for line in entry.lines:
        account = db.query(Account).filter(Account.id == line.account_id).first()
        if account:
            current_balance = account.balance or Decimal("0")
            account.balance = current_balance + line.debit_amount - line.credit_amount

    entry.status = "posted"
    db.commit()
    db.refresh(entry)
    return entry


@router.post("/{entry_id}/reverse", response_model=JournalEntryResponse, status_code=201)
async def reverse_journal(
    entry_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Create a reversing entry for a posted journal entry."""
    ctx = await get_current_user(credentials)
    original = db.query(JournalEntry).filter(
        JournalEntry.id == entry_id, JournalEntry.agency_id == ctx.agency_id
    ).first()
    if not original:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    if original.status != "posted":
        raise HTTPException(status_code=400, detail="Only posted entries can be reversed")

    # Create reversing entry
    reversing = JournalEntry(
        agency_id=original.agency_id,
        client_id=original.client_id,
        posting_period_id=original.posting_period_id,
        entry_number=_generate_entry_number(),
        entry_date=datetime.now(timezone.utc),
        description=f"Reversal of {original.entry_number}: {original.description}",
        debit_total=original.credit_total,
        credit_total=original.debit_total,
        status="posted",
        is_balanced=True,
    )
    db.add(reversing)
    db.flush()

    # Create reversed lines (swap debit/credit)
    for line in original.lines:
        reversed_line = JournalEntryLine(
            entry_id=reversing.id,
            account_id=line.account_id,
            debit_amount=line.credit_amount,
            credit_amount=line.debit_amount,
            description=f"Reversal: {line.description or ''}",
            line_number=line.line_number,
        )
        db.add(reversed_line)

        # Update account balances
        account = db.query(Account).filter(Account.id == line.account_id).first()
        if account:
            current_balance = account.balance or Decimal("0")
            account.balance = current_balance + line.credit_amount - line.debit_amount

    original.status = "reversed"
    original.reversed_by = reversing.id
    db.commit()
    db.refresh(reversing)
    return reversing
