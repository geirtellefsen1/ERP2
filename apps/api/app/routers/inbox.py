"""Inbox router — receipt drop zone + AI extraction + approval flow.

Endpoints:
  POST   /api/v1/inbox/upload     — drag-drop or mobile upload
  GET    /api/v1/inbox            — list items (filter by client/status)
  GET    /api/v1/inbox/{id}       — fetch one item
  POST   /api/v1/inbox/{id}/approve   — convert to a Transaction
  POST   /api/v1/inbox/{id}/reject    — soft-reject with reason
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models import Account, Client, InboxItem, Transaction
from app.services.inbox.extraction import extract_from_filename


router = APIRouter(prefix="/api/v1/inbox", tags=["inbox"])


# --- Schemas -----------------------------------------------------------------


class InboxUploadRequest(BaseModel):
    """A simulated upload — the demo doesn't actually store the file,
    just records the metadata and runs the extractor on the filename."""
    client_id: int
    filename: str
    source: str = "upload"   # upload | email | mobile | ehf


class InboxItemOut(BaseModel):
    id: int
    client_id: Optional[int]
    source: str
    original_filename: Optional[str]
    status: str
    extracted_vendor: Optional[str]
    extracted_date: Optional[str]
    extracted_amount_minor: Optional[int]
    extracted_vat_minor: Optional[int]
    extracted_currency: Optional[str]
    extracted_invoice_number: Optional[str]
    suggested_account_id: Optional[int]
    suggested_account_code: Optional[str]
    suggested_account_name: Optional[str]
    suggested_outlet_type: Optional[str]
    ai_confidence: Optional[float]
    ai_reasoning: Optional[str]
    transaction_id: Optional[int]
    approved_at: Optional[str]
    rejected_at: Optional[str]
    rejection_reason: Optional[str]
    created_at: str


class InboxRejectRequest(BaseModel):
    reason: str


class InboxApproveRequest(BaseModel):
    """Allow the accountant to override AI suggestions before approving."""
    account_id: Optional[int] = None
    amount_minor: Optional[int] = None
    vendor: Optional[str] = None


# --- Helpers -----------------------------------------------------------------


def _ensure_client_visible(
    db: Session, client_id: int, current_user: CurrentUser
) -> Client:
    c = (
        db.query(Client)
        .filter(
            Client.id == client_id,
            Client.agency_id == current_user.agency_id,
        )
        .first()
    )
    if c is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return c


def _serialize(item: InboxItem, db: Session) -> InboxItemOut:
    suggested_account = None
    if item.suggested_account_id:
        suggested_account = (
            db.query(Account).filter(Account.id == item.suggested_account_id).first()
        )
    return InboxItemOut(
        id=item.id,
        client_id=item.client_id,
        source=item.source,
        original_filename=item.original_filename,
        status=item.status,
        extracted_vendor=item.extracted_vendor,
        extracted_date=item.extracted_date.isoformat() if item.extracted_date else None,
        extracted_amount_minor=item.extracted_amount_minor,
        extracted_vat_minor=item.extracted_vat_minor,
        extracted_currency=item.extracted_currency,
        extracted_invoice_number=item.extracted_invoice_number,
        suggested_account_id=item.suggested_account_id,
        suggested_account_code=suggested_account.code if suggested_account else None,
        suggested_account_name=suggested_account.name if suggested_account else None,
        suggested_outlet_type=item.suggested_outlet_type,
        ai_confidence=float(item.ai_confidence) if item.ai_confidence else None,
        ai_reasoning=item.ai_reasoning,
        transaction_id=item.transaction_id,
        approved_at=item.approved_at.isoformat() if item.approved_at else None,
        rejected_at=item.rejected_at.isoformat() if item.rejected_at else None,
        rejection_reason=item.rejection_reason,
        created_at=item.created_at.isoformat(),
    )


# --- Routes ------------------------------------------------------------------


@router.post("/upload", response_model=InboxItemOut)
def upload(
    body: InboxUploadRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record a new inbox item and run the AI extractor on the filename."""
    _ensure_client_visible(db, body.client_id, current_user)

    result = extract_from_filename(body.filename)

    suggested_account_id = None
    if result.suggested_account_code:
        acc = (
            db.query(Account)
            .filter(
                Account.client_id == body.client_id,
                Account.code == result.suggested_account_code,
            )
            .first()
        )
        if acc:
            suggested_account_id = acc.id

    extracted_date_dt = None
    if result.date:
        extracted_date_dt = datetime.combine(
            result.date, datetime.min.time(), tzinfo=timezone.utc
        )

    item = InboxItem(
        agency_id=current_user.agency_id,
        client_id=body.client_id,
        source=body.source,
        original_filename=body.filename,
        status="extracted" if result.vendor else "pending",
        extracted_vendor=result.vendor,
        extracted_date=extracted_date_dt,
        extracted_amount_minor=result.amount_minor,
        extracted_vat_minor=result.vat_minor,
        extracted_currency=result.currency,
        extracted_invoice_number=result.invoice_number,
        suggested_account_id=suggested_account_id,
        suggested_outlet_type=result.suggested_outlet_type,
        ai_confidence=result.confidence,
        ai_reasoning=result.reasoning,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _serialize(item, db)


@router.get("", response_model=list[InboxItemOut])
def list_items(
    client_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List inbox items for the agency, optionally scoped to a client."""
    q = (
        db.query(InboxItem)
        .filter(InboxItem.agency_id == current_user.agency_id)
        .order_by(desc(InboxItem.created_at))
    )
    if client_id is not None:
        q = q.filter(InboxItem.client_id == client_id)
    if status is not None:
        q = q.filter(InboxItem.status == status)

    return [_serialize(i, db) for i in q.limit(limit).all()]


@router.get("/{item_id}", response_model=InboxItemOut)
def get_item(
    item_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(InboxItem)
        .filter(
            InboxItem.id == item_id,
            InboxItem.agency_id == current_user.agency_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Inbox item not found")
    return _serialize(item, db)


@router.post("/{item_id}/approve", response_model=InboxItemOut)
def approve(
    item_id: int,
    body: InboxApproveRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Convert an inbox item to a Transaction and mark it approved.

    The accountant may override AI suggestions in the request body.
    """
    item = (
        db.query(InboxItem)
        .filter(
            InboxItem.id == item_id,
            InboxItem.agency_id == current_user.agency_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Inbox item not found")
    if item.status not in ("pending", "extracted"):
        raise HTTPException(
            status_code=400, detail=f"Cannot approve item in status '{item.status}'"
        )

    amount = body.amount_minor if body.amount_minor is not None else item.extracted_amount_minor
    if amount is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot approve without an amount — provide amount_minor",
        )
    vendor = body.vendor if body.vendor is not None else item.extracted_vendor
    if not item.client_id:
        raise HTTPException(
            status_code=400, detail="Inbox item has no client_id assigned"
        )

    txn = Transaction(
        client_id=item.client_id,
        date=item.extracted_date or datetime.now(timezone.utc),
        description=f"{vendor or 'Manual'} — {item.extracted_invoice_number or 'no inv ref'}",
        amount=Decimal(amount) / Decimal(100),  # store in major units
        reference=item.extracted_invoice_number or f"INBOX-{item.id}",
        matched=False,
    )
    db.add(txn)
    db.flush()

    item.transaction_id = txn.id
    item.status = "approved"
    item.approved_at = datetime.now(timezone.utc)
    item.approved_by_user_id = current_user.id
    db.commit()
    db.refresh(item)
    return _serialize(item, db)


@router.post("/{item_id}/reject", response_model=InboxItemOut)
def reject(
    item_id: int,
    body: InboxRejectRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(InboxItem)
        .filter(
            InboxItem.id == item_id,
            InboxItem.agency_id == current_user.agency_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Inbox item not found")
    if item.status in ("approved", "rejected"):
        raise HTTPException(
            status_code=400, detail=f"Cannot reject item in status '{item.status}'"
        )

    item.status = "rejected"
    item.rejected_at = datetime.now(timezone.utc)
    item.rejection_reason = body.reason
    db.commit()
    db.refresh(item)
    return _serialize(item, db)
