"""GDPR Data Subject Rights (DSR) service.

Handles data export (access/portability) and erasure for a given
subject email within an agency's scope.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import (
    Client,
    ClientContact,
    DsrArtifact,
    FeeEarner,
    User,
)

logger = logging.getLogger(__name__)


def export_subject_data(
    db: Session,
    agency_id: int,
    subject_email: str,
) -> dict:
    """Collect all PII related to *subject_email* within the agency.

    Returns a dict suitable for JSON serialisation (access / portability).
    """
    data: dict = {"subject_email": subject_email, "exported_at": datetime.now(timezone.utc).isoformat()}

    # Users
    users = (
        db.query(User)
        .filter(User.agency_id == agency_id, User.email == subject_email)
        .all()
    )
    data["users"] = [
        {"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role, "created_at": str(u.created_at)}
        for u in users
    ]

    # Client contacts — scope to agency via Client FK
    contacts = (
        db.query(ClientContact)
        .join(Client, ClientContact.client_id == Client.id)
        .filter(Client.agency_id == agency_id, ClientContact.email == subject_email)
        .all()
    )
    data["client_contacts"] = [
        {"id": c.id, "name": c.name, "email": c.email, "phone": c.phone, "role": c.role}
        for c in contacts
    ]

    # Fee earners — scope to agency via Client FK
    earners = (
        db.query(FeeEarner)
        .join(Client, FeeEarner.client_id == Client.id)
        .filter(Client.agency_id == agency_id, FeeEarner.email == subject_email)
        .all()
    )
    data["fee_earners"] = [
        {"id": e.id, "name": e.name, "email": e.email, "grade": e.grade}
        for e in earners
    ]

    # Note: Employee records (payroll) lack an email field and require
    # manual matching by the DSR admin. They are not auto-exported here.

    return data


def erase_subject_data(
    db: Session,
    agency_id: int,
    subject_email: str,
) -> dict:
    """Pseudonymise / erase PII for *subject_email* within the agency.

    Financial records (invoices, journal entries, transactions) are
    retained with personal fields redacted — full deletion would violate
    accounting regulations.

    Returns a summary of what was erased.
    """
    summary: dict = {"erased": [], "redacted": []}
    placeholder = "[ERASED]"

    # Users — deactivate + scrub
    users = (
        db.query(User)
        .filter(User.agency_id == agency_id, User.email == subject_email)
        .all()
    )
    for u in users:
        u.email = f"erased-{u.id}@redacted.local"
        u.full_name = placeholder
        u.hashed_password = "!"  # cannot log in
        u.is_active = False
        summary["erased"].append(f"user:{u.id}")

    # Client contacts — delete (scoped to agency)
    contacts = (
        db.query(ClientContact)
        .join(Client, ClientContact.client_id == Client.id)
        .filter(Client.agency_id == agency_id, ClientContact.email == subject_email)
        .all()
    )
    for c in contacts:
        summary["erased"].append(f"client_contact:{c.id}")
        db.delete(c)

    # Fee earners — pseudonymise (scoped to agency)
    earners = (
        db.query(FeeEarner)
        .join(Client, FeeEarner.client_id == Client.id)
        .filter(Client.agency_id == agency_id, FeeEarner.email == subject_email)
        .all()
    )
    for e in earners:
        e.name = placeholder
        e.email = f"erased-{e.id}@redacted.local"
        e.is_active = False
        summary["redacted"].append(f"fee_earner:{e.id}")

    db.flush()
    return summary


def create_artifact(
    db: Session,
    dsr_request_id: int,
    artifact_type: str,
    content: dict,
) -> DsrArtifact:
    """Persist an artifact (e.g. export JSON) for a DSR request."""
    raw = json.dumps(content, default=str, indent=2)
    sha = hashlib.sha256(raw.encode()).hexdigest()
    uri = f"dsr-artifacts/{dsr_request_id}/{artifact_type}.json"

    artifact = DsrArtifact(
        dsr_request_id=dsr_request_id,
        artifact_type=artifact_type,
        uri=uri,
        sha256=sha,
    )
    db.add(artifact)
    db.flush()
    return artifact
