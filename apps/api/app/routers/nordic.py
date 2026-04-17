from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models import Account, Client
from app.auth import AuthUser, get_current_user
from app.services.nordic import (
    vat_rate_options,
    validate_org_number,
    get_coa_template,
    coa_as_dicts,
)

router = APIRouter(prefix="/api/v1/nordic", tags=["nordic"])


@router.get("/vat-rates")
def get_vat_rates(
    country: str = Query("NO", pattern=r"^(NO|SE)$"),
    locale: str = Query("en"),
):
    return vat_rate_options(country, locale)


class OrgValidationRequest(BaseModel):
    org_number: str
    country: str = "NO"


class OrgValidationResponse(BaseModel):
    valid: bool
    formatted: str
    error: Optional[str] = None


@router.post("/validate-org-number", response_model=OrgValidationResponse)
def validate_org(data: OrgValidationRequest):
    result = validate_org_number(data.org_number, data.country)
    return OrgValidationResponse(
        valid=result.valid,
        formatted=result.formatted,
        error=result.error,
    )


@router.get("/coa-template")
def get_coa(
    country: str = Query("NO", pattern=r"^(NO|SE)$"),
    locale: str = Query("en"),
):
    return coa_as_dicts(country, locale)


@router.post("/seed-accounts")
def seed_accounts(
    client_id: int = Query(...),
    country: str = Query("NO", pattern=r"^(NO|SE)$"),
    locale: str = Query("en"),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.agency_id == current_user.agency_id,
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    existing = db.query(Account).filter(Account.client_id == client_id).count()
    if existing > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Client already has {existing} accounts. Delete them first or skip seeding.",
        )

    name_key = {"no": "name_no", "nb": "name_no", "sv": "name_sv"}.get(locale, "name_en")
    template = get_coa_template(country)
    created = []
    parent_map: dict[str, int] = {}

    for acct in template:
        parent_id = parent_map.get(acct.parent_code) if acct.parent_code else None
        account = Account(
            client_id=client_id,
            code=acct.code,
            name=getattr(acct, name_key),
            account_type=acct.type,
            parent_id=parent_id,
            is_active=True,
        )
        db.add(account)
        db.flush()
        parent_map[acct.code] = account.id
        created.append(acct.code)

    db.commit()
    return {"seeded": len(created), "codes": created, "country": country}
