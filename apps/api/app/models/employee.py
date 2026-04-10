from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Boolean
from app.models.base import BaseModel


class Employee(BaseModel):
    """Employee record for payroll processing."""
    __tablename__ = "employees"

    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    employee_number = Column(String(50))
    full_name = Column(String(255), nullable=False)
    id_number = Column(String(20), nullable=True)  # SA ID
    tax_number = Column(String(20), nullable=True)
    monthly_salary = Column(Numeric(12, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    country = Column(String(10), default="ZA")
