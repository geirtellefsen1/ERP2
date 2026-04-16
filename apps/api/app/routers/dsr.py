"""GDPR Data Subject Rights (DSR) router.

Endpoints:
  POST   /api/v1/dsr              — create a new DSR request
  GET    /api/v1/dsr              — list DSR requests for the agency
  GET    /api/v1/dsr/{id}         — get a single DSR request
  POST   /api/v1/dsr/{id}/process — process (execute) a DSR request
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models import DsrRequest, DsrArtifact
from app.services.dsr import create_artifact, erase_subject_data, export_subject_data

router = APIRouter(prefix="/api/v1/dsr", tags=["dsr"])

GDPR_DEADLINE_DAYS = 30


# ─── Schemas ────────────────────────────────────────────────────────────


class DsrCreateRequest(BaseModel):
    subject_email: EmailStr
    subject_name: str | None = None
    request_type: str = Field(..., pattern="^(access|erasure|portability|rectification)$")
    notes: str | None = None


class DsrArtifactOut(BaseModel):
    id: int
    artifact_type: str
    uri: str
    sha256: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DsrOut(BaseModel):
    id: int
    agency_id: int
    subject_email: str
    subject_name: str | None
    request_type: str
    status: str
    received_at: datetime
    deadline_at: datetime
    completed_at: datetime | None
    notes: str | None
    artifacts: list[DsrArtifactOut] = []

    model_config = {"from_attributes": True}


# ─── Routes ─────────────────────────────────────────────────────────────


@router.post("", response_model=DsrOut, status_code=201)
def create_dsr(
    body: DsrCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new GDPR DSR request."""
    now = datetime.now(timezone.utc)
    dsr = DsrRequest(
        agency_id=current_user.agency_id,
        subject_email=body.subject_email,
        subject_name=body.subject_name,
        request_type=body.request_type,
        status="pending",
        received_at=now,
        deadline_at=now + timedelta(days=GDPR_DEADLINE_DAYS),
        notes=body.notes,
    )
    db.add(dsr)
    db.commit()
    db.refresh(dsr)
    return dsr


@router.get("", response_model=list[DsrOut])
def list_dsrs(
    status: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List DSR requests for the current agency."""
    q = db.query(DsrRequest).filter(DsrRequest.agency_id == current_user.agency_id)
    if status:
        q = q.filter(DsrRequest.status == status)
    return q.order_by(DsrRequest.deadline_at.asc()).all()


@router.get("/{dsr_id}", response_model=DsrOut)
def get_dsr(
    dsr_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single DSR request by ID."""
    dsr = (
        db.query(DsrRequest)
        .filter(DsrRequest.id == dsr_id, DsrRequest.agency_id == current_user.agency_id)
        .first()
    )
    if not dsr:
        raise HTTPException(status_code=404, detail="DSR request not found")
    return dsr


@router.post("/{dsr_id}/process", response_model=DsrOut)
def process_dsr(
    dsr_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Process (execute) a DSR request.

    - access / portability → export subject data + create artifact
    - erasure → erase/pseudonymise subject data + create confirmation artifact
    - rectification → mark as in_progress (manual step required)
    """
    dsr = (
        db.query(DsrRequest)
        .filter(DsrRequest.id == dsr_id, DsrRequest.agency_id == current_user.agency_id)
        .first()
    )
    if not dsr:
        raise HTTPException(status_code=404, detail="DSR request not found")
    if dsr.status == "completed":
        raise HTTPException(status_code=400, detail="DSR request already completed")

    now = datetime.now(timezone.utc)

    if dsr.request_type in ("access", "portability"):
        data = export_subject_data(db, dsr.agency_id, dsr.subject_email)
        create_artifact(db, dsr.id, "export_json", data)
        dsr.status = "completed"
        dsr.completed_at = now

    elif dsr.request_type == "erasure":
        summary = erase_subject_data(db, dsr.agency_id, dsr.subject_email)
        create_artifact(db, dsr.id, "erasure_confirmation", summary)
        dsr.status = "completed"
        dsr.completed_at = now

    elif dsr.request_type == "rectification":
        dsr.status = "in_progress"

    db.commit()
    db.refresh(dsr)
    return dsr
