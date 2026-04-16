"""
Integration configuration router.

Endpoints:
  GET  /api/v1/integrations/providers        → catalogue (no secrets)
  GET  /api/v1/integrations                  → per-agency configs, masked
  GET  /api/v1/integrations/{provider}       → one provider, masked
  PUT  /api/v1/integrations/{provider}       → upsert encrypted values
  POST /api/v1/integrations/{provider}/verify → test the connection
  DELETE /api/v1/integrations/{provider}     → wipe one provider

Security:
  - Every endpoint requires an authenticated user
  - Responses are ALWAYS masked — clear-text secrets never leave the API
  - RLS scopes by agency_id so a user from agency A cannot see
    agency B's configs even with a crafted agency_id query string
  - Only admins can write or delete (enforced via RBAC dependency)
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import AuthUser, get_current_user
from app.database import get_db
from app.services import integrations as svc
from app.services.integrations import ProviderSpec
from app.services.tenant import set_tenant_context

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


# ─── Schemas ────────────────────────────────────────────────────────


class FieldSchema(BaseModel):
    key: str
    label: str
    type: str
    is_secret: bool
    required: bool
    placeholder: str
    help_text: str
    options: list[str]


class ProviderSchema(BaseModel):
    key: str
    label: str
    category: str
    description: str
    docs_url: str
    fields: list[FieldSchema]


class ProviderConfigResponse(BaseModel):
    provider: str
    values: dict[str, str]  # masked
    last_verified_at: str | None = None
    last_verification_error: str | None = None
    is_configured: bool


class SetConfigRequest(BaseModel):
    values: dict[str, str]


class VerifyResponse(BaseModel):
    ok: bool
    message: str


# ─── Helpers ────────────────────────────────────────────────────────


def _require_admin(user: AuthUser) -> None:
    if user.role not in ("admin",):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only agency admins can modify integrations",
        )


def _provider_to_schema(p: ProviderSpec) -> ProviderSchema:
    return ProviderSchema(
        key=p.key,
        label=p.label,
        category=p.category,
        description=p.description,
        docs_url=p.docs_url,
        fields=[
            FieldSchema(
                key=f.key,
                label=f.label,
                type=f.type,
                is_secret=f.is_secret,
                required=f.required,
                placeholder=f.placeholder,
                help_text=f.help_text,
                options=f.options,
            )
            for f in p.fields
        ],
    )


# ─── Endpoints ──────────────────────────────────────────────────────


@router.get("/providers", response_model=list[ProviderSchema])
def list_providers(current_user: AuthUser = Depends(get_current_user)):
    """Return the catalogue of known integrations. No secrets involved."""
    return [_provider_to_schema(p) for p in svc.list_providers()]


@router.get("/{provider}", response_model=ProviderConfigResponse)
def get_provider_config(
    provider: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current config for one provider, with secrets masked."""
    try:
        svc.get_provider(provider)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    set_tenant_context(db, current_user.agency_id)
    values = svc.get_config(db, current_user.agency_id, provider)
    masked = svc.mask_for_display(provider, values)
    from app.models import IntegrationConfig
    row = (
        db.query(IntegrationConfig)
        .filter(
            IntegrationConfig.agency_id == current_user.agency_id,
            IntegrationConfig.provider == provider,
        )
        .first()
    )
    return ProviderConfigResponse(
        provider=provider,
        values=masked,
        last_verified_at=(
            row.last_verified_at.isoformat() if row and row.last_verified_at else None
        ),
        last_verification_error=row.last_verification_error if row else None,
        is_configured=bool(values),
    )


@router.put("/{provider}", response_model=ProviderConfigResponse)
def set_provider_config(
    provider: str,
    body: SetConfigRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upsert config values for one provider. Admin only."""
    _require_admin(current_user)
    try:
        svc.get_provider(provider)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    set_tenant_context(db, current_user.agency_id)
    try:
        svc.set_config(
            db=db,
            agency_id=current_user.agency_id,
            provider=provider,
            values=body.values,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Return the (newly masked) current state
    values = svc.get_config(db, current_user.agency_id, provider)
    return ProviderConfigResponse(
        provider=provider,
        values=svc.mask_for_display(provider, values),
        is_configured=bool(values),
    )


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider_config(
    provider: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Wipe all config rows for one provider. Admin only."""
    _require_admin(current_user)
    try:
        svc.get_provider(provider)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    set_tenant_context(db, current_user.agency_id)
    svc.delete_config(db, current_user.agency_id, provider)


@router.post("/{provider}/verify", response_model=VerifyResponse)
def verify_provider(
    provider: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Test connection — for providers that support it. Currently a stub
    that just checks required fields are populated; live verify calls
    will come as each adapter is implemented.
    """
    _require_admin(current_user)
    try:
        spec = svc.get_provider(provider)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    set_tenant_context(db, current_user.agency_id)
    values = svc.get_config(db, current_user.agency_id, provider)

    missing = [
        f.key for f in spec.fields
        if f.required and not values.get(f.key)
    ]
    if missing:
        error = f"Missing required fields: {', '.join(missing)}"
        svc.mark_verified(db, current_user.agency_id, provider, error=error)
        return VerifyResponse(ok=False, message=error)

    svc.mark_verified(db, current_user.agency_id, provider, error=None)
    return VerifyResponse(
        ok=True,
        message=(
            "All required fields are set. Live connection testing will be "
            "added when the adapter is fully wired."
        ),
    )
