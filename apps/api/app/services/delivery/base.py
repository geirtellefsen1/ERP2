"""Abstract delivery interface and value objects."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal, Optional


DeliveryStatus = Literal["pending", "sent", "failed", "bounced"]


@dataclass
class EmailDelivery:
    to: str
    subject: str
    body_text: str
    body_html: str = ""
    attachments: list[tuple[str, bytes]] = field(default_factory=list)  # (filename, content)
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    reply_to: Optional[str] = None
    from_address: Optional[str] = None  # default sender if None
    language: str = "en"


@dataclass
class DeliveryReceipt:
    to: str
    subject: str
    sent_at: datetime
    status: DeliveryStatus
    provider: str
    message_id: str = ""
    error: str = ""


class DeliveryError(Exception):
    """Raised when a delivery fails due to a client-side error."""


class Deliverer(ABC):
    provider_name: str

    @abstractmethod
    def send(self, delivery: EmailDelivery) -> DeliveryReceipt: ...
