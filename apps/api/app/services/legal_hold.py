"""Legal hold service.

Checks whether a deletion / DSR erasure is blocked by an active legal hold.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import LegalHold


def is_on_hold(
    db: Session,
    agency_id: int,
    client_id: int | None = None,
    subject_email: str | None = None,
) -> bool:
    """Return True if any active legal hold covers the given scope.

    Matching rules (OR — any match blocks):
    1. Agency-wide hold: active hold with agency_id and no client_id/subject_email.
    2. Client-specific hold: active hold matching agency_id + client_id.
    3. Subject-specific hold: active hold matching agency_id + subject_email.
    """
    q = db.query(LegalHold).filter(
        LegalHold.agency_id == agency_id,
        LegalHold.active.is_(True),
    )

    from sqlalchemy import or_

    conditions = [
        # Agency-wide hold (no client_id and no subject_email)
        (LegalHold.client_id.is_(None) & LegalHold.subject_email.is_(None)),
    ]
    if client_id is not None:
        conditions.append(LegalHold.client_id == client_id)
    if subject_email is not None:
        conditions.append(LegalHold.subject_email == subject_email)

    q = q.filter(or_(*conditions))
    return q.first() is not None
