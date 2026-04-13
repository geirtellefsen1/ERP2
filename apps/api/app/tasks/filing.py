"""
Statutory filing reminder tasks.

Payroll and VAT filings are due on fixed calendar windows per country.
`check_upcoming_deadlines` runs daily (Beat cron 07:00 UTC) and looks
for open PayrollPeriod rows whose `period_end` is within the reminder
window, logs them, and (in a live deployment) enqueues a delivery task.

We intentionally do NOT fire real filings from this task — statutory
submission must remain a human-confirmed action in the UI. This task
only produces visibility, never actually submits.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from celery import shared_task
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Client, PayrollPeriod

logger = logging.getLogger(__name__)

# How many days ahead we look when raising reminders.
REMINDER_WINDOW_DAYS = 7


def _db_session() -> Session:
    return SessionLocal()


@shared_task(name="app.tasks.filing.check_upcoming_deadlines")
def check_upcoming_deadlines(window_days: int = REMINDER_WINDOW_DAYS) -> dict:
    """
    Find open payroll periods whose period_end falls inside the reminder
    window and return a summary. Caller code (or another task) can use
    that summary to push notifications — we keep this task side-effect
    free so Beat can run it repeatedly with no surprise mutations.
    """
    db = _db_session()
    try:
        now = datetime.now(timezone.utc)
        horizon = now + timedelta(days=window_days)
        rows = (
            db.query(PayrollPeriod, Client)
            .join(Client, PayrollPeriod.client_id == Client.id)
            .filter(
                PayrollPeriod.status == "open",
                PayrollPeriod.period_end >= now,
                PayrollPeriod.period_end <= horizon,
            )
            .all()
        )
        summary = {
            "window_days": window_days,
            "due_count": len(rows),
            "due": [
                {
                    "period_id": p.id,
                    "client_id": c.id,
                    "client_name": c.name,
                    "country": c.country,
                    "period_end": p.period_end.isoformat() if p.period_end else None,
                }
                for p, c in rows
            ],
        }
        logger.info(
            "filing reminder sweep due=%s window_days=%s",
            summary["due_count"],
            window_days,
        )
        return summary
    finally:
        db.close()
