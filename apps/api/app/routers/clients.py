from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Client as ClientModel
from app.schemas import ClientCreate, ClientUpdate, Client as ClientSchema
from app.auth import AuthUser, get_current_user
from app.rbac import require_min_role, Roles

router = APIRouter(prefix="/api/v1/clients", tags=["clients"])


@router.get("", response_model=list[ClientSchema])
def list_clients(
    skip: int = 0,
    limit: int = 100,
    country: str | None = None,
    is_active: bool | None = None,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(ClientModel).filter(ClientModel.agency_id == current_user.agency_id)
    if country:
        q = q.filter(ClientModel.country == country)
    if is_active is not None:
        q = q.filter(ClientModel.is_active == is_active)
    return q.offset(skip).limit(limit).all()


@router.post("", response_model=ClientSchema, status_code=status.HTTP_201_CREATED)
def create_client(
    data: ClientCreate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models import Account
    from app.services.nordic import get_coa_template

    client = ClientModel(**data.model_dump(), agency_id=current_user.agency_id)
    db.add(client)
    db.flush()

    country = data.country or "NO"
    if country in ("NO", "SE"):
        name_key = {"NO": "name_no", "SE": "name_sv"}.get(country, "name_en")
        template = get_coa_template(country)
        parent_map: dict[str, int] = {}
        for acct in template:
            parent_id = parent_map.get(acct.parent_code) if acct.parent_code else None
            account = Account(
                client_id=client.id,
                code=acct.code,
                name=getattr(acct, name_key),
                account_type=acct.type,
                parent_id=parent_id,
                is_active=True,
            )
            db.add(account)
            db.flush()
            parent_map[acct.code] = account.id

    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientSchema)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.patch("/{client_id}", response_model=ClientSchema)
def update_client(
    client_id: int,
    data: ClientUpdate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = db.query(ClientModel).filter(
        ClientModel.id == client_id,
        ClientModel.agency_id == current_user.agency_id,
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    db.delete(client)
    db.commit()
