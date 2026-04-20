"""
Professional Services Module — Sprint 19.
Time tracking, trust accounts, WIP billing.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from app.database import get_db
from app.models import Matter, TimeEntry, TrustTransaction, Client
from app.auth import AuthUser, get_current_user

router = APIRouter(prefix="/api/v1/services", tags=["services"])


@router.get("/matters", response_model=list)
def list_matters(client_id: int = Query(...), db: Session = Depends(get_db)):
    return db.query(Matter).filter(Matter.client_id == client_id).all()


@router.post("/matters", response_model=dict, status_code=201)
def create_matter(
    client_id: int = Query(...),
    title: str = Query(...),
    type: str = Query(...),
    rate_type: str = Query("hourly"),
    db: Session = Depends(get_db),
):
    import uuid
    matter = Matter(
        client_id=client_id,
        matter_number=f"M-{uuid.uuid4().hex[:8].upper()}",
        title=title,
        type=type,
        rate_type=rate_type,
    )
    db.add(matter); db.commit(); db.refresh(matter)
    return {"id": matter.id, "matter_number": matter.matter_number, "title": matter.title}


@router.post("/time-entries", response_model=dict, status_code=201)
def log_time(
    matter_id: int = Query(...),
    employee_id: int = Query(...),
    date: datetime = Query(...),
    hours: Decimal = Query(...),
    rate: Decimal = Query(...),
    description: str = Query(""),
    db: Session = Depends(get_db),
):
    entry = TimeEntry(
        matter_id=matter_id,
        employee_id=employee_id,
        date=date,
        hours=hours,
        rate=rate,
        description=description,
    )
    db.add(entry); db.commit(); db.refresh(entry)
    return {"id": entry.id, "value": float(hours * rate)}


@router.get("/wip", response_model=list)
def get_wip(
    client_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Work in Progress — unbilled time entries per matter."""
    from sqlalchemy import func
    results = db.query(
        Matter.matter_number,
        Matter.title,
        func.sum(TimeEntry.hours * TimeEntry.rate).label("wip_value"),
        func.sum(TimeEntry.hours).label("total_hours"),
    ).join(Matter, TimeEntry.matter_id == Matter.id).filter(
        Matter.client_id == client_id,
        TimeEntry.invoiced == False,
    ).group_by(Matter.id).all()

    return [
        {
            "matter_number": r.matter_number,
            "title": r.title,
            "wip_value": float(r.wip_value or 0),
            "total_hours": float(r.total_hours or 0),
        }
        for r in results
    ]


@router.get("/trust-account/{matter_id}")
def get_trust_balance(matter_id: int, db: Session = Depends(get_db)):
    """Get trust account balance for a matter."""
    from sqlalchemy import func
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")

    deposits = db.query(func.sum(TrustTransaction.amount)).filter(
        TrustTransaction.matter_id == matter_id,
        TrustTransaction.transaction_type == "deposit",
    ).scalar() or Decimal("0")

    withdrawals = db.query(func.sum(TrustTransaction.amount)).filter(
        TrustTransaction.matter_id == matter_id,
        TrustTransaction.transaction_type == "withdrawal",
    ).scalar() or Decimal("0")

    return {
        "matter_id": matter_id,
        "trust_account": matter.trust_account or "N/A",
        "deposits": float(deposits),
        "withdrawals": float(withdrawals),
        "balance": float(deposits - withdrawals),
    }


@router.post("/trust-account/{matter_id}/deposit")
def trust_deposit(
    matter_id: int,
    amount: Decimal = Query(...),
    reference: str = Query(""),
    db: Session = Depends(get_db),
):
    tx = TrustTransaction(
        matter_id=matter_id,
        transaction_type="deposit",
        amount=amount,
        reference=reference,
    )
    db.add(tx); db.commit()
    return {"id": tx.id, "type": "deposit", "amount": float(amount)}
