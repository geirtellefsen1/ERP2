"""
Scheduled delivery interface for reports.

Same pattern as the statutory submitter: an abstract Deliverer interface
plus a MockDeliverer for tests/dev and a ResendDeliverer stub for
production. Production stub is intentionally not implemented yet — flip
the mode flag once a Resend API key is in place and implement
ResendDeliverer.send() with the real API call.

Usage:
    from app.services.delivery import get_deliverer, EmailDelivery

    deliverer = get_deliverer(mode="mock")
    receipt = deliverer.send(
        EmailDelivery(
            to="admin@acme.no",
            subject="Acme — March 2026 Management Report",
            body_text="Attached is your monthly report.",
            attachments=[("acme-march-2026.pdf", pdf_bytes)],
            language="nb-NO",
        )
    )
"""
from .base import (
    EmailDelivery,
    DeliveryReceipt,
    Deliverer,
    DeliveryError,
)
from .mock import MockDeliverer
from .factory import get_deliverer

__all__ = [
    "EmailDelivery",
    "DeliveryReceipt",
    "Deliverer",
    "DeliveryError",
    "MockDeliverer",
    "get_deliverer",
]
