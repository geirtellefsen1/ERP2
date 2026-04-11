"""
Bank Reconciliation — bank accounts, transaction import,
Open Banking (TrueLayer) integration, AI-powered matching.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
import csv, io, httpx
from app.database import get_db
from app.models import BankAccount, BankTransaction, Invoice, Transaction, JournalEntry, JournalLine, Account
from app.auth import AuthUser, get_current_user
from app.config import get_settings

router = APIRouter(prefix="/api/v1/banking", tags=["banking"])
settings = get_settings()

# ─── Schemas ──────────────────────────────────────────────────────────────────

class BankAccountCreate(BaseModel):
    client_id: int
    bank_name: str = Field(max_length=100)
    account_number: str = Field(max_length=50)
    account_type: str = Field(default="checking", pattern=r"^(checking|savings)$")
    currency: str = Field(default="ZAR", max_length=3)


class BankAccountOut(BaseModel):
    id: int; client_id: int; bank_name: str; account_number: str
    account_type: str; currency: str; is_active: bool
    class Config: from_attributes = True


class MatchRequest(BaseModel):
    transaction_ids: list[int]
    match_type: str = Field(pattern=r"^(invoice|journal)$")
    invoice_id: int | None = None
    journal_line_id: int | None = None


class ReconcileResponse(BaseModel):
    transaction_id: int
    status: str
    confidence: float
    reason: str
    suggested_invoice_id: int | None = None


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def call_claude_for_match(
    transaction_description: str,
    transaction_amount: Decimal,
    transaction_date: datetime,
    pending_invoices: list,
    pending_journals: list,
) -> dict:
    """
    Call Claude API to suggest the best match for a bank transaction.
    Returns: { match_type, match_id, confidence, reason }
    """
    if not settings.claude_api_key:
        return {"match_type": None, "match_id": None, "confidence": 0, "reason": "Claude API not configured"}

    prompt = f"""
You are a bank reconciliation AI. A bank transaction was received:
- Description: "{transaction_description}"
- Amount: {transaction_amount} (positive = money in, negative = money out)
- Date: {transaction_date.strftime('%Y-%m-%d')}

Available invoices to match against:
{chr(10).join([f'- Invoice #{inv.id}: {inv.invoice_number}, amount={inv.amount}, status={inv.status}' for inv in pending_invoices[:10]])}

Available journal entries (unpaid):
{chr(10).join([f'- JE #{je.id}: {je.description}, date={je.entry_date.strftime("%Y-%m-%d")}' for je in pending_journals[:5]])}

Respond ONLY with valid JSON:
{{
  "match_type": "invoice" | "journal" | null,
  "match_id": integer | null,
  "confidence": 0.0 to 1.0,
  "reason": "brief explanation"
}}
"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.claude_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 200,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                import json as _json
                content = data["content"][0]["text"]
                # Extract JSON from response
                start = content.find("{")
                end = content.rfind("}") + 1
                return _json.loads(content[start:end])
    except Exception:
        pass
    return {"match_type": None, "match_id": None, "confidence": 0, "reason": "AI unavailable"}


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/accounts", response_model=BankAccountOut, status_code=201)
def create_bank_account(
    data: BankAccountCreate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    from app.models import Client
    client = db.query(Client).filter(
        Client.id == data.client_id,
        Client.agency_id == current_user.agency_id,
    ).first()
    if not client:
        raise HTTPException(status_code=403, detail="Client not found")
    acct = BankAccount(**data.model_dump())
    db.add(acct); db.commit(); db.refresh(acct)
    return acct


@router.get("/accounts", response_model=list[BankAccountOut])
def list_bank_accounts(client_id: int = Query(...), db: Session = Depends(get_db)):
    return db.query(BankAccount).filter(BankAccount.client_id == client_id).all()


@router.post("/accounts/{account_id}/import-csv")
async def import_transactions_csv(
    account_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Import bank transactions from CSV. Columns: date, description, amount, reference"""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be CSV")
    content = await file.read()
    try:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    except UnicodeError:
        raise HTTPException(status_code=400, detail="Invalid encoding — use UTF-8")

    account = db.query(BankAccount).filter(BankAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")

    imported = []
    for row in reader:
        date_str = row.get("date", "").strip()
        description = row.get("description", "").strip()
        amount_str = row.get("amount", "").strip().replace(",", "")
        reference = row.get("reference", "").strip() or None

        try:
            tx_date = datetime.fromisoformat(date_str.replace("/", "-"))
        except ValueError:
            continue

        try:
            amount = Decimal(amount_str)
        except Exception:
            continue

        existing = db.query(BankTransaction).filter(
            BankTransaction.account_id == account_id,
            BankTransaction.external_id == reference,
        ).first()
        if existing:
            continue

        tx = BankTransaction(
            account_id=account_id,
            external_id=reference,
            date=tx_date,
            description=description,
            amount=amount,
            reference=reference,
        )
        db.add(tx)
        imported.append(reference or str(tx_date))

    db.commit()
    return {"imported": len(imported), "references": imported[:20]}


@router.post("/accounts/{account_id}/reconcile")
async def reconcile_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    Run AI-powered reconciliation on all unmatched transactions for an account.
    Matches against unpaid invoices and open journal entries.
    """
    account = db.query(BankAccount).filter(BankAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")

    from app.models import Client
    client = db.query(Client).filter(
        Client.id == account.client_id,
        Client.agency_id == current_user.agency_id,
    ).first()
    if not client:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get unmatched transactions
    unmatched = db.query(BankTransaction).filter(
        BankTransaction.account_id == account_id,
        BankTransaction.status == "unmatched",
    ).all()

    # Get pending invoices
    pending_invoices = db.query(Invoice).filter(
        Invoice.client_id == account.client_id,
        Invoice.status.in_(["sent", "overdue"]),
    ).all()

    # Get open journals
    pending_journals = db.query(JournalEntry).filter(
        JournalEntry.client_id == account.client_id,
    ).all()

    results = []
    for tx in unmatched:
        ai_result = await call_claude_for_match(
            tx.description or "",
            tx.amount,
            tx.date,
            pending_invoices,
            pending_journals,
        )
        tx.match_confidence = Decimal(str(ai_result.get("confidence", 0)))
        tx.match_reason = ai_result.get("reason")
        if ai_result.get("match_type") == "invoice":
            tx.matched_invoice_id = ai_result.get("match_id")
            tx.status = "matched"
        elif ai_result.get("match_type") == "journal":
            tx.matched_journal_line_id = ai_result.get("match_id")
            tx.status = "matched"
        results.append(ReconcileResponse(
            transaction_id=tx.id,
            status=tx.status,
            confidence=float(tx.match_confidence or 0),
            reason=tx.match_reason or "",
            suggested_invoice_id=tx.matched_invoice_id,
        ))

    db.commit()
    return {
        "account_id": account_id,
        "reconciled": len(results),
        "results": results,
    }


@router.post("/match")
async def match_transactions(
    data: MatchRequest,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Manually match transactions to invoices or journal lines."""
    updated = []
    for tx_id in data.transaction_ids:
        tx = db.query(BankTransaction).filter(BankTransaction.id == tx_id).first()
        if not tx:
            continue
        if data.match_type == "invoice" and data.invoice_id:
            tx.matched_invoice_id = data.invoice_id
            tx.status = "matched"
            tx.match_confidence = Decimal("1.0")
            tx.match_reason = "Manual match by user"
        elif data.match_type == "journal" and data.journal_line_id:
            tx.matched_journal_line_id = data.journal_line_id
            tx.status = "matched"
            tx.match_confidence = Decimal("1.0")
            tx.match_reason = "Manual match by user"
        updated.append(tx.id)

    db.commit()
    return {"matched": updated}


@router.get("/transactions", response_model=list)
def list_transactions(
    account_id: int = Query(...),
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(BankTransaction).filter(BankTransaction.account_id == account_id)
    if status:
        q = q.filter(BankTransaction.status == status)
    return q.order_by(BankTransaction.date.desc()).offset(skip).limit(limit).all()


# ─── TrueLayer Open Banking (UK/EU) ─────────────────────────────────────────────

@router.get("/providers/{country}")
async def list_providers(country: str):
    """
    List available Open Banking providers for a country.
    UK: uses TrueLayer
    Norway: uses Aiia
    """
    if country == "UK":
        return {
            "providers": [
                {"id": "abricot", "name": "Abricot", "icon": "🍊"},
                {"id": "adsl", "name": "ADS L", "icon": "🏦"},
                {"id": "aeoon", "name": "Aeoon", "icon": "🌍"},
            ]
        }
    return {"providers": []}


@router.post("/accounts/{account_id}/connect-truelayer")
async def connect_truelayer(
    account_id: int,
    db: Session = Depends(get_db),
):
    """
    Generate a TrueLayer Connect Link to connect a bank account.
    After user authorizes, TrueLayer redirects to our callback with a token.
    """
    if not settings.truelayer_client_id:
        raise HTTPException(status_code=501, detail="TrueLayer not configured")

    from urllib.parse import urlencode
    redirect_uri = "http://localhost:8000/api/v1/banking/callback/truelayer"
    params = urlencode({
        "response_type": "code",
        "client_id": settings.truelayer_client_id,
        "redirect_uri": redirect_uri,
        "scope": "accounts transactions",
        "providers": "[\"mock\"]]",
    })
    connect_url = f"https://auth.truelayer.com/connect?{params}"
    return {"connect_url": connect_url, "message": "Redirect user to connect_url"}
