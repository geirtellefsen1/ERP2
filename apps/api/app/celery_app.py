"""
Celery app for background jobs and Beat schedule.

Why Celery and not FastAPI BackgroundTasks?
  - Tier 5 jobs span minutes (bank sync, PDF generation, filing submission)
    and we don't want them tied to a web worker.
  - Beat gives us cron-style scheduling for nightly banking sync,
    monthly filing reminders, and daily report delivery sweeps.
  - Redis is already in the stack for rate limiting, so re-using it as
    the broker/result backend keeps ops simple.

Task locations are discovered via `include=[...]`. Every new task module
has to be added to TASK_MODULES below so it's picked up at worker start.

Tests run tasks in CELERY_TASK_ALWAYS_EAGER mode (see
conftest fixture `celery_eager`), which executes tasks synchronously in
the caller's thread — no broker required.
"""
from __future__ import annotations

import logging
import os

from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Task modules must be listed here so Celery can import them at startup.
TASK_MODULES = [
    "app.tasks.banking",
    "app.tasks.delivery",
    "app.tasks.filing",
    "app.tasks.cashflow",
]


def _make_celery() -> Celery:
    app = Celery(
        "claud_erp",
        broker=settings.redis_url,
        backend=settings.redis_url,
        include=TASK_MODULES,
    )

    app.conf.update(
        # UTC everywhere — Beat schedules, task timestamps, everything.
        timezone="UTC",
        enable_utc=True,
        # Serialization — JSON only; no pickle on the broker.
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        # Visibility timeout for long-running jobs (PDF gen + delivery sweeps)
        broker_transport_options={"visibility_timeout": 3600},
        # Retry policy defaults — individual tasks can override.
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        # Result expiration — we don't need results forever.
        result_expires=3600 * 24,
    )

    # ── Beat schedule ──────────────────────────────────────────────────
    # All times are UTC. Cron windows are chosen so the bank-sync runs
    # BEFORE the morning cashflow refresh (so forecasts see fresh data).
    app.conf.beat_schedule = {
        "banking-sync-nightly": {
            "task": "app.tasks.banking.sync_all_agencies",
            "schedule": crontab(hour=2, minute=0),
            "options": {"queue": "banking"},
        },
        "cashflow-refresh-morning": {
            "task": "app.tasks.cashflow.refresh_all_clients",
            "schedule": crontab(hour=5, minute=0),
            "options": {"queue": "reports"},
        },
        "delivery-sweep-hourly": {
            "task": "app.tasks.delivery.sweep_pending_deliveries",
            "schedule": crontab(minute=0),
            "options": {"queue": "delivery"},
        },
        "filing-reminders-daily": {
            "task": "app.tasks.filing.check_upcoming_deadlines",
            "schedule": crontab(hour=7, minute=0),
            "options": {"queue": "filing"},
        },
    }

    # Tests & local dev: run tasks synchronously in-process.
    if os.getenv("CELERY_TASK_ALWAYS_EAGER", "").lower() in {"1", "true", "yes"}:
        app.conf.task_always_eager = True
        app.conf.task_eager_propagates = True
        logger.info("Celery running in EAGER mode (tests / dev)")

    return app


celery_app = _make_celery()


__all__ = ["celery_app", "TASK_MODULES"]
