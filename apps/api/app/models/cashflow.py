from app.models.base import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Date, DateTime, Boolean, Text
from sqlalchemy.sql import func


class CashflowForecast(BaseModel):
    __tablename__ = "cashflow_forecasts"

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    forecast_date = Column(Date, nullable=False)
    forecast_generated_at = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(Date)
    status = Column(String(20), default="draft")  # draft/published


class CashflowForecastLine(BaseModel):
    __tablename__ = "cashflow_forecast_lines"

    forecast_id = Column(Integer, ForeignKey("cashflow_forecasts.id"), nullable=False)
    week_commencing = Column(Date, nullable=False)
    opening_balance = Column(Numeric(15, 2), default=0)
    receipts = Column(Numeric(15, 2), default=0)
    payments = Column(Numeric(15, 2), default=0)
    closing_balance = Column(Numeric(15, 2), default=0)
    alert_flag = Column(Boolean, default=False)


class ForecastAlert(BaseModel):
    __tablename__ = "forecast_alerts"

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    forecast_id = Column(Integer, ForeignKey("cashflow_forecasts.id"), nullable=False)
    alert_type = Column(String(20))  # low_balance/negative/volatility
    severity = Column(String(20))  # info/warning/critical
    week_number = Column(Integer)
    narrative = Column(Text, nullable=True)
