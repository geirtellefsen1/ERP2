"""MFA router -- TOTP setup, enable, verify, disable."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models import User
from app.services.mfa import generate_totp_secret, get_provisioning_uri, verify_totp

router = APIRouter(prefix="/api/v1/mfa", tags=["mfa"])


# --- Schemas -----------------------------------------------------------------


class MFASetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    qr_data: str


class MFACodeRequest(BaseModel):
    code: str


class MFAEnableRequest(BaseModel):
    secret: str
    code: str


class MFAVerifyRequest(BaseModel):
    user_id: int
    code: str


# --- Routes ------------------------------------------------------------------


@router.post("/setup", response_model=MFASetupResponse)
def mfa_setup(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Generate a new TOTP secret and provisioning URI for the current user."""
    secret = generate_totp_secret()
    uri = get_provisioning_uri(secret, current_user.email)
    return MFASetupResponse(
        secret=secret,
        provisioning_uri=uri,
        qr_data=uri,
    )


@router.post("/enable")
def mfa_enable(
    body: MFAEnableRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify a TOTP code against the provided secret and enable MFA.

    The client passes the secret from /setup + the code the user entered.
    This avoids storing the secret until verification succeeds.
    """
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_totp(body.secret, body.code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")

    user.mfa_secret = body.secret
    user.mfa_enabled = True
    db.commit()
    return {"detail": "MFA enabled successfully"}


@router.post("/verify")
def mfa_verify(
    body: MFAVerifyRequest,
    db: Session = Depends(get_db),
):
    """Verify a TOTP code during login (no auth header required).

    Returns a uniform 400 for all failure cases to avoid leaking whether
    a user exists or has MFA enabled.
    """
    _invalid = HTTPException(status_code=400, detail="Invalid MFA verification")

    user = db.query(User).filter(User.id == body.user_id).first()
    if not user or not user.mfa_enabled or not user.mfa_secret:
        raise _invalid

    if not verify_totp(user.mfa_secret, body.code):
        raise _invalid

    return {"detail": "MFA verification successful"}


@router.post("/disable")
def mfa_disable(
    body: MFACodeRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disable MFA for the authenticated user (requires a valid TOTP code)."""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.mfa_enabled or not user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA is not enabled")

    if not verify_totp(user.mfa_secret, body.code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")

    user.mfa_enabled = False
    user.mfa_secret = None
    db.commit()
    return {"detail": "MFA disabled successfully"}
