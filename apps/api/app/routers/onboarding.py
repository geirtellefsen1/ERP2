"""Onboarding wizard state endpoints."""

import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user, CurrentUser
from app.models import OnboardingProgress

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

STEP_NAMES = [
    "Agency Setup",
    "Invite Users",
    "Connect Bank",
    "Import Chart of Accounts",
    "First Client",
]
MIN_STEP = 1
MAX_STEP = 5


# ── Schemas ──────────────────────────────────────────────────────────

class OnboardingStateResponse(BaseModel):
    current_step: int
    step_data: Optional[dict] = None
    completed_at: Optional[datetime] = None
    step_names: list[str] = STEP_NAMES

    model_config = {"from_attributes": True}


class OnboardingStateUpdate(BaseModel):
    current_step: int
    step_data: Optional[dict] = None

    @field_validator("current_step")
    @classmethod
    def validate_step(cls, v: int) -> int:
        if v < MIN_STEP or v > MAX_STEP:
            raise ValueError(f"current_step must be between {MIN_STEP} and {MAX_STEP}")
        return v


# ── Endpoints ────────────────────────────────────────────────────────

@router.get("/state", response_model=OnboardingStateResponse)
def get_onboarding_state(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current onboarding step and saved form data for the user's agency."""
    progress = db.execute(
        select(OnboardingProgress).where(
            OnboardingProgress.agency_id == user.agency_id
        )
    ).scalar_one_or_none()

    if progress is None:
        return OnboardingStateResponse(current_step=1, step_data=None)

    step_data = None
    if progress.step_data:
        try:
            step_data = json.loads(progress.step_data)
        except json.JSONDecodeError:
            step_data = None

    return OnboardingStateResponse(
        current_step=progress.current_step,
        step_data=step_data,
        completed_at=progress.completed_at,
    )


@router.put("/state", response_model=OnboardingStateResponse)
def update_onboarding_state(
    payload: OnboardingStateUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save the current onboarding step and partial form data."""
    progress = db.execute(
        select(OnboardingProgress).where(
            OnboardingProgress.agency_id == user.agency_id
        )
    ).scalar_one_or_none()

    step_data_json = json.dumps(payload.step_data) if payload.step_data else None

    if progress is None:
        progress = OnboardingProgress(
            agency_id=user.agency_id,
            current_step=payload.current_step,
            step_data=step_data_json,
        )
        db.add(progress)
    else:
        progress.current_step = payload.current_step
        progress.step_data = step_data_json

    # Mark complete when the user finishes step 5
    if payload.current_step == MAX_STEP and progress.completed_at is None:
        progress.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(progress)

    step_data = None
    if progress.step_data:
        try:
            step_data = json.loads(progress.step_data)
        except json.JSONDecodeError:
            step_data = None

    return OnboardingStateResponse(
        current_step=progress.current_step,
        step_data=step_data,
        completed_at=progress.completed_at,
    )
