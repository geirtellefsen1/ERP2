"""
MockSubmitter — in-memory submitter used for development and testing.

Records every submission in a thread-local store so tests and dev
environments can inspect what would have been sent without touching
a real tax authority. Returns a deterministic reference number so
subsequent status checks work.
"""
from __future__ import annotations

import hashlib
import threading
from datetime import datetime, timezone

from .base import (
    StatutoryFiling,
    SubmissionReceipt,
    StatutorySubmitter,
)


class MockSubmitter(StatutorySubmitter):
    """In-memory submitter. Accepts everything. Useful for local dev."""

    provider_name = "mock"

    # Shared across instances so tests can reset it
    _lock = threading.Lock()
    _submissions: dict[str, SubmissionReceipt] = {}
    _payloads: dict[str, StatutoryFiling] = {}

    def submit(self, filing: StatutoryFiling) -> SubmissionReceipt:
        reference = self._make_reference(filing)
        receipt = SubmissionReceipt(
            form_code=filing.form_code,
            submitted_at=datetime.now(timezone.utc),
            status="accepted",
            reference_number=reference,
            message="Mock submission recorded locally",
            provider=self.provider_name,
        )
        with self._lock:
            self._submissions[reference] = receipt
            self._payloads[reference] = filing
        return receipt

    def check_status(self, reference_number: str) -> SubmissionReceipt:
        with self._lock:
            if reference_number not in self._submissions:
                return SubmissionReceipt(
                    form_code="unknown",
                    submitted_at=datetime.now(timezone.utc),
                    status="error",
                    reference_number=reference_number,
                    message="No submission found with that reference",
                    provider=self.provider_name,
                )
            return self._submissions[reference_number]

    # ── Helpers ─────────────────────────────────────────────────────

    def _make_reference(self, filing: StatutoryFiling) -> str:
        """
        Deterministic reference from the form code, period, and org number
        so retries don't create duplicates and tests can verify equality.
        """
        key = f"{filing.form_code}|{filing.period_start}|{filing.period_end}|{filing.organisation_number}"
        digest = hashlib.sha256(key.encode()).hexdigest()[:12]
        return f"MOCK-{filing.form_code.upper()}-{digest}"

    @classmethod
    def all_submissions(cls) -> list[SubmissionReceipt]:
        """Test helper — returns every submission recorded so far."""
        with cls._lock:
            return list(cls._submissions.values())

    @classmethod
    def get_payload(cls, reference: str) -> StatutoryFiling | None:
        """Test helper — fetch the raw payload that was submitted."""
        with cls._lock:
            return cls._payloads.get(reference)

    @classmethod
    def clear(cls) -> None:
        """Test helper — reset the mock store."""
        with cls._lock:
            cls._submissions.clear()
            cls._payloads.clear()
