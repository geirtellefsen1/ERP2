from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Any


def generate_13_week_forecast(
    client_id: int,
    opening_balance: float,
    avg_weekly_receipts: float,
    avg_weekly_payments: float,
) -> List[Dict[str, Any]]:
    """Generate a 13-week cashflow forecast.

    Each week:
    - opening = previous week's closing (first week uses opening_balance)
    - receipts = avg_weekly_receipts
    - payments = avg_weekly_payments
    - closing = opening + receipts - payments
    - alert_flag = True if closing < 0 or closing < opening * 0.1
    """
    lines = []
    today = date.today()
    # Start from next Monday
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    start_date = today + timedelta(days=days_until_monday)

    current_opening = Decimal(str(opening_balance))
    receipts = Decimal(str(avg_weekly_receipts))
    payments = Decimal(str(avg_weekly_payments))

    for week in range(13):
        week_commencing = start_date + timedelta(weeks=week)
        closing = current_opening + receipts - payments
        alert_flag = closing < 0 or closing < current_opening * Decimal("0.1")

        lines.append({
            "week_commencing": week_commencing,
            "opening_balance": float(current_opening),
            "receipts": float(receipts),
            "payments": float(payments),
            "closing_balance": float(closing),
            "alert_flag": alert_flag,
        })

        current_opening = closing

    return lines


def detect_alerts(forecast_lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect alerts from forecast lines.

    - Negative balance -> critical severity
    - Low balance < 50000 -> warning severity
    - >20% drop week-over-week -> info/volatility
    """
    alerts = []

    for i, line in enumerate(forecast_lines):
        closing = Decimal(str(line["closing_balance"]))
        week_number = i + 1

        # Critical: negative balance
        if closing < 0:
            alerts.append({
                "alert_type": "negative",
                "severity": "critical",
                "week_number": week_number,
                "narrative": generate_alert_narrative("negative", week_number, float(closing)),
            })

        # Warning: low balance (< 50000)
        elif closing < 50000:
            alerts.append({
                "alert_type": "low_balance",
                "severity": "warning",
                "week_number": week_number,
                "narrative": generate_alert_narrative("low_balance", week_number, float(closing)),
            })

        # Info: >20% drop week-over-week
        if i > 0:
            prev_closing = Decimal(str(forecast_lines[i - 1]["closing_balance"]))
            if prev_closing > 0:
                drop_pct = (prev_closing - closing) / prev_closing
                if drop_pct > Decimal("0.2"):
                    alerts.append({
                        "alert_type": "volatility",
                        "severity": "info",
                        "week_number": week_number,
                        "narrative": generate_alert_narrative("volatility", week_number, float(closing)),
                    })

    return alerts


def generate_alert_narrative(alert_type: str, week_number: int, balance: float) -> str:
    """Generate a plain-text alert message."""
    balance_formatted = f"{balance:,.2f}"

    if alert_type == "negative":
        return (
            f"Critical: Projected negative balance of {balance_formatted} "
            f"in week {week_number}. Immediate action required to avoid cash shortfall."
        )
    elif alert_type == "low_balance":
        return (
            f"Warning: Projected low balance of {balance_formatted} "
            f"in week {week_number}. Consider accelerating receivables or deferring payments."
        )
    elif alert_type == "volatility":
        return (
            f"Info: Significant balance drop detected in week {week_number} "
            f"(closing balance: {balance_formatted}). Review payment schedule for potential smoothing."
        )
    else:
        return f"Alert in week {week_number}: balance is {balance_formatted}."
