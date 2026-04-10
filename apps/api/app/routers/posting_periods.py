from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth.middleware import get_current_user, security
from app.models import Client
from app.models.posting_period import PostingPeriod
from app.schemas.posting_period import PostingPeriodCreate, PostingPeriodResponse

router = APIRouter(prefix="/posting-periods", tags=["posting-periods"])


@router.get("", response_model=list[PostingPeriodResponse])
async def list_posting_periods(
    client_id: int = Query(..., description="Client ID to filter posting periods"),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List posting periods for a client."""
    ctx = await get_current_user(credentials)
    client = db.query(Client).filter(
        Client.id == client_id, Client.agency_id == ctx.agency_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    periods = (
        db.query(PostingPeriod)
        .filter(PostingPeriod.client_id == client_id, PostingPeriod.agency_id == ctx.agency_id)
        .order_by(PostingPeriod.period_start.desc())
        .all()
    )
    return periods


@router.post("", response_model=PostingPeriodResponse, status_code=201)
async def create_posting_period(
    data: PostingPeriodCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Create a new posting period."""
    ctx = await get_current_user(credentials)

    client = db.query(Client).filter(
        Client.id == data.client_id, Client.agency_id == ctx.agency_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if data.period_end <= data.period_start:
        raise HTTPException(status_code=400, detail="Period end must be after period start")

    period = PostingPeriod(
        agency_id=ctx.agency_id,
        client_id=data.client_id,
        period_name=data.period_name,
        period_start=data.period_start,
        period_end=data.period_end,
        status="open",
        is_locked=False,
    )
    db.add(period)
    db.commit()
    db.refresh(period)
    return period


@router.put("/{period_id}/close", response_model=PostingPeriodResponse)
async def close_posting_period(
    period_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Close a posting period."""
    ctx = await get_current_user(credentials)
    period = db.query(PostingPeriod).filter(
        PostingPeriod.id == period_id, PostingPeriod.agency_id == ctx.agency_id
    ).first()
    if not period:
        raise HTTPException(status_code=404, detail="Posting period not found")

    if period.status == "locked":
        raise HTTPException(status_code=400, detail="Cannot close a locked period")

    period.status = "closed"
    db.commit()
    db.refresh(period)
    return period


@router.put("/{period_id}/lock", response_model=PostingPeriodResponse)
async def lock_posting_period(
    period_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Lock a posting period."""
    ctx = await get_current_user(credentials)
    period = db.query(PostingPeriod).filter(
        PostingPeriod.id == period_id, PostingPeriod.agency_id == ctx.agency_id
    ).first()
    if not period:
        raise HTTPException(status_code=404, detail="Posting period not found")

    period.status = "locked"
    period.is_locked = True
    db.commit()
    db.refresh(period)
    return period
