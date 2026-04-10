from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from app.db.session import get_db
from app.auth.middleware import get_current_user, security
from app.models.hospitality import (
    HospitalityClient,
    RoomType,
    DailyRevenue,
    GratuityTip,
    InventoryStockTake,
)
from app.schemas.hospitality import (
    HospitalityClientCreate,
    HospitalityClientResponse,
    RoomTypeCreate,
    RoomTypeResponse,
    DailyRevenueCreate,
    DailyRevenueResponse,
    DailyRevenueList,
    GratuityTipCreate,
    GratuityTipResponse,
    StockTakeCreate,
    StockTakeResponse,
    HospitalityMetricsResponse,
)
from app.services.hospitality_service import (
    calculate_revpar,
    calculate_adr,
    calculate_occupancy,
    calculate_stock_variance,
)

router = APIRouter(prefix="/hospitality", tags=["hospitality"])


# --- Hospitality Clients ---

@router.post("/clients", response_model=HospitalityClientResponse, status_code=status.HTTP_201_CREATED)
async def create_hospitality_client(
    data: HospitalityClientCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Register a hospitality client."""
    ctx = await get_current_user(credentials)
    client = HospitalityClient(
        client_id=data.client_id,
        pms_system=data.pms_system,
        currency=data.currency,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/clients", response_model=list[HospitalityClientResponse])
async def list_hospitality_clients(
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List hospitality clients."""
    ctx = await get_current_user(credentials)
    clients = db.query(HospitalityClient).all()
    return clients


# --- Room Types ---

@router.post("/room-types", response_model=RoomTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_room_type(
    data: RoomTypeCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Create a room type."""
    ctx = await get_current_user(credentials)
    room_type = RoomType(
        hospitality_client_id=data.hospitality_client_id,
        code=data.code,
        name=data.name,
        capacity=data.capacity,
        avg_daily_rate=data.avg_daily_rate,
    )
    db.add(room_type)
    db.commit()
    db.refresh(room_type)
    return room_type


@router.get("/room-types", response_model=list[RoomTypeResponse])
async def list_room_types(
    hospitality_client_id: Optional[int] = Query(None),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List room types, optionally filtered by hospitality client."""
    ctx = await get_current_user(credentials)
    query = db.query(RoomType)
    if hospitality_client_id is not None:
        query = query.filter(RoomType.hospitality_client_id == hospitality_client_id)
    return query.all()


# --- Daily Revenue ---

@router.post("/daily-revenue", response_model=DailyRevenueResponse, status_code=status.HTTP_201_CREATED)
async def create_daily_revenue(
    data: DailyRevenueCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Record daily revenue."""
    ctx = await get_current_user(credentials)
    revenue = DailyRevenue(
        hospitality_client_id=data.hospitality_client_id,
        date=data.date,
        room_type_id=data.room_type_id,
        revenue_stream=data.revenue_stream,
        rooms_available=data.rooms_available,
        rooms_occupied=data.rooms_occupied,
        total_revenue=data.total_revenue,
    )
    db.add(revenue)
    db.commit()
    db.refresh(revenue)
    return revenue


@router.get("/daily-revenue", response_model=DailyRevenueList)
async def list_daily_revenue(
    hospitality_client_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List daily revenue with date range filter."""
    ctx = await get_current_user(credentials)
    query = db.query(DailyRevenue)
    if hospitality_client_id is not None:
        query = query.filter(DailyRevenue.hospitality_client_id == hospitality_client_id)
    if start_date is not None:
        query = query.filter(DailyRevenue.date >= start_date)
    if end_date is not None:
        query = query.filter(DailyRevenue.date <= end_date)
    items = query.all()
    return DailyRevenueList(items=items, total=len(items))


# --- Metrics ---

@router.get("/metrics", response_model=HospitalityMetricsResponse)
async def get_metrics(
    hospitality_client_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get hospitality metrics (RevPAR, ADR, Occupancy) for a date range."""
    ctx = await get_current_user(credentials)
    revenue_data = (
        db.query(DailyRevenue)
        .filter(
            DailyRevenue.hospitality_client_id == hospitality_client_id,
            DailyRevenue.date >= start_date,
            DailyRevenue.date <= end_date,
        )
        .all()
    )
    revpar = calculate_revpar(revenue_data)
    adr = calculate_adr(revenue_data)
    occupancy = calculate_occupancy(revenue_data)
    period = f"{start_date.isoformat()} to {end_date.isoformat()}"
    return HospitalityMetricsResponse(
        revpar=revpar,
        adr=adr,
        occupancy_pct=occupancy,
        period=period,
    )


# --- Gratuity Tips ---

@router.post("/tips", response_model=GratuityTipResponse, status_code=status.HTTP_201_CREATED)
async def create_tip(
    data: GratuityTipCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Record a gratuity tip."""
    ctx = await get_current_user(credentials)
    tip = GratuityTip(
        hospitality_client_id=data.hospitality_client_id,
        employee_id=data.employee_id,
        date=data.date,
        amount=data.amount,
        source=data.source,
    )
    db.add(tip)
    db.commit()
    db.refresh(tip)
    return tip


# --- Stock Take ---

@router.post("/stock-take", response_model=StockTakeResponse, status_code=status.HTTP_201_CREATED)
async def create_stock_take(
    data: StockTakeCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Record a stock take with automatic variance calculation."""
    ctx = await get_current_user(credentials)
    variance = calculate_stock_variance(
        data.quantity_counted,
        data.quantity_expected,
        data.unit_cost,
    )
    stock_take = InventoryStockTake(
        hospitality_client_id=data.hospitality_client_id,
        date=data.date,
        item_code=data.item_code,
        description=data.description,
        quantity_counted=data.quantity_counted,
        quantity_expected=data.quantity_expected,
        unit_cost=data.unit_cost,
        variance=variance,
    )
    db.add(stock_take)
    db.commit()
    db.refresh(stock_take)
    return stock_take
