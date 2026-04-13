"""
Cashflow refresh tasks.

`refresh_client` re-runs the 13-week forecaster for a single client and
stores a fresh CashflowSnapshot row. `refresh_all_clients` fans out
across every active client and is scheduled by Beat each morning.

This task is intentionally lean: it only COUNTS clients that would be
refreshed in a full production run. The actual forecasting call needs
live AR/AP/payroll data, which Tier 5 does not yet wire into a task
pipeline — the UI calls the forecaster directly. When that pipeline
lands, flesh out the body below; the Beat schedule and task names
should not change.
"""
from __future__ import annotations

import logging

from celery import shared_task
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Client

logger = logging.getLogger(__name__)


def _db_session() -> Session:
    return SessionLocal()


@shared_task(name="app.tasks.cashflow.refresh_all_clients")
def refresh_all_clients() -> dict:
    """
    Fan-out stub: count active clients and log. In production this will
    enqueue one `refresh_client` task per client — leaving it as a count
    now so the Beat cron is exercised by tests without pulling the full
    forecasting pipeline into the task layer.
    """
    db = _db_session()
    try:
        count = db.query(Client).filter(Client.is_active.is_(True)).count()
        logger.info("cashflow refresh sweep clients=%s", count)
        return {"active_clients": count, "dispatched": 0}
    finally:
        db.close()
