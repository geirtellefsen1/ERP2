from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.auth.middleware import get_current_user, security
from app.models.cashflow import CashflowForecast, CashflowForecastLine, ForecastAlert
from app.schemas.cashflow import (
    CashflowForecastCreate,
    CashflowForecastResponse,
    CashflowForecastDetail,
    CashflowForecastLineResponse,
    ForecastAlertResponse,
    ForecastAlertList,
)
from app.services.cashflow_engine import generate_13_week_forecast, detect_alerts

router = APIRouter(prefix="/cashflow", tags=["cashflow"])


@router.post("/forecasts", response_model=CashflowForecastDetail, status_code=201)
async def create_forecast(
    data: CashflowForecastCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Generate a 13-week cashflow forecast."""
    ctx = await get_current_user(credentials)

    today = date.today()

    # Generate forecast lines
    forecast_lines = generate_13_week_forecast(
        client_id=data.client_id,
        opening_balance=data.opening_balance,
        avg_weekly_receipts=data.avg_weekly_receipts,
        avg_weekly_payments=data.avg_weekly_payments,
    )

    # Determine end date from last line
    end_date = forecast_lines[-1]["week_commencing"] if forecast_lines else today

    # Create forecast record
    forecast = CashflowForecast(
        client_id=data.client_id,
        forecast_date=today,
        end_date=end_date,
        status="draft",
    )
    db.add(forecast)
    db.flush()

    # Create forecast lines
    db_lines = []
    for line_data in forecast_lines:
        line = CashflowForecastLine(
            forecast_id=forecast.id,
            week_commencing=line_data["week_commencing"],
            opening_balance=line_data["opening_balance"],
            receipts=line_data["receipts"],
            payments=line_data["payments"],
            closing_balance=line_data["closing_balance"],
            alert_flag=line_data["alert_flag"],
        )
        db.add(line)
        db_lines.append(line)

    # Detect and create alerts
    alerts_data = detect_alerts(forecast_lines)
    db_alerts = []
    for alert_data in alerts_data:
        alert = ForecastAlert(
            client_id=data.client_id,
            forecast_id=forecast.id,
            alert_type=alert_data["alert_type"],
            severity=alert_data["severity"],
            week_number=alert_data["week_number"],
            narrative=alert_data["narrative"],
        )
        db.add(alert)
        db_alerts.append(alert)

    db.commit()
    db.refresh(forecast)
    for line in db_lines:
        db.refresh(line)
    for alert in db_alerts:
        db.refresh(alert)

    return CashflowForecastDetail(
        forecast=forecast,
        lines=db_lines,
        alerts=db_alerts,
    )


@router.get("/forecasts", response_model=list[CashflowForecastResponse])
async def list_forecasts(
    client_id: Optional[int] = Query(None),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List forecasts, optionally filtered by client_id."""
    ctx = await get_current_user(credentials)

    query = db.query(CashflowForecast)
    if client_id is not None:
        query = query.filter(CashflowForecast.client_id == client_id)

    forecasts = query.order_by(CashflowForecast.created_at.desc()).all()
    return forecasts


@router.get("/forecasts/latest/{client_id}", response_model=CashflowForecastDetail)
async def get_latest_forecast(
    client_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get the latest published forecast for a client."""
    ctx = await get_current_user(credentials)

    forecast = (
        db.query(CashflowForecast)
        .filter(
            CashflowForecast.client_id == client_id,
            CashflowForecast.status == "published",
        )
        .order_by(CashflowForecast.created_at.desc())
        .first()
    )

    if not forecast:
        raise HTTPException(status_code=404, detail="No published forecast found for this client")

    lines = (
        db.query(CashflowForecastLine)
        .filter(CashflowForecastLine.forecast_id == forecast.id)
        .order_by(CashflowForecastLine.week_commencing)
        .all()
    )

    alerts = (
        db.query(ForecastAlert)
        .filter(ForecastAlert.forecast_id == forecast.id)
        .all()
    )

    return CashflowForecastDetail(
        forecast=forecast,
        lines=lines,
        alerts=alerts,
    )


@router.get("/forecasts/{forecast_id}", response_model=CashflowForecastDetail)
async def get_forecast(
    forecast_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get a specific forecast with its lines and alerts."""
    ctx = await get_current_user(credentials)

    forecast = db.query(CashflowForecast).filter(CashflowForecast.id == forecast_id).first()
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")

    lines = (
        db.query(CashflowForecastLine)
        .filter(CashflowForecastLine.forecast_id == forecast.id)
        .order_by(CashflowForecastLine.week_commencing)
        .all()
    )

    alerts = (
        db.query(ForecastAlert)
        .filter(ForecastAlert.forecast_id == forecast.id)
        .all()
    )

    return CashflowForecastDetail(
        forecast=forecast,
        lines=lines,
        alerts=alerts,
    )


@router.post("/forecasts/{forecast_id}/publish", response_model=CashflowForecastResponse)
async def publish_forecast(
    forecast_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Publish a draft forecast."""
    ctx = await get_current_user(credentials)

    forecast = db.query(CashflowForecast).filter(CashflowForecast.id == forecast_id).first()
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")

    if forecast.status == "published":
        raise HTTPException(status_code=400, detail="Forecast is already published")

    forecast.status = "published"
    db.commit()
    db.refresh(forecast)
    return forecast


@router.get("/alerts", response_model=ForecastAlertList)
async def list_alerts(
    client_id: Optional[int] = Query(None),
    severity: Optional[str] = Query(None),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List alerts with optional filters."""
    ctx = await get_current_user(credentials)

    query = db.query(ForecastAlert)
    if client_id is not None:
        query = query.filter(ForecastAlert.client_id == client_id)
    if severity is not None:
        query = query.filter(ForecastAlert.severity == severity)

    alerts = query.order_by(ForecastAlert.created_at.desc()).all()
    return ForecastAlertList(items=alerts, total=len(alerts))
