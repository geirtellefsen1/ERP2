"""Delivery factory — mock for tests, Resend stub for live."""
from __future__ import annotations

from typing import Literal

from .base import Deliverer, DeliveryError
from .mock import MockDeliverer


Mode = Literal["mock", "live"]


def get_deliverer(mode: Mode = "mock") -> Deliverer:
    """
    Return the active deliverer.

    Live mode is intentionally not yet implemented — it requires a Resend
    API key and a configured sender domain with verified SPF/DKIM. Once
    that's in place, add ResendDeliverer in this package and dispatch to
    it here.
    """
    if mode == "mock":
        return MockDeliverer()
    if mode == "live":
        raise DeliveryError(
            "Live deliverer not yet implemented. Requires:\n"
            "  - RESEND_API_KEY in /etc/claud-erp/.env\n"
            "  - Verified sender domain with SPF and DKIM records\n"
            "  - app/services/delivery/resend.py implementing Deliverer\n"
            "Use mode='mock' until those are in place."
        )
    raise DeliveryError(f"Unknown delivery mode: {mode}")
