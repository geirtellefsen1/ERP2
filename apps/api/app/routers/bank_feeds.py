from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import uuid

from app.db.session import get_db
from app.auth.middleware import get_current_user, security
from app.models import Client
from app.models.bank_feed import BankConnection, BankTransaction
from app.schemas.bank_feed import (
    BankConnectionCreate,
    BankConnectionResponse,
    BankTransactionResponse,
    BankSyncRequest,
    BankSyncResponse,
)

router = APIRouter(prefix="/bank-feeds", tags=["bank-feeds"])


@router.post("/connections", response_model=BankConnectionResponse, status_code=201)
async def create_connection(
    data: BankConnectionCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Create a new bank connection."""
    ctx = await get_current_user(credentials)

    client = db.query(Client).filter(
        Client.id == data.client_id, Client.agency_id == ctx.agency_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    connection = BankConnection(
        agency_id=ctx.agency_id,
        client_id=data.client_id,
        provider=data.provider,
        bank_name=data.bank_name,
        account_number_masked=data.account_number_masked,
        status="connected",
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)
    return connection


@router.get("/connections", response_model=list[BankConnectionResponse])
async def list_connections(
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List bank connections for the agency."""
    ctx = await get_current_user(credentials)

    connections = (
        db.query(BankConnection)
        .filter(BankConnection.agency_id == ctx.agency_id)
        .order_by(BankConnection.created_at.desc())
        .all()
    )
    return connections


@router.post("/sync", response_model=BankSyncResponse)
async def sync_transactions(
    data: BankSyncRequest,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Simulate importing bank transactions from a bank feed."""
    ctx = await get_current_user(credentials)

    connection = db.query(BankConnection).filter(
        BankConnection.id == data.connection_id,
        BankConnection.agency_id == ctx.agency_id,
    ).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Bank connection not found")

    # Generate sample transactions
    now = datetime.now(timezone.utc)
    sample_txns = [
        {"desc": "POS Purchase - Woolworths", "amount": Decimal("-450.00")},
        {"desc": "EFT Payment Received", "amount": Decimal("12500.00")},
        {"desc": "Debit Order - Insurance", "amount": Decimal("-1200.00")},
        {"desc": "ATM Withdrawal", "amount": Decimal("-500.00")},
        {"desc": "Salary Deposit", "amount": Decimal("35000.00")},
    ]

    imported = 0
    for i, txn in enumerate(sample_txns):
        ext_id = f"{connection.id}-{uuid.uuid4().hex[:12]}"
        bank_txn = BankTransaction(
            agency_id=ctx.agency_id,
            client_id=connection.client_id,
            bank_connection_id=connection.id,
            external_id=ext_id,
            transaction_date=now - timedelta(days=i),
            description=txn["desc"],
            amount=txn["amount"],
            currency="ZAR",
            match_status="unmatched",
        )
        db.add(bank_txn)
        imported += 1

    connection.last_synced_at = now
    db.commit()

    return BankSyncResponse(
        connection_id=connection.id,
        transactions_imported=imported,
        message=f"Successfully imported {imported} transactions",
    )


@router.get("/transactions", response_model=list[BankTransactionResponse])
async def list_transactions(
    match_status: str = Query(None, description="Filter by match status: unmatched, matched, excluded"),
    connection_id: int = Query(None, description="Filter by bank connection ID"),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List bank transactions with optional match_status filter."""
    ctx = await get_current_user(credentials)

    query = db.query(BankTransaction).filter(
        BankTransaction.agency_id == ctx.agency_id
    )
    if match_status:
        query = query.filter(BankTransaction.match_status == match_status)
    if connection_id:
        query = query.filter(BankTransaction.bank_connection_id == connection_id)

    transactions = query.order_by(BankTransaction.transaction_date.desc()).all()
    return transactions
