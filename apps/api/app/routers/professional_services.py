from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from decimal import Decimal

from app.db.session import get_db
from app.auth.middleware import get_current_user, security
from app.models.professional_services import (
    Matter,
    TimeEntry,
    BillingRate,
    WIPEntry,
    TrustTransaction,
    Disbursement,
)
from app.schemas.professional_services import (
    MatterCreate,
    MatterResponse,
    MatterList,
    TimeEntryCreate,
    TimeEntryResponse,
    TimeEntryList,
    BillingRateCreate,
    BillingRateResponse,
    BillingRateList,
    WIPAgingResponse,
    UtilisationResponse,
    TrustTransactionCreate,
    TrustTransactionResponse,
    TrustTransactionList,
    DisbursementCreate,
    DisbursementResponse,
    DisbursementList,
)
from app.services.time_tracking_service import (
    calculate_units,
    calculate_wip,
    get_wip_aging,
    calculate_utilisation,
)

router = APIRouter(prefix="/ps", tags=["professional-services"])


# --- Matters ---

@router.post("/matters", response_model=MatterResponse, status_code=status.HTTP_201_CREATED)
async def create_matter(
    data: MatterCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Create a new matter."""
    ctx = await get_current_user(credentials)
    matter = Matter(
        client_id=data.client_id,
        code=data.code,
        name=data.name,
        matter_type=data.matter_type,
        client_reference=data.client_reference,
        opened_date=data.opened_date or date.today(),
        responsible_fee_earner_id=data.responsible_fee_earner_id,
    )
    db.add(matter)
    db.commit()
    db.refresh(matter)
    return matter


@router.get("/matters", response_model=MatterList)
async def list_matters(
    client_id: int = Query(None),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List matters with optional client_id filter."""
    ctx = await get_current_user(credentials)
    query = db.query(Matter)
    if client_id:
        query = query.filter(Matter.client_id == client_id)
    total = query.count()
    items = query.all()
    return MatterList(items=items, total=total)


@router.get("/matters/{matter_id}", response_model=MatterResponse)
async def get_matter(
    matter_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get matter detail."""
    ctx = await get_current_user(credentials)
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    return matter


# --- Time Entries ---

@router.post("/time-entries", response_model=TimeEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_time_entry(
    data: TimeEntryCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Log a time entry. Auto-calculates units from start/end time."""
    ctx = await get_current_user(credentials)

    units = None
    if data.start_time and data.end_time:
        units = calculate_units(data.start_time, data.end_time)

    entry = TimeEntry(
        matter_id=data.matter_id,
        fee_earner_id=int(ctx.user_id) if ctx.user_id else 0,
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        units=units,
        description=data.description,
        billable=data.billable,
        billed=False,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/time-entries", response_model=TimeEntryList)
async def list_time_entries(
    matter_id: int = Query(None),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List time entries with optional matter_id filter."""
    ctx = await get_current_user(credentials)
    query = db.query(TimeEntry)
    if matter_id:
        query = query.filter(TimeEntry.matter_id == matter_id)
    total = query.count()
    items = query.all()
    return TimeEntryList(items=items, total=total)


# --- Billing Rates ---

@router.post("/billing-rates", response_model=BillingRateResponse, status_code=status.HTTP_201_CREATED)
async def create_billing_rate(
    data: BillingRateCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Set a billing rate."""
    ctx = await get_current_user(credentials)
    rate = BillingRate(
        client_id=data.client_id,
        fee_earner_grade=data.fee_earner_grade,
        matter_type=data.matter_type,
        hourly_rate=data.hourly_rate,
        effective_from=data.effective_from,
        effective_to=data.effective_to,
    )
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


@router.get("/billing-rates", response_model=BillingRateList)
async def list_billing_rates(
    client_id: int = Query(None),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List billing rates."""
    ctx = await get_current_user(credentials)
    query = db.query(BillingRate)
    if client_id:
        query = query.filter(BillingRate.client_id == client_id)
    total = query.count()
    items = query.all()
    return BillingRateList(items=items, total=total)


# --- WIP Aging ---

@router.get("/wip/aging", response_model=WIPAgingResponse)
async def get_wip_aging_report(
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get WIP aging report."""
    ctx = await get_current_user(credentials)
    wip_entries = db.query(WIPEntry).filter(WIPEntry.invoice_date.is_(None)).all()
    today = date.today()
    buckets = get_wip_aging(wip_entries, today)
    return WIPAgingResponse(
        buckets_0_30=buckets["0_30"],
        buckets_31_60=buckets["31_60"],
        buckets_61_90=buckets["61_90"],
        buckets_over_90=buckets["over_90"],
    )


# --- Trust Transactions ---

@router.post("/trust-transactions", response_model=TrustTransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_trust_transaction(
    data: TrustTransactionCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Record a trust transaction."""
    ctx = await get_current_user(credentials)
    txn = TrustTransaction(
        client_id=data.client_id,
        matter_id=data.matter_id,
        transaction_type=data.transaction_type,
        amount=data.amount,
        description=data.description,
        bank_reference=data.bank_reference,
        transaction_date=data.transaction_date,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


@router.get("/trust-transactions", response_model=TrustTransactionList)
async def list_trust_transactions(
    client_id: int = Query(None),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List trust transactions."""
    ctx = await get_current_user(credentials)
    query = db.query(TrustTransaction)
    if client_id:
        query = query.filter(TrustTransaction.client_id == client_id)
    total = query.count()
    items = query.all()
    return TrustTransactionList(items=items, total=total)


# --- Disbursements ---

@router.post("/disbursements", response_model=DisbursementResponse, status_code=status.HTTP_201_CREATED)
async def create_disbursement(
    data: DisbursementCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Record a disbursement."""
    ctx = await get_current_user(credentials)
    disb = Disbursement(
        matter_id=data.matter_id,
        date=data.date,
        description=data.description,
        amount=data.amount,
        to_be_rebilled=data.to_be_rebilled,
        rebilled_amount=data.rebilled_amount,
    )
    db.add(disb)
    db.commit()
    db.refresh(disb)
    return disb


# --- Utilisation ---

@router.get("/utilisation", response_model=list[UtilisationResponse])
async def get_utilisation_report(
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get utilisation report grouped by fee earner."""
    ctx = await get_current_user(credentials)

    # Aggregate time entries by fee_earner_id
    results = (
        db.query(
            TimeEntry.fee_earner_id,
            func.sum(TimeEntry.units).label("total_units"),
            func.sum(
                func.case(
                    (TimeEntry.billable == True, TimeEntry.units),  # noqa: E712
                    else_=0,
                )
            ).label("billable_units"),
        )
        .group_by(TimeEntry.fee_earner_id)
        .all()
    )

    utilisation_list = []
    for row in results:
        total = Decimal(str(row.total_units or 0))
        billable = Decimal(str(row.billable_units or 0))
        # Convert units (6-min blocks) to hours: units / 10
        total_hours = total / Decimal("10")
        billable_hours = billable / Decimal("10")
        pct = calculate_utilisation(total, billable)
        utilisation_list.append(
            UtilisationResponse(
                fee_earner=str(row.fee_earner_id),
                total_hours=total_hours,
                billable_hours=billable_hours,
                utilisation_pct=pct,
            )
        )

    return utilisation_list
