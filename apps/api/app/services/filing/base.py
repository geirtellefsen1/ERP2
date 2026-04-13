"""Abstract submitter interface and shared value objects."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Literal, Optional


SubmissionStatus = Literal["pending", "accepted", "rejected", "error"]


@dataclass
class StatutoryFiling:
    """A payload ready to be submitted to a tax authority."""
    form_code: str                  # e.g. "MVA-melding", "AGD", "Tulorekisteri"
    period_start: date
    period_end: date
    organisation_number: str
    # The actual payload — XML for Altinn/Skatteverket, JSON for Tulorekisteri
    payload_xml: Optional[str] = None
    payload_json: Optional[str] = None
    # Extra metadata (client_id, payroll run id, etc.) for the audit trail
    metadata: dict = field(default_factory=dict)


@dataclass
class SubmissionReceipt:
    """Acknowledgement returned by the tax authority after submission."""
    form_code: str
    submitted_at: datetime
    status: SubmissionStatus
    reference_number: str          # tax authority's tracking ID
    message: str = ""              # human-readable status detail
    provider: str = "unknown"      # "altinn" / "skatteverket" / "vero" / "mock"


class SubmitterError(Exception):
    """Raised when a submission fails due to a client-side error."""


class StatutorySubmitter(ABC):
    """Interface that all country-specific submitters implement."""

    provider_name: str

    @abstractmethod
    def submit(self, filing: StatutoryFiling) -> SubmissionReceipt: ...

    @abstractmethod
    def check_status(self, reference_number: str) -> SubmissionReceipt: ...

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)
