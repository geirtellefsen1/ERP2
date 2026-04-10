from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.middleware import get_current_user, security
from app.models import Account, Client
from app.schemas.account import AccountCreate, AccountUpdate, AccountResponse, AccountHierarchyNode
from typing import Optional

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/client/{client_id}", response_model=list[AccountResponse])
async def list_accounts(
    client_id: int,
    account_type: Optional[str] = Query(None),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List all accounts for a client."""
    ctx = await get_current_user(credentials)
    client = db.query(Client).filter(Client.id == client_id, Client.agency_id == ctx.agency_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    query = db.query(Account).filter(Account.client_id == client_id)
    if account_type:
        query = query.filter(Account.account_type == account_type)

    return query.order_by(Account.account_number).all()


@router.get("/client/{client_id}/hierarchy", response_model=list[AccountHierarchyNode])
async def get_account_hierarchy(
    client_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get account hierarchy (tree structure) for a client."""
    ctx = await get_current_user(credentials)
    client = db.query(Client).filter(Client.id == client_id, Client.agency_id == ctx.agency_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    all_accounts = db.query(Account).filter(Account.client_id == client_id).order_by(Account.account_number).all()

    # Build lookup
    by_id = {a.id: a for a in all_accounts}
    children_map: dict[int | None, list] = {}
    for a in all_accounts:
        children_map.setdefault(a.parent_account_id, []).append(a)

    def build_node(account) -> dict:
        kids = children_map.get(account.id, [])
        return AccountHierarchyNode(
            id=account.id,
            client_id=account.client_id,
            agency_id=account.agency_id,
            account_number=account.account_number,
            name=account.name,
            account_type=account.account_type,
            description=account.description,
            parent_account_id=account.parent_account_id,
            is_active=account.is_active,
            balance=float(account.balance or 0),
            created_at=account.created_at,
            updated_at=account.updated_at,
            children=[build_node(c) for c in kids],
        )

    roots = children_map.get(None, [])
    return [build_node(r) for r in roots]


@router.post("", response_model=AccountResponse, status_code=201)
async def create_account(
    account_data: AccountCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Create a new account."""
    ctx = await get_current_user(credentials)
    client = db.query(Client).filter(Client.id == account_data.client_id, Client.agency_id == ctx.agency_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    account = Account(
        agency_id=ctx.agency_id,
        client_id=account_data.client_id,
        account_number=account_data.account_number,
        name=account_data.name,
        account_type=account_data.account_type,
        description=account_data.description,
        parent_account_id=account_data.parent_account_id,
        is_active="active",
        balance=0,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    account_data: AccountUpdate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Update an account."""
    ctx = await get_current_user(credentials)
    account = db.query(Account).filter(Account.id == account_id, Account.agency_id == ctx.agency_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    for field, value in account_data.model_dump(exclude_unset=True).items():
        setattr(account, field, value)

    db.commit()
    db.refresh(account)
    return account
