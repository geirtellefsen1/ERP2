"""
Cashflow Forecaster + Narrative Reports — Sprints 20 & 21.
13-week cashflow model + Claude-generated management narrative.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, literal_column
from pydantic import BaseModel
from datetime import datetime, timedelta, date
from decimal import Decimal
import httpx, json
from app.database import get_db
from app.models import JournalEntry, JournalLine, Account, Invoice, Client
from app.auth import AuthUser, get_current_user
from app.config import get_settings

router = APIRouter(prefix="/api/v1/forecast", tags=["forecast"])
settings = get_settings()


@router.get("/cashflow-13week")
def cashflow_13week(
    client_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """
    13-week rolling cashflow forecast.
    Based on actuals up to today + ML/simple projection.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())

    # Get actual cash movements (bank transactions)
    from app.models import BankTransaction
    movements = db.query(
        func.date_trunc("week", BankTransaction.date).label("week"),
        func.sum(BankTransaction.amount).label("total"),
    ).filter(
        BankTransaction.account_id.in_(
            db.query(BankTransaction.account_id).filter(BankTransaction.client_id == client_id).subquery()
        ),
        BankTransaction.date <= today,
    ).group_by("week").all()

    actuals = {m.week.date(): float(m.total or 0) for m in movements}

    # Simple projection: average of last 4 weeks
    avg_weekly = sum(list(actuals.values())[-4:]) / max(len(list(actuals.values())[-4:]), 1)

    # Generate 13-week forecast
    weeks = []
    running_balance = 0  # Starting balance (would come from actual bank balance)

    for i in range(13):
        week_start = start_of_week + timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        if week_start <= today:
            # Use actuals
            weeks.append({
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "actual": actuals.get(week_start, 0),
                "forecast": actuals.get(week_start, 0),
                "type": "actual",
            })
            running_balance += actuals.get(week_start, 0)
        else:
            projected = avg_weekly
            weeks.append({
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "actual": None,
                "forecast": round(projected, 2),
                "type": "forecast",
            })
            running_balance += projected

    return {
        "client_id": client_id,
        "generated_at": datetime.utcnow().isoformat(),
        "weeks": weeks,
        "ending_balance": round(running_balance, 2),
        "method": "simple_average",
    }


@router.get("/narrative-report")
async def generate_narrative_report(
    client_id: int = Query(...),
    year: int = Query(default_factory=lambda: datetime.now().year),
    month: int = Query(default_factory=lambda: datetime.now().month),
    db: Session = Depends(get_db),
):
    """
    Generate a management narrative report using Claude Opus.
    Analyses P&L, balance sheet and cashflow data.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Get financial data
    period_start = datetime(year, month, 1)
    if month == 12:
        period_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        period_end = datetime(year, month + 1, 1) - timedelta(seconds=1)

    from app.routers.journal import get_period_totals, net_balance
    totals = get_period_totals(db, client_id, period_start, period_end)

    revenue = sum(
        abs(net_balance(code, d["account_type"], d["debit"], d["credit"]))
        for code, d in totals.items() if d["account_type"] == "revenue"
    )
    expenses = sum(
        abs(net_balance(code, d["account_type"], d["debit"], d["credit"]))
        for code, d in totals.items() if d["account_type"] == "expense"
    )
    net_profit = revenue - expenses

    # Get balance sheet data
    from app.routers.journal import get_type_total
    assets = get_type_total(db, client_id, "asset", datetime(2000,1,1), period_end)
    liabilities = get_type_total(db, client_id, "liability", datetime(2000,1,1), period_end)

    # Get recent anomalies
    from app.routers.ai import detect_anomalies
    # (Would call detect_anomalies here in production)

    prompt = f"""
Generate a comprehensive monthly management report for {client.name} ({client.country}) for {period_start.strftime('%B %Y')}.

FINANCIAL HIGHLIGHTS:
- Revenue: {client.country} {float(revenue):,.2f}
- Expenses: {client.country} {float(expenses):,.2f}
- Net Profit: {client.country} {float(net_profit):,.2f}
- Total Assets: {client.country} {float(assets):,.2f}
- Total Liabilities: {client.country} {float(liabilities):,.2f}

Write a professional 400-500 word management narrative covering:
1. Executive Summary (2-3 sentences)
2. Financial Performance vs prior period
3. Key Revenue Drivers
4. Cost Analysis & Efficiency
5. Balance Sheet Health
6. Outlook & Recommendations

Respond ONLY with this JSON structure:
{{
  "executive_summary": "...",
  "financial_highlights": {{"revenue": "...", "expenses": "...", "net_profit": "..."}},
  "key_themes": ["theme 1", "theme 2", "theme 3"],
  "risks": ["risk 1", "risk 2"],
  "recommendations": ["rec 1", "rec 2"],
  "outlook": "...",
  "next_month_focus": "..."
}}
"""

    if not settings.claude_api_key:
        return {
            "period": period_start.strftime("%B %Y"),
            "error": "Claude API not configured",
            "financials": {
                "revenue": float(revenue),
                "expenses": float(expenses),
                "net_profit": float(net_profit),
            }
        }

    try:
        async with httpx.AsyncClient(timeout=60.0) as http:
            resp = await http.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.claude_api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": "claude-opus-4-20250514",
                    "max_tokens": 1500,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data["content"][0]["text"]
                start = content.find("{")
                end = content.rfind("}") + 1
                result = json.loads(content[start:end])
                return {
                    "period": period_start.strftime("%B %Y"),
                    "client": client.name,
                    "generated_at": datetime.utcnow().isoformat(),
                    **result,
                }
    except Exception as e:
        return {"period": period_start.strftime("%B %Y"), "error": str(e)}
