"""MockDeliverer — in-memory delivery for tests and dev."""
from __future__ import annotations

import threading
from datetime import datetime, timezone

from .base import (
    Deliverer,
    DeliveryReceipt,
    EmailDelivery,
)


class MockDeliverer(Deliverer):
    """In-memory deliverer. Records every send for test introspection."""

    provider_name = "mock"

    _lock = threading.Lock()
    _deliveries: list[tuple[EmailDelivery, DeliveryReceipt]] = []

    def send(self, delivery: EmailDelivery) -> DeliveryReceipt:
        receipt = DeliveryReceipt(
            to=delivery.to,
            subject=delivery.subject,
            sent_at=datetime.now(timezone.utc),
            status="sent",
            provider=self.provider_name,
            message_id=f"mock-{len(MockDeliverer._deliveries) + 1:08d}",
        )
        with self._lock:
            MockDeliverer._deliveries.append((delivery, receipt))
        return receipt

    @classmethod
    def all_deliveries(cls) -> list[tuple[EmailDelivery, DeliveryReceipt]]:
        with cls._lock:
            return list(cls._deliveries)

    @classmethod
    def last(cls) -> tuple[EmailDelivery, DeliveryReceipt] | None:
        with cls._lock:
            return cls._deliveries[-1] if cls._deliveries else None

    @classmethod
    def clear(cls) -> None:
        with cls._lock:
            cls._deliveries.clear()
