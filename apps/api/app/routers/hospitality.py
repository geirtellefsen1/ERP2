"""
Hospitality Module — Sprint 18.
PMS integration, RevPAR, split P&L per revenue centre.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal
from app.database import get_db
from app.models import PMSConnection, RoomType, DailyRevenue, Client
from app.auth import AuthUser, get_current_user

router = APIRouter(prefix="/api/v1/hospitality", tags=["hospitality"])


@router.get("/dashboard")
def hospitality_dashboard(
    client_id: int = Query(...),
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db),
):
    """
    Hospitality KPI dashboard: ADR, RevPAR, Occupancy, F&B revenue.
    """
    from sqlalchemy import func
    revenues = db.query(
        func.sum(DailyRevenue.rooms_sold).label("total_rooms_sold"),
        func.avg(DailyRevenue.average_rate).label("adr"),
        func.avg(DailyRevenue.revpar).label("revpar"),
        func.sum(DailyRevenue.total_revenue).label("total_revenue"),
        func.sum(DailyRevenue.food_revenue).label("food"),
        func.sum(DailyRevenue.beverage_revenue).label("beverage"),
    ).filter(
        DailyRevenue.client_id == client_id,
        DailyRevenue.date >= datetime.combine(from_date, datetime.min.time()),
        DailyRevenue.date <= datetime.combine(to_date, datetime.max.time()),
    ).first()

    room_types = db.query(RoomType).filter(RoomType.client_id == client_id).all()
    total_rooms = sum(rt.total_rooms for rt in room_types)
    days = max((to_date - from_date).days, 1)

    return {
        "period": f"{from_date} to {to_date}",
        "total_rooms_sold": revenues.total_rooms_sold or 0,
        "adr": round(float(revenues.adr or 0), 2),
        "revpar": round(float(revenues.revpar or 0), 2),
        "total_revenue": float(revenues.total_revenue or 0),
        "food_revenue": float(revenues.food or 0),
        "beverage_revenue": float(revenues.beverage or 0),
        "total_rooms": total_rooms,
        "available_room_nights": total_rooms * days,
        "occupancy_pct": round(
            float(revenues.total_rooms_sold or 0) / max(total_rooms * days, 1) * 100, 1
        ),
    }


@router.get("/revpar-trend")
def revpar_trend(
    client_id: int = Query(...),
    year: int = Query(default_factory=lambda: datetime.now().year),
    db: Session = Depends(get_db),
):
    """Monthly RevPAR trend for a year."""
    from sqlalchemy import extract
    from app.models import DailyRevenue
    from app.database import engine
    results = db.query(
        extract("month", DailyRevenue.date).label("month"),
        func.avg(DailyRevenue.revpar).label("avg_revpar"),
    ).filter(
        DailyRevenue.client_id == client_id,
        extract("year", DailyRevenue.date) == year,
    ).group_by(extract("month", DailyRevenue.date)).all()

    return [{"month": int(r.month), "revpar": round(float(r.avg_revpar or 0), 2)} for r in results]


@router.post("/sync-pms")
def sync_pms_data(
    client_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    Trigger PMS data sync (Opera/Micros/etc.).
    Placeholder — in production: call PMS API to fetch daily revenue data.
    """
    connection = db.query(PMSConnection).filter(
        PMSConnection.client_id == client_id,
        PMSConnection.is_active == True,
    ).first()
    if not connection:
        return {"status": "no_connection", "message": "No active PMS connection configured"}

    return {
        "status": "sync_triggered",
        "pms_type": connection.pms_type,
        "message": "PMS sync initiated — data will be available within 24 hours",
    }
