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
    vat_number: Optional[str] = None
    country: str = Field(default="NO", pattern=r"^(NO|SE|FI|UK|EU|ZA)$")
    industry: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    default_currency: str = Field(default="NOK", max_length=3)


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    registration_number: Optional[str] = None
    vat_number: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    default_currency: Optional[str] = None
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
    vat_rate: Decimal = Field(default=Decimal("25"))


class InvoiceLineItemCreate(InvoiceLineItemBase):
    pass


class InvoiceLineItem(InvoiceLineItemBase):
    id: int
    invoice_id: int
    vat_amount: Decimal
    total: Decimal

    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    client_id: int
    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_email: Optional[str] = None
    customer_address: Optional[str] = None
    customer_org_number: Optional[str] = None
    currency: str = Field(default="NOK", max_length=3)
    reference: Optional[str] = None
    payment_terms_days: int = Field(default=30)
    notes: Optional[str] = None
    line_items: list[InvoiceLineItemCreate] = []


class InvoiceUpdate(BaseModel):
    status: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_address: Optional[str] = None
    customer_org_number: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


class Invoice(BaseModel):
    id: int
    client_id: int
    invoice_number: str
    status: str
    currency: str
    subtotal: Decimal
    vat_amount: Decimal
    amount: Decimal
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_address: Optional[str] = None
    customer_org_number: Optional[str] = None
    reference: Optional[str] = None
    payment_terms_days: Optional[int] = None
    notes: Optional[str] = None
    due_date: Optional[datetime] = None
    issued_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Expense ──────────────────────────────────────────────────────────────────

class ExpenseCreate(BaseModel):
    client_id: int
    vendor_name: str = Field(..., min_length=1, max_length=255)
    vendor_org_number: Optional[str] = None
    description: Optional[str] = None
    date: datetime
    due_date: Optional[datetime] = None
    amount: Decimal
    vat_amount: Decimal = Field(default=Decimal("0"))
    vat_rate: Decimal = Field(default=Decimal("25"))
    currency: str = Field(default="NOK", max_length=3)
    category: Optional[str] = None
    account_id: Optional[int] = None
    inbox_item_id: Optional[int] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None


class ExpenseUpdate(BaseModel):
    status: Optional[str] = None
    vendor_name: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None
    category: Optional[str] = None
    account_id: Optional[int] = None
    notes: Optional[str] = None


class Expense(BaseModel):
    id: int
    client_id: int
    vendor_name: str
    vendor_org_number: Optional[str] = None
    description: Optional[str] = None
    date: datetime
    due_date: Optional[datetime] = None
    amount: Decimal
    vat_amount: Decimal
    vat_rate: Decimal
    currency: str
    category: Optional[str] = None
    status: str
    account_id: Optional[int] = None
    inbox_item_id: Optional[int] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

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
