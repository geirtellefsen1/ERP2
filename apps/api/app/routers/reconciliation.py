from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db.session import get_db
from app.auth.middleware import get_current_user, security
from app.models.bank_feed import BankTransaction
from app.models.transaction import Transaction
from app.schemas.bank_feed import (
    AutoMatchResponse,
    MatchSuggestionsResponse,
    MatchSuggestion,
    ConfirmMatchRequest,
    ConfirmMatchResponse,
    ExcludeRequest,
    ExcludeResponse,
)

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])


@router.post("/auto-match", response_model=AutoMatchResponse)
async def auto_match(
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Auto-match bank transactions to journal entries by amount and date."""
    ctx = await get_current_user(credentials)

    unmatched = (
        db.query(BankTransaction)
        .filter(
            BankTransaction.agency_id == ctx.agency_id,
            BankTransaction.match_status == "unmatched",
        )
        .all()
    )

    matched_pairs = []
    for bank_txn in unmatched:
        # Look for transactions with same amount within 3-day window
        candidates = (
            db.query(Transaction)
            .filter(
                Transaction.agency_id == ctx.agency_id,
                Transaction.client_id == bank_txn.client_id,
                Transaction.amount == bank_txn.amount,
                Transaction.matched == False,  # noqa: E712
                Transaction.transaction_date >= bank_txn.transaction_date - timedelta(days=3),
                Transaction.transaction_date <= bank_txn.transaction_date + timedelta(days=3),
            )
            .first()
        )

        if candidates:
            bank_txn.match_status = "matched"
            bank_txn.matched_transaction_id = candidates.id
            candidates.matched = True
            matched_pairs.append({
                "bank_transaction_id": bank_txn.id,
                "transaction_id": candidates.id,
                "amount": float(bank_txn.amount),
            })

    db.commit()

    return AutoMatchResponse(
        matches_found=len(matched_pairs),
        matched_pairs=matched_pairs,
    )


@router.get("/suggestions", response_model=MatchSuggestionsResponse)
async def get_suggestions(
    bank_transaction_id: int = Query(..., description="Bank transaction ID to get suggestions for"),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get match suggestions for a bank transaction."""
    ctx = await get_current_user(credentials)

    bank_txn = db.query(BankTransaction).filter(
        BankTransaction.id == bank_transaction_id,
        BankTransaction.agency_id == ctx.agency_id,
    ).first()
    if not bank_txn:
        raise HTTPException(status_code=404, detail="Bank transaction not found")

    # Find potential matches within 7 days and similar amount (within 10%)
    amount = float(bank_txn.amount)
    tolerance = abs(amount * 0.1) if amount != 0 else 1.0
    candidates = (
        db.query(Transaction)
        .filter(
            Transaction.agency_id == ctx.agency_id,
            Transaction.client_id == bank_txn.client_id,
            Transaction.matched == False,  # noqa: E712
            Transaction.amount.between(amount - tolerance, amount + tolerance),
            Transaction.transaction_date >= bank_txn.transaction_date - timedelta(days=7),
            Transaction.transaction_date <= bank_txn.transaction_date + timedelta(days=7),
        )
        .limit(10)
        .all()
    )

    suggestions = []
    for txn in candidates:
        date_diff = abs((txn.transaction_date - bank_txn.transaction_date).days)
        amount_diff = abs(float(txn.amount) - amount)
        # Confidence: 1.0 if exact match on amount and date, decreasing otherwise
        confidence = 1.0 - (date_diff * 0.05) - (amount_diff / max(abs(amount), 1) * 0.3)
        confidence = max(0.0, min(1.0, confidence))

        suggestions.append(MatchSuggestion(
            bank_transaction_id=bank_txn.id,
            suggested_transaction_id=txn.id,
            confidence=round(confidence, 2),
            amount=float(txn.amount),
            date_diff_days=date_diff,
        ))

    suggestions.sort(key=lambda s: s.confidence, reverse=True)

    return MatchSuggestionsResponse(
        bank_transaction_id=bank_txn.id,
        suggestions=suggestions,
    )


@router.post("/confirm", response_model=ConfirmMatchResponse)
async def confirm_match(
    data: ConfirmMatchRequest,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Confirm a match between a bank transaction and a system transaction."""
    ctx = await get_current_user(credentials)

    bank_txn = db.query(BankTransaction).filter(
        BankTransaction.id == data.bank_transaction_id,
        BankTransaction.agency_id == ctx.agency_id,
    ).first()
    if not bank_txn:
        raise HTTPException(status_code=404, detail="Bank transaction not found")

    txn = db.query(Transaction).filter(
        Transaction.id == data.transaction_id,
        Transaction.agency_id == ctx.agency_id,
    ).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    bank_txn.match_status = "matched"
    bank_txn.matched_transaction_id = txn.id
    txn.matched = True
    db.commit()

    return ConfirmMatchResponse(
        bank_transaction_id=bank_txn.id,
        transaction_id=txn.id,
        status="matched",
        message="Match confirmed successfully",
    )


@router.post("/exclude", response_model=ExcludeResponse)
async def exclude_transaction(
    data: ExcludeRequest,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Mark a bank transaction as excluded from reconciliation."""
    ctx = await get_current_user(credentials)

    bank_txn = db.query(BankTransaction).filter(
        BankTransaction.id == data.bank_transaction_id,
        BankTransaction.agency_id == ctx.agency_id,
    ).first()
    if not bank_txn:
        raise HTTPException(status_code=404, detail="Bank transaction not found")

    bank_txn.match_status = "excluded"
    bank_txn.matched_transaction_id = None
    db.commit()

    return ExcludeResponse(
        bank_transaction_id=bank_txn.id,
        status="excluded",
        message="Bank transaction excluded from reconciliation",
    )
