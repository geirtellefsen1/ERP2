from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.auth.middleware import get_current_user, security
from app.models.filing import FilingRecord, FilingDeadline
from app.schemas.filing import (
    FilingRecordCreate,
    FilingRecordResponse,
    FilingRecordList,
    FilingDeadlineCreate,
    FilingDeadlineResponse,
    FilingDeadlineList,
    VATFilingPrepareRequest,
    VATFilingResponse,
)
from app.services.filing_service import (
    prepare_vat_filing,
    generate_vat_xml,
    get_upcoming_deadlines,
    submit_filing,
)

router = APIRouter(prefix="/filings", tags=["filings"])


@router.post("", response_model=FilingRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_filing(
    data: FilingRecordCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Create a new filing record."""
    ctx = await get_current_user(credentials)
    filing = FilingRecord(
        client_id=data.client_id,
        jurisdiction=data.jurisdiction,
        filing_type=data.filing_type,
        period_start=data.period_start,
        period_end=data.period_end,
        status="draft",
        created_by=int(ctx.user_id) if ctx.user_id else None,
    )
    db.add(filing)
    db.commit()
    db.refresh(filing)
    return filing


@router.get("", response_model=FilingRecordList)
async def list_filings(
    client_id: Optional[int] = Query(None),
    jurisdiction: Optional[str] = Query(None),
    filing_status: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List filing records with optional filters."""
    ctx = await get_current_user(credentials)
    query = db.query(FilingRecord)

    if client_id is not None:
        query = query.filter(FilingRecord.client_id == client_id)
    if jurisdiction is not None:
        query = query.filter(FilingRecord.jurisdiction == jurisdiction)
    if filing_status is not None:
        query = query.filter(FilingRecord.status == filing_status)

    total = query.count()
    filings = (
        query.order_by(FilingRecord.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return FilingRecordList(items=filings, total=total, page=page, per_page=per_page)


@router.get("/deadlines/upcoming", response_model=FilingDeadlineList)
async def upcoming_deadlines(
    client_id: Optional[int] = Query(None),
    days_ahead: int = Query(30, ge=1, le=365),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get upcoming filing deadlines."""
    ctx = await get_current_user(credentials)
    deadlines = get_upcoming_deadlines(client_id, days_ahead, db)
    return FilingDeadlineList(items=deadlines, total=len(deadlines))


@router.get("/{filing_id}", response_model=FilingRecordResponse)
async def get_filing(
    filing_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get a specific filing record."""
    ctx = await get_current_user(credentials)
    filing = db.query(FilingRecord).filter(FilingRecord.id == filing_id).first()
    if not filing:
        raise HTTPException(status_code=404, detail="Filing record not found")
    return filing


@router.post("/{filing_id}/submit", response_model=FilingRecordResponse)
async def submit_filing_endpoint(
    filing_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Submit a filing (mock submission)."""
    ctx = await get_current_user(credentials)
    try:
        filing = submit_filing(filing_id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return filing


@router.post("/prepare-vat", response_model=VATFilingResponse)
async def prepare_vat(
    data: VATFilingPrepareRequest,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Prepare VAT filing data and generate jurisdiction-specific XML/JSON."""
    ctx = await get_current_user(credentials)
    filing_data = prepare_vat_filing(
        client_id=data.client_id,
        jurisdiction=data.jurisdiction,
        period_start=data.period_start,
        period_end=data.period_end,
    )
    try:
        xml_content = generate_vat_xml(data.jurisdiction, filing_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return VATFilingResponse(
        jurisdiction=data.jurisdiction,
        filing_data=filing_data,
        xml_content=xml_content,
    )


@router.post("/deadlines", response_model=FilingDeadlineResponse, status_code=status.HTTP_201_CREATED)
async def create_deadline(
    data: FilingDeadlineCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Create a filing deadline."""
    ctx = await get_current_user(credentials)
    deadline = FilingDeadline(
        client_id=data.client_id,
        jurisdiction=data.jurisdiction,
        filing_type=data.filing_type,
        due_date=data.due_date,
        frequency=data.frequency,
    )
    db.add(deadline)
    db.commit()
    db.refresh(deadline)
    return deadline
