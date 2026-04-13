"""
Statutory filing submitter interface.

The payroll/VAT engines produce the payloads (XML for Altinn and
Skatteverket, JSON for Tulorekisteri). The submitter layer is what
actually sends them to the tax authority and captures the acknowledgement.

In production, swap MockSubmitter for a provider-specific LiveSubmitter
that handles authentication (virksomhetssertifikat, BankID, Katso ID) and
the real HTTP posts. Until those credentials are in place, the
MockSubmitter records submissions locally so the rest of the pipeline can
be exercised end-to-end.

Usage:
    from app.services.filing import get_submitter, StatutoryFiling

    submitter = get_submitter("NO", mode="mock")
    receipt = submitter.submit(
        StatutoryFiling(
            form_code="MVA-melding",
            period_start=date(2026, 3, 1),
            period_end=date(2026, 4, 30),
            organisation_number="987654321",
            payload_xml=xml_string,
        )
    )
    print(receipt.reference_number, receipt.status)
"""
from .base import (
    StatutoryFiling,
    SubmissionReceipt,
    SubmissionStatus,
    StatutorySubmitter,
    SubmitterError,
)
from .mock import MockSubmitter
from .factory import get_submitter

__all__ = [
    "StatutoryFiling",
    "SubmissionReceipt",
    "SubmissionStatus",
    "StatutorySubmitter",
    "SubmitterError",
    "MockSubmitter",
    "get_submitter",
]
