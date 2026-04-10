from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.middleware import get_current_user, MultiTenantContext, security
from app.models import Client
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse, ClientListResponse

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=ClientListResponse)
async def list_clients(
    page: int = 1,
    per_page: int = 20,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List all clients for current agency."""
    ctx = await get_current_user(credentials)
    query = db.query(Client).filter(Client.agency_id == ctx.agency_id)
    total = query.count()
    clients = query.offset((page - 1) * per_page).limit(per_page).all()

    return ClientListResponse(items=clients, total=total, page=page, per_page=per_page)


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get a specific client."""
    ctx = await get_current_user(credentials)
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.agency_id == ctx.agency_id,
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Create a new client."""
    ctx = await get_current_user(credentials)
    client = Client(
        agency_id=ctx.agency_id,
        name=client_data.name,
        registration_number=client_data.registration_number,
        country=client_data.country,
        industry=client_data.industry,
        fiscal_year_end=client_data.fiscal_year_end,
        is_active=True,
        health_score="good",
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    client_data: ClientUpdate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Update a client."""
    ctx = await get_current_user(credentials)
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.agency_id == ctx.agency_id,
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    for field, value in client_data.model_dump(exclude_unset=True).items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)
    return client
