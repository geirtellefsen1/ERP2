# BPO Nexus — SQLAlchemy Models
# Sprint 2 will add Alembic migrations; these are the target schema

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Text, Numeric
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Agency(Base):
    """BPO Agency (the customer — the BPO firm itself)"""
    __tablename__ = "agencies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    subscription_tier = Column(String(50), default="starter")  # starter, growth, enterprise
    countries_enabled = Column(String(255), default="ZA,NO,UK")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    clients = relationship("Client", back_populates="agency")
    users = relationship("User", back_populates="agency")


class Client(Base):
    """Client company managed by the BPO agency"""
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    registration_number = Column(String(100))
    country = Column(String(3))  # ZA, NO, UK, EU
    industry = Column(String(100))
    fiscal_year_end = Column(String(10))  # e.g. "2024-12-31"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    agency = relationship("Agency", back_populates="clients")
    contacts = relationship("ClientContact", back_populates="client")
    invoices = relationship("Invoice", back_populates="client")
    transactions = relationship("Transaction", back_populates="client")
    payroll_runs = relationship("PayrollRun", back_populates="client")


class User(Base):
    """User (BPO agent or client user)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50))  # admin, agent, client_admin, client_user
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    agency = relationship("Agency", back_populates="users")


class ClientContact(Base):
    """Contact person at a client company"""
    __tablename__ = "client_contacts"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    role = Column(String(100))
    is_primary = Column(Boolean, default=False)

    client = relationship("Client", back_populates="contacts")


class Invoice(Base):
    """Invoice issued by BPO agency to client"""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    invoice_number = Column(String(50), unique=True, nullable=False)
    status = Column(String(50), default="draft")  # draft, sent, paid, overdue
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="ZAR")
    due_date = Column(DateTime(timezone=True))
    issued_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice")


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(10, 2), default=1)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total = Column(Numeric(12, 2), nullable=False)

    invoice = relationship("Invoice", back_populates="line_items")


class Transaction(Base):
    """Bank transaction linked to a client"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    description = Column(Text)
    amount = Column(Numeric(12, 2), nullable=False)  # positive = debit, negative = credit
    reference = Column(String(255))
    matched = Column(Boolean, default=False)
    matched_invoice_id = Column(Integer, ForeignKey("invoices.id"))

    client = relationship("Client", back_populates="transactions")


class PayrollRun(Base):
    """Payroll run for a client"""
    __tablename__ = "payroll_runs"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), default="draft")  # draft, processing, submitted, paid
    total_gross = Column(Numeric(12, 2), default=0)
    total_paye = Column(Numeric(12, 2), default=0)
    total_uif = Column(Numeric(12, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="payroll_runs")


class OnboardingProgress(Base):
    """Tracks onboarding wizard progress per agency."""
    __tablename__ = "onboarding_progress"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    current_step = Column(Integer, nullable=False, default=1)  # 1-5
    step_data = Column(Text)  # JSON blob for partial form data
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    agency = relationship("Agency")
