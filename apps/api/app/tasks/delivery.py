"""
Report delivery background tasks.

ReportDelivery rows are created in the "pending" state by the reporting
service. The hourly `sweep_pending_deliveries` Beat task finds them,
loads the stored PDF (via the storage abstraction), sends the email via
the configured deliverer, and moves the row to "sent" or "failed".
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import ReportDelivery
from app.services.delivery import (
    Deliverer,
    DeliveryError,
    EmailDelivery,
    get_deliverer,
)
from app.services.storage import LocalStorage, StorageError

logger = logging.getLogger(__name__)

# Cap how many we process in a single sweep so one slow run can't run
# the worker out of memory with 500 PDFs.
SWEEP_BATCH_LIMIT = 50


def _db_session() -> Session:
    return SessionLocal()


def _load_pdf_bytes(storage, pdf_path: str) -> bytes:
    """Best-effort PDF load — returns empty bytes if anything goes wrong."""
    try:
        return storage.get(pdf_path)
    except StorageError as e:
        logger.warning("delivery: pdf not loadable path=%s err=%s", pdf_path, e)
        return b""


@shared_task(
    name="app.tasks.delivery.send_report_delivery",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    retry_backoff=True,
)
def send_report_delivery(
    self,
    delivery_id: int,
    *,
    mode: str = "mock",
) -> dict:
    """
    Send a single queued ReportDelivery row. Idempotent — if the row is
    already "sent" this returns a no-op result without re-sending.
    """
    db = _db_session()
    try:
        row = db.query(ReportDelivery).filter(ReportDelivery.id == delivery_id).first()
        if row is None:
            return {"delivery_id": delivery_id, "status": "missing"}
        if row.status == "sent":
            return {"delivery_id": delivery_id, "status": "already_sent"}

        storage = LocalStorage()  # tasks-layer: local is fine for dev; prod
                                  # swap once object storage is wired via DI.
        pdf = _load_pdf_bytes(storage, row.pdf_path) if row.pdf_path else b""

        attachments = []
        if pdf:
            filename = (row.pdf_path or "report.pdf").rsplit("/", 1)[-1]
            attachments.append((filename, pdf))

        deliverer: Deliverer = get_deliverer(mode=mode)
        try:
            receipt = deliverer.send(
                EmailDelivery(
                    to=row.recipient_email or "",
                    subject=f"ClaudERP — {row.report_type}",
                    body_text="Your report is attached.",
                    attachments=attachments,
                    language=row.language or "en",
                )
            )
        except DeliveryError as exc:
            row.status = "failed"
            row.delivery_error = str(exc)
            db.commit()
            return {"delivery_id": delivery_id, "status": "failed", "error": str(exc)}

        row.status = "sent"
        row.delivery_provider = receipt.provider
        row.delivery_message_id = receipt.message_id
        row.sent_at = datetime.now(timezone.utc)
        db.commit()
        return {
            "delivery_id": delivery_id,
            "status": "sent",
            "provider": receipt.provider,
        }
    finally:
        db.close()


@shared_task(name="app.tasks.delivery.sweep_pending_deliveries")
def sweep_pending_deliveries(limit: int = SWEEP_BATCH_LIMIT) -> dict:
    """
    Find pending deliveries whose `scheduled_for` has passed and enqueue
    a send task for each. Called hourly by Beat.
    """
    db = _db_session()
    now = datetime.now(timezone.utc)
    try:
        rows = (
            db.query(ReportDelivery)
            .filter(
                ReportDelivery.status == "pending",
                ReportDelivery.scheduled_for != None,  # noqa: E711
                ReportDelivery.scheduled_for <= now,
            )
            .order_by(ReportDelivery.scheduled_for.asc())
            .limit(limit)
            .all()
        )
        dispatched = 0
        for row in rows:
            try:
                send_report_delivery.apply_async(
                    args=(row.id,), queue="delivery"
                )
                dispatched += 1
            except Exception:
                logger.exception(
                    "delivery sweep: failed to enqueue delivery_id=%s", row.id
                )
        return {"candidates": len(rows), "dispatched": dispatched}
    finally:
        db.close()
