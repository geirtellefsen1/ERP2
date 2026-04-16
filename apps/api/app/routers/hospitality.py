"""Hospitality vertical router.

Exposes property-level dashboard data, KPIs, daily revenue listings,
and the AI activity feed for the hospitality demo.

All endpoints scoped by the current user's agency via RLS.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models import (
    AiActivityFeed,
    Client,
    DailyRevenueImport,
    DailyRevenueLine,
    Outlet,
    Property,
    RoomCategory,
)
from app.services.verticals.hospitality.anomaly import detect_alerts
from app.services.verticals.hospitality.dashboard import get_dashboard


router = APIRouter(prefix="/api/v1/hospitality", tags=["hospitality"])


# --- Response schemas --------------------------------------------------------


class PropertySummary(BaseModel):
    id: int
    client_id: int
    name: str
    country: str
    total_rooms: int
    timezone: str


class RoomCategoryOut(BaseModel):
    id: int
    code: str
    label: str
    room_count: int
    base_rate_minor: int
    currency: str


class OutletOut(BaseModel):
    id: int
    name: str
    outlet_type: str


class DaySnapshotOut(BaseModel):
    snapshot_date: str
    rooms_sold: int
    rooms_available: int
    occupancy_pct: float
    adr_minor: Optional[int]
    revpar_minor: int
    food_revenue_minor: int
    beverage_revenue_minor: int
    food_covers: int
    rooms_revenue_minor: int
    total_revenue_minor: int
    currency: str


class TrendPointOut(BaseModel):
    point_date: str
    occupancy_pct: float
    revpar_minor: int
    total_revenue_minor: int


class AlertOut(BaseModel):
    severity: str
    title: str
    detail: str
    metric: str
    current_value: float
    baseline_value: float
    delta_pct: float


class DashboardResponse(BaseModel):
    property_id: int
    property_name: str
    country: str
    currency: str
    today: Optional[DaySnapshotOut]
    yesterday: Optional[DaySnapshotOut]
    trend_30d: list[TrendPointOut]
    alerts: list[AlertOut]
    room_categories: list[RoomCategoryOut]
    outlets: list[OutletOut]


class AiActivityItem(BaseModel):
    id: int
    client_id: Optional[int]
    category: str
    severity: str
    title: str
    detail: Optional[str]
    source_kind: Optional[str]
    source_id: Optional[int]
    requires_review: bool
    reviewed_at: Optional[str]
    created_at: str


# --- Helpers -----------------------------------------------------------------


def _ensure_property_visible(
    db: Session, property_id: int, current_user: CurrentUser
) -> Property:
    """Load a property and verify the caller's agency owns its client."""
    prop = db.query(Property).filter(Property.id == property_id).first()
    if prop is None:
        raise HTTPException(status_code=404, detail="Property not found")
    client = db.query(Client).filter(Client.id == prop.client_id).first()
    if client is None or client.agency_id != current_user.agency_id:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


# --- Routes ------------------------------------------------------------------


@router.get("/properties", response_model=list[PropertySummary])
def list_properties(
    client_id: Optional[int] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List every hospitality property visible to the caller's agency.

    Optionally filter to one client_id.
    """
    agency_client_ids = [
        c.id
        for c in db.query(Client.id)
        .filter(Client.agency_id == current_user.agency_id)
        .all()
    ]
    q = db.query(Property).filter(Property.client_id.in_(agency_client_ids))
    if client_id is not None:
        q = q.filter(Property.client_id == client_id)
    return [
        PropertySummary(
            id=p.id,
            client_id=p.client_id,
            name=p.name,
            country=p.country,
            total_rooms=p.total_rooms,
            timezone=p.timezone,
        )
        for p in q.all()
    ]


@router.get("/properties/{property_id}/dashboard", response_model=DashboardResponse)
def property_dashboard(
    property_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Build the headline hospitality dashboard for one property.

    Returns today's snapshot, yesterday's snapshot, a 30-day trend,
    active alerts, and the property's room categories + outlets.
    """
    prop = _ensure_property_visible(db, property_id, current_user)

    payload = get_dashboard(db, property_id)
    alerts = detect_alerts(db, property_id)

    cats = (
        db.query(RoomCategory)
        .filter(RoomCategory.property_id == property_id)
        .order_by(RoomCategory.base_rate_minor.asc())
        .all()
    )
    outs = (
        db.query(Outlet)
        .filter(Outlet.property_id == property_id)
        .order_by(Outlet.name.asc())
        .all()
    )

    def snap(s):
        if s is None:
            return None
        return DaySnapshotOut(
            snapshot_date=s.snapshot_date.isoformat(),
            rooms_sold=s.rooms_sold,
            rooms_available=s.rooms_available,
            occupancy_pct=s.occupancy_pct,
            adr_minor=s.adr_minor,
            revpar_minor=s.revpar_minor,
            food_revenue_minor=s.food_revenue_minor,
            beverage_revenue_minor=s.beverage_revenue_minor,
            food_covers=s.food_covers,
            rooms_revenue_minor=s.rooms_revenue_minor,
            total_revenue_minor=s.total_revenue_minor,
            currency=s.currency,
        )

    return DashboardResponse(
        property_id=payload.property_id,
        property_name=payload.property_name,
        country=payload.country,
        currency=payload.currency,
        today=snap(payload.today),
        yesterday=snap(payload.yesterday),
        trend_30d=[
            TrendPointOut(
                point_date=p.point_date.isoformat(),
                occupancy_pct=p.occupancy_pct,
                revpar_minor=p.revpar_minor,
                total_revenue_minor=p.total_revenue_minor,
            )
            for p in payload.trend_30d
        ],
        alerts=[
            AlertOut(
                severity=a.severity,
                title=a.title,
                detail=a.detail,
                metric=a.metric,
                current_value=a.current_value,
                baseline_value=a.baseline_value,
                delta_pct=a.delta_pct,
            )
            for a in alerts
        ],
        room_categories=[
            RoomCategoryOut(
                id=c.id,
                code=c.code,
                label=c.label,
                room_count=c.room_count,
                base_rate_minor=c.base_rate_minor,
                currency=c.currency,
            )
            for c in cats
        ],
        outlets=[
            OutletOut(id=o.id, name=o.name, outlet_type=o.outlet_type)
            for o in outs
        ],
    )


@router.get("/ai-activity", response_model=list[AiActivityItem])
def ai_activity(
    since_hours: int = Query(72, ge=1, le=24 * 30),
    client_id: Optional[int] = Query(None),
    requires_review: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List AI activity items for the agency.

    Used by the dashboard "AI did this since you last logged in" panel
    and the approvals queue.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    q = (
        db.query(AiActivityFeed)
        .filter(
            AiActivityFeed.agency_id == current_user.agency_id,
            AiActivityFeed.created_at >= cutoff,
        )
        .order_by(desc(AiActivityFeed.created_at))
    )
    if client_id is not None:
        q = q.filter(AiActivityFeed.client_id == client_id)
    if requires_review is not None:
        q = q.filter(AiActivityFeed.requires_review == requires_review)

    items = q.limit(limit).all()
    return [
        AiActivityItem(
            id=i.id,
            client_id=i.client_id,
            category=i.category,
            severity=i.severity,
            title=i.title,
            detail=i.detail,
            source_kind=i.source_kind,
            source_id=i.source_id,
            requires_review=i.requires_review,
            reviewed_at=i.reviewed_at.isoformat() if i.reviewed_at else None,
            created_at=i.created_at.isoformat(),
        )
        for i in items
    ]


@router.post("/ai-activity/{item_id}/approve")
def approve_ai_activity(
    item_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark an AI activity item as reviewed/approved."""
    item = (
        db.query(AiActivityFeed)
        .filter(
            AiActivityFeed.id == item_id,
            AiActivityFeed.agency_id == current_user.agency_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Activity item not found")
    item.reviewed_at = datetime.now(timezone.utc)
    item.reviewed_by_user_id = current_user.id
    db.commit()
    return {"detail": "Approved"}
