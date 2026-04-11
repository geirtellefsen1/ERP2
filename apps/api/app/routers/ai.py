"""
AI Processing Layer — Claude API for:
- GL Coding: suggest account codes for transactions
- Anomaly Detection: flag unusual patterns
- Narrative Reports: generate monthly management narratives
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, literal_column
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import httpx, json
from app.database import get_db
from app.models import Transaction, JournalEntry, JournalLine, Account, Invoice, Client
from app.auth import AuthUser, get_current_user
from app.config import get_settings

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])
settings = get_settings()


# ─── Schemas ──────────────────────────────────────────────────────────────────

class GLCodingRequest(BaseModel):
    description: str
    amount: Decimal
    client_id: int


class GLCodingResponse(BaseModel):
    suggested_account_id: int | None
    suggested_account_code: str | None
    suggested_account_name: str | None
    confidence: float
    alternatives: list[dict]
    reasoning: str


class AnomalyAlert(BaseModel):
    transaction_id: int | None
    journal_entry_id: int | None
    type: str  # amount Spike, unusual_timing, duplicate, category_mismatch
    severity: str  # low, medium, high
    description: str
    amount: Decimal | None


class NarrativeRequest(BaseModel):
    client_id: int
    year: int
    month: int


class NarrativeResponse(BaseModel):
    client_id: int
    period: str
    narrative: str
    key_themes: list[str]
    risks: list[str]
    generated_at: datetime


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def call_claude(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 1024,
) -> str:
    """Make a Claude API call and return the response text."""
    if not settings.claude_api_key:
        raise HTTPException(status_code=501, detail="Claude API not configured")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.claude_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": max_tokens,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_message}],
                },
            )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Claude API error: {resp.status_code} {resp.text[:200]}",
                )
            data = resp.json()
            return data["content"][0]["text"]
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Claude API timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claude API error: {e}")


# ─── GL Coding ────────────────────────────────────────────────────────────────

@router.post("/gl-code", response_model=GLCodingResponse)
async def suggest_gl_code(
    data: GLCodingRequest,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    Use Claude to suggest the best GL account code for a transaction description.
    Returns top 3 suggestions with confidence scores.
    """
    # Get client's chart of accounts
    accounts = db.query(Account).filter(
        Account.client_id == data.client_id,
        Account.is_active == True,
    ).all()

    if not accounts:
        raise HTTPException(status_code=404, detail="No accounts found for this client")

    account_list = "\n".join([
        f'- Code {a.code}: {a.name} ({a.account_type})' + (f' - subtype: {a.sub_type}' if a.sub_type else '')
        for a in accounts
    ])

    prompt = f"""A transaction was recorded:
- Description: "{data.description}"
- Amount: {data.amount} (positive = income/debit, negative = expense/credit)

Available GL accounts for this client:
{account_list}

Based ONLY on the transaction description and amount, suggest the most appropriate GL account(s).
Respond ONLY with valid JSON:
{{
  "primary_suggestion": {{"code": "XXXX", "name": "Account Name", "confidence": 0.0 to 1.0, "reasoning": "brief explanation"}},
  "alternatives": [
    {{"code": "YYYY", "name": "Account Name", "confidence": 0.0 to 1.0, "reasoning": "brief explanation"}}
  ]
}}"""

    response = await call_claude(
        system_prompt="You are a GL coding assistant. Suggest the most appropriate general ledger account codes for transactions.",
        user_message=prompt,
        max_tokens=400,
    )

    # Parse JSON
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        result = json.loads(response[start:end])
    except Exception:
        return GLCodingResponse(
            suggested_account_id=None,
            suggested_account_code=None,
            suggested_account_name=None,
            confidence=0,
            alternatives=[],
            reasoning=f"Could not parse Claude response: {response[:200]}",
        )

    # Map codes to IDs
    code_to_account = {a.code: a for a in accounts}
    primary = result.get("primary_suggestion", {})
    primary_account = code_to_account.get(primary.get("code", ""))

    alternatives = []
    for alt in result.get("alternatives", []):
        alt_account = code_to_account.get(alt.get("code", ""))
        if alt_account:
            alternatives.append({
                "account_id": alt_account.id,
                "code": alt_account.code,
                "name": alt_account.name,
                "confidence": alt.get("confidence", 0),
                "reasoning": alt.get("reasoning", ""),
            })

    return GLCodingResponse(
        suggested_account_id=primary_account.id if primary_account else None,
        suggested_account_code=primary.get("code"),
        suggested_account_name=primary.get("name"),
        confidence=primary.get("confidence", 0),
        alternatives=alternatives,
        reasoning=primary.get("reasoning", ""),
    )


# ─── Anomaly Detection ────────────────────────────────────────────────────────

@router.get("/anomalies", response_model=list[AnomalyAlert])
async def detect_anomalies(
    client_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    Scan recent journal entries for anomalies:
    - Amount spikes (> 3x average)
    - Unusual timing (weekends/holidays)
    - Duplicate entries
    - Category mismatches
    """
    # Verify access
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.agency_id == current_user.agency_id,
    ).first()
    if not client:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get recent transactions
    thirty_days_ago = datetime.now() - timedelta(days=30)
    transactions = (
        db.query(JournalLine, JournalEntry)
        .join(JournalEntry, JournalEntry.id == JournalLine.entry_id)
        .filter(
            JournalEntry.client_id == client_id,
            JournalEntry.entry_date >= thirty_days_ago,
            JournalEntry.is_reversal == False,
        )
        .all()
    )

    alerts = []
    amounts = [float(abs(ln.debit or ln.credit)) for ln, _ in transactions if (ln.debit or ln.credit)]
    avg_amount = sum(amounts) / len(amounts) if amounts else 1
    max_amount = max(amounts) if amounts else 1

    for ln, entry in transactions:
        amount = float(abs(ln.debit or ln.credit))

        # Amount spike: > 3x average
        if avg_amount > 0 and amount > avg_amount * 3:
            alerts.append(AnomalyAlert(
                journal_entry_id=entry.id,
                type="amount_spike",
                severity="high" if amount > max_amount * 0.9 else "medium",
                description=f"Amount {amount} is {amount/avg_amount:.1f}x the 30-day average ({avg_amount:.2f})",
                amount=Decimal(str(amount)),
            ))

        # Weekend transaction
        if entry.entry_date.weekday() >= 5:
            alerts.append(AnomalyAlert(
                journal_entry_id=entry.id,
                type="unusual_timing",
                severity="low",
                description=f"Transaction posted on {entry.entry_date.strftime('%A')}",
                amount=Decimal(str(amount)),
            ))

        # Check for duplicate entries (same amount, same date, same account)
        for other_ln, other_entry in transactions:
            if other_ln.id > ln.id:  # only check each pair once
                if (abs(float(ln.debit or 0) - float(other_ln.debit or 0)) < 0.01 and
                    abs((ln.credit or 0) - (other_ln.credit or 0)) < 0.01 and
                    abs((entry.entry_date - other_entry.entry_date).days) == 0 and
                    ln.account_id == other_ln.account_id and
                    ln.id != other_ln.id):
                    alerts.append(AnomalyAlert(
                        journal_entry_id=entry.id,
                        type="duplicate",
                        severity="medium",
                        description=f"Possible duplicate: same amount, date and account as JE #{other_entry.id}",
                        amount=Decimal(str(amount)),
                    ))

    return alerts[:50]  # Cap at 50 alerts


# ─── Narrative Reports ────────────────────────────────────────────────────────

@router.post("/narrative", response_model=NarrativeResponse)
async def generate_narrative(
    data: NarrativeRequest,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    Generate a management narrative report using Claude.
    Analyses the month's financial data and produces a written narrative.
    """
    client = db.query(Client).filter(
        Client.id == data.client_id,
        Client.agency_id == current_user.agency_id,
    ).first()
    if not client:
        raise HTTPException(status_code=403, detail="Access denied")

    period_start = datetime(data.year, data.month, 1)
    if data.month == 12:
        period_end = datetime(data.year + 1, 1, 1) - timedelta(seconds=1)
    else:
        period_end = datetime(data.year, data.month + 1, 1) - timedelta(seconds=1)

    # Get P&L data
    from app.routers.journal import get_period_totals, net_balance
    totals = get_period_totals(db, data.client_id, period_start, period_end)

    revenue = sum(
        abs(net_balance(code, d["account_type"], d["debit"], d["credit"]))
        for code, d in totals.items()
        if d["account_type"] == "revenue"
    )
    expenses = sum(
        abs(net_balance(code, d["account_type"], d["debit"], d["credit"]))
        for code, d in totals.items()
        if d["account_type"] == "expense"
    )
    net_profit = revenue - expenses

    # Top expense categories
    top_expenses = sorted([
        {"code": code, "name": d["name"],
         "amount": abs(net_balance(code, d["account_type"], d["debit"], d["credit"]))}
        for code, d in totals.items()
        if d["account_type"] == "expense"
    ], key=lambda x: x["amount"], reverse=True)[:5]

    # Client info
    period_str = period_start.strftime("%B %Y")

    prompt = f"""Generate a concise monthly management narrative for {client.name} for {period_str}.

Financial Summary:
- Revenue: {client.country} {revenue:,.2f}
- Expenses: {client.country} {expenses:,.2f}
- Net Profit: {client.country} {net_profit:,.2f}

Top 5 Expense Categories:
{chr(10).join([f'- {e["code"]} {e["name"]}: {client.country} {e["amount"]:,.2f}' for e in top_expenses])}

Write a professional 200-300 word management narrative covering:
1. Overall financial performance
2. Key revenue and expense highlights
3. Notable trends or anomalies
4. Areas of concern (if any)
5. Forward look

Respond ONLY with valid JSON:
{{
  "narrative": "full narrative text...",
  "key_themes": ["theme 1", "theme 2"],
  "risks": ["risk 1 or empty array"]
}}"""

    response = await call_claude(
        system_prompt="You are a CFO writing a management narrative. Be professional, concise and factual.",
        user_message=prompt,
        max_tokens=800,
    )

    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        result = json.loads(response[start:end])
    except Exception:
        result = {"narrative": response[:500], "key_themes": [], "risks": []}

    return NarrativeResponse(
        client_id=data.client_id,
        period=period_str,
        narrative=result.get("narrative", response[:500]),
        key_themes=result.get("key_themes", []),
        risks=result.get("risks", []),
        generated_at=datetime.utcnow(),
    )
