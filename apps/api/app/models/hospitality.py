from app.models.base import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Date, DateTime, Text


class HospitalityClient(BaseModel):
    __tablename__ = "hospitality_clients"

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, unique=True)
    pms_system = Column(String(50))  # opera/mews/protel/roomraccoon
    pms_api_key = Column(String(255), nullable=True)
    pms_property_id = Column(String(50), nullable=True)
    currency = Column(String(3), default="USD")
    financial_year_start = Column(Integer, default=1)


class RoomType(BaseModel):
    __tablename__ = "room_types"

    hospitality_client_id = Column(Integer, ForeignKey("hospitality_clients.id"), nullable=False)
    code = Column(String(20))
    name = Column(String(100))
    capacity = Column(Integer)
    avg_daily_rate = Column(Numeric(10, 2))


class DailyRevenue(BaseModel):
    __tablename__ = "daily_revenue"

    hospitality_client_id = Column(Integer, ForeignKey("hospitality_clients.id"), nullable=False)
    date = Column(Date, nullable=False)
    room_type_id = Column(Integer, ForeignKey("room_types.id"), nullable=True)
    revenue_stream = Column(String(50))  # room/fb/spa/other
    rooms_available = Column(Integer, default=0)
    rooms_occupied = Column(Integer, default=0)
    total_revenue = Column(Numeric(12, 2), default=0)


class GratuityTip(BaseModel):
    __tablename__ = "gratuity_tips"

    hospitality_client_id = Column(Integer, ForeignKey("hospitality_clients.id"), nullable=False)
    employee_id = Column(Integer, nullable=True)
    date = Column(Date, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    source = Column(String(50))  # credit_card/cash/room_service


class InventoryStockTake(BaseModel):
    __tablename__ = "inventory_stock_takes"

    hospitality_client_id = Column(Integer, ForeignKey("hospitality_clients.id"), nullable=False)
    date = Column(Date, nullable=False)
    item_code = Column(String(50))
    description = Column(String(255))
    quantity_counted = Column(Integer, default=0)
    quantity_expected = Column(Integer, default=0)
    unit_cost = Column(Numeric(10, 2), default=0)
    variance = Column(Numeric(12, 2), default=0)
