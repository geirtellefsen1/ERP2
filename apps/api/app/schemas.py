from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


# ─── Agency ────────────────────────────────────────────────────────────────────

class AgencyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    subscription_tier: str = Field(default="starter")
    countries_enabled: str = Field(default="ZA,NO,UK")


class AgencyCreate(AgencyBase):
    pass


class AgencyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    subscription_tier: Optional[str] = None


class Agency(AgencyBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── User ──────────────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str = Field(default="agent")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    agency_id: int


class User(UserBase):
    id: int
    agency_id: int
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Client ────────────────────────────────────────────────────────────────────

class ClientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    registration_number: Optional[str] = None
    country: str = Field(default="ZA", pattern=r"^(ZA|NO|UK|EU)$")
    industry: Optional[str] = None
    fiscal_year_end: Optional[str] = None


class ClientCreate(ClientBase):
    agency_id: int


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    registration_number: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    is_active: Optional[bool] = None


class Client(ClientBase):
    id: int
    agency_id: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Client Contact ────────────────────────────────────────────────────────────

class ClientContactBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_primary: bool = False


class ClientContactCreate(ClientContactBase):
    client_id: int


class ClientContact(ClientContactBase):
    id: int
    client_id: int

    class Config:
        from_attributes = True


# ─── Invoice ──────────────────────────────────────────────────────────────────

class InvoiceLineItemBase(BaseModel):
    description: str
    quantity: Decimal = Field(default=Decimal("1"))
    unit_price: Decimal


class InvoiceLineItemCreate(InvoiceLineItemBase):
    pass


class InvoiceLineItem(InvoiceLineItemBase):
    id: int
    invoice_id: int
    total: Decimal

    class Config:
        from_attributes = True


class InvoiceBase(BaseModel):
    invoice_number: str = Field(..., min_length=1, max_length=50)
    status: str = Field(default="draft", pattern=r"^(draft|sent|paid|overdue)$")
    amount: Decimal
    currency: str = Field(default="ZAR", max_length=3)
    due_date: Optional[datetime] = None


class InvoiceCreate(InvoiceBase):
    client_id: int
    line_items: list[InvoiceLineItemCreate] = []


class InvoiceUpdate(BaseModel):
    status: Optional[str] = None


class Invoice(InvoiceBase):
    id: int
    client_id: int
    issued_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Transaction ───────────────────────────────────────────────────────────────

class TransactionBase(BaseModel):
    date: datetime
    description: Optional[str] = None
    amount: Decimal
    reference: Optional[str] = None


class TransactionCreate(TransactionBase):
    client_id: int


class Transaction(TransactionBase):
    id: int
    client_id: int
    matched: bool
    matched_invoice_id: Optional[int] = None

    class Config:
        from_attributes = True


# ─── Payroll Run ───────────────────────────────────────────────────────────────

class PayrollRunBase(BaseModel):
    period_start: datetime
    period_end: datetime


class PayrollRunCreate(PayrollRunBase):
    client_id: int


class PayrollRun(PayrollRunBase):
    id: int
    client_id: int
    status: str
    total_gross: Decimal
    total_paye: Decimal
    total_uif: Decimal
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
