from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Client
from app.schemas import ClientCreate, ClientUpdate, Client
from app.auth import AuthUser, get_current_user
from app.rbac import require_min_role, Roles

router = APIRouter(prefix="/api/v1/clients", tags=["clients"])


@router.get("", response_model=list[Client])
def list_clients(
    skip: int = 0,
    limit: int = 100,
    country: str | None = None,
    is_active: bool | None = None,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Client).filter(Client.agency_id == current_user.agency_id)
    if country:
        q = q.filter(Client.country == country)
    if is_active is not None:
        q = q.filter(Client.is_active == is_active)
    return q.offset(skip).limit(limit).all()


@router.post("", response_model=Client, status_code=status.HTTP_201_CREATED)
def create_client(
    data: ClientCreate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = Client(**data.model_dump(), agency_id=current_user.agency_id)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=Client)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.patch("/{client_id}", response_model=Client)
def update_client(client_id: int, data: ClientUpdate, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    db.delete(client)
    db.commit()
