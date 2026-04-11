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


# ─── Sprint 5: Chart of Accounts ─────────────────────────────────────────────

class Account(Base):
    """GL account — part of a client's chart of accounts"""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    account_type = Column(String(20), nullable=False)
    sub_type = Column(String(50))
    parent_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_control_account = Column(Boolean, default=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    client = relationship("Client")
    parent = relationship("Account", remote_side=[id], backref="children")


class JournalEntry(Base):
    """Double-entry journal entry"""
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    entry_date = Column(DateTime(timezone=True), nullable=False)
    description = Column(Text)
    reference = Column(String(100))
    posted_by = Column(Integer, ForeignKey("users.id"))
    is_reversal = Column(Boolean, default=False)
    reversed_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client")
    lines = relationship("JournalLine", back_populates="entry", cascade="all, delete-orphan")


class JournalLine(Base):
    """Line item of a journal entry"""
    __tablename__ = "journal_lines"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    debit = Column(Numeric(14, 2), default=0)
    credit = Column(Numeric(14, 2), default=0)
    description = Column(Text)

    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account")


# ─── Sprint 7: Bank Reconciliation ──────────────────────────────────────────────

class BankAccount(Base):
    """Bank account linked to a client"""
    __tablename__ = "bank_accounts"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    bank_name = Column(String(100))
    account_number = Column(String(50))
    account_type = Column(String(20))  # checking, savings
    currency = Column(String(3), default="ZAR")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client")
    transactions = relationship("BankTransaction", back_populates="account")


class BankTransaction(Base):
    """Individual bank transaction imported from Open Banking or manual"""
    __tablename__ = "bank_transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=False)
    external_id = Column(String(255))  # TrueLayer transaction ID
    date = Column(DateTime(timezone=True), nullable=False)
    description = Column(Text)
    amount = Column(Numeric(14, 2), nullable=False)  # positive = inflow, negative = outflow
    reference = Column(String(255))
    category = Column(String(100))  # e.g. "payroll", "invoice", "transfer"
    status = Column(String(20), default="unmatched")  # unmatched, matched, disputed
    matched_invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    matched_journal_line_id = Column(Integer, ForeignKey("journal_lines.id"), nullable=True)
    match_confidence = Column(Numeric(5, 4))  # 0.0 to 1.0
    match_reason = Column(Text)  # AI explanation
    imported_at = Column(DateTime(timezone=True), server_default=func.now())

    account = relationship("BankAccount", back_populates="transactions")


# ─── Sprint 9: Client Portal ───────────────────────────────────────────────────

class Document(Base):
    """Uploaded document for a client"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    file_path = Column(String(500))  # DO Spaces path
    file_size = Column(Integer)
    mime_type = Column(String(100))
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client")


# ─── Sprint 10: Document Intelligence ─────────────────────────────────────────

class DocumentIntelligence(Base):
    """AI-extracted data from a document"""
    __tablename__ = "document_intelligence"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    extraction_model = Column(String(50))  # aws_textract, claude_vision
    raw_text = Column(Text)
    extracted_data = Column(Text)  # JSON string
    confidence_score = Column(Numeric(5, 4))  # 0.0 to 1.0
    is_fraud_flagged = Column(Boolean, default=False)
    fraud_reasons = Column(Text)  # JSON array
    status = Column(String(20), default="pending")  # pending, processing, complete, failed
    processed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document")


# ─── Sprint 14: South Africa Payroll ──────────────────────────────────────────

class Employee(Base):
    """Employee at a client company"""
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    employee_number = Column(String(50), unique=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    id_number = Column(String(13))  # SA ID number
    tax_number = Column(String(10))
    uif_number = Column(String(10))
    employment_type = Column(String(20), default="permanent")  # permanent, contract, casual
    department = Column(String(100))
    position = Column(String(100))
    join_date = Column(DateTime(timezone=True))
    leave_date = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client")
    payslips = relationship("Payslip", back_populates="employee")


class PayrollPeriod(Base):
    """Payroll period definition"""
    __tablename__ = "payroll_periods"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default="open")  # open, processing, submitted, paid
    pay_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client")


class Payslip(Base):
    """Individual payslip for an employee in a payroll run"""
    __tablename__ = "payslips"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    payroll_run_id = Column(Integer, ForeignKey("payroll_runs.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("payroll_periods.id"), nullable=False)

    # Earnings
    gross_salary = Column(Numeric(12, 2), nullable=False)
    total_earnings = Column(Numeric(12, 2), nullable=False)

    # Deductions
    paye = Column(Numeric(12, 2), default=0)
    uif_employee = Column(Numeric(12, 2), default=0)
    uif_employer = Column(Numeric(12, 2), default=0)
    sdl = Column(Numeric(12, 2), default=0)
    pension = Column(Numeric(12, 2), default=0)
    medical_aid = Column(Numeric(12, 2), default=0)
    other_deductions = Column(Numeric(12, 2), default=0)

    # Net
    total_deductions = Column(Numeric(12, 2), nullable=False)
    net_salary = Column(Numeric(12, 2), nullable=False)

    # ETI (Employment Tax Incentive)
    eti_amount = Column(Numeric(12, 2), default=0)

    status = Column(String(20), default="draft")  # draft, approved, paid
    paid_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    employee = relationship("Employee", back_populates="payslips")


# ─── Sprint 15: Norway Payroll ──────────────────────────────────────────────────

class EmployeeNO(Base):
    """Norwegian employee with tax card and OTP data"""
    __tablename__ = "employees_no"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    national_id = Column(String(11))  # 11-digit fødselsnummer or D-nummer
    tax_withholding_table = Column(String(10))  # Skattekort tabellnummer
    basis_tax = Column(Numeric(12, 2))  # Skattetrekksgrunnlag
    employee_type = Column(String(20))  # primary, secondary, pensioner
    account_number = Column(String(11))  # Norwegian bank account
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client")


class HolidayAccumulation(Base):
    """Holiday pay accumulation tracking per employee"""
    __tablename__ = "holiday_accumulations"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees_no.id"), nullable=False)
    year = Column(Integer, nullable=False)
    days_accumulated = Column(Numeric(5, 2), default=0)  # days
    days_taken = Column(Numeric(5, 2), default=0)
    holiday_pay_rate = Column(Numeric(4, 3), default=Decimal("0.124"))  # 12.4% of gross
    carried_forward = Column(Numeric(5, 2), default=0)  # days carried from prev year
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    employee = relationship("EmployeeNO")


# ─── Sprint 16: Leave Management ───────────────────────────────────────────────

class LeaveType(Base):
    __tablename__ = "leave_types"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)  # Annual, Sick, Maternity, etc.
    country = Column(String(3))  # ZA, NO, UK
    default_days = Column(Integer, default=0)
    paid = Column(Boolean, default=True)

class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, nullable=False)  # Works for both ZA and NO employees
    leave_type_id = Column(Integer, ForeignKey("leave_types.id"), nullable=False)
    year = Column(Integer, nullable=False)
    entitled_days = Column(Numeric(5, 2), default=0)
    used_days = Column(Numeric(5, 2), default=0)
    pending_days = Column(Numeric(5, 2), default=0)

class LeaveApplication(Base):
    __tablename__ = "leave_applications"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, nullable=False)
    leave_type_id = Column(Integer, ForeignKey("leave_types.id"), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    days_requested = Column(Numeric(5, 2), nullable=False)
    status = Column(String(20), default="pending")  # pending, approved, rejected
    approved_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── Sprint 17: Statutory Filing ──────────────────────────────────────────────

class TaxFiling(Base):
    """Statutory tax filing (VAT, PAYE, A-melding)"""
    __tablename__ = "tax_filings"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    filing_type = Column(String(30), nullable=False)  # vat_sa, paye_sa, amelding_no, vat_uk
    period_year = Column(Integer, nullable=False)
    period_month = Column(Integer, nullable=False)
    amount = Column(Numeric(14, 2), default=0)
    status = Column(String(20), default="draft")  # draft, filed, accepted, rejected
    filed_at = Column(DateTime(timezone=True))
    reference = Column(String(100))  # Filing reference from tax authority
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client")


# ─── Sprint 18: Hospitality Module ────────────────────────────────────────────

class PMSConnection(Base):
    """PMS (Property Management System) integration"""
    __tablename__ = "pms_connections"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    pms_type = Column(String(50))  # opera, micros, cloudbeds, etc.
    api_key = Column(String(255))
    property_id = Column(String(100))
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client")


class RoomType(Base):
    __tablename__ = "room_types"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String(100))  # Standard Room, Suite, Deluxe
    short_code = Column(String(10))
    total_rooms = Column(Integer, default=0)


class DailyRevenue(Base):
    """Daily room revenue snapshot"""
    __tablename__ = "daily_revenue"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    room_type_id = Column(Integer, ForeignKey("room_types.id"))
    rooms_sold = Column(Integer, default=0)
    average_rate = Column(Numeric(10, 2), default=0)  # ADR
    revpar = Column(Numeric(10, 2), default=0)  # Revenue Per Available Room
    food_revenue = Column(Numeric(12, 2), default=0)
    beverage_revenue = Column(Numeric(12, 2), default=0)
    other_revenue = Column(Numeric(12, 2), default=0)
    total_revenue = Column(Numeric(12, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── Sprint 19: Professional Services ─────────────────────────────────────────

class Matter(Base):
    """Legal/consulting matter"""
    __tablename__ = "matters"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    matter_number = Column(String(20), unique=True, nullable=False)
    title = Column(String(255))
    type = Column(String(50))  # litigation, advisory, corporate, tax
    rate_type = Column(String(20))  # fixed, hourly, contingency
    hourly_rate = Column(Numeric(12, 2))
    trust_account = Column(String(50))  # Trust account number
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client")


class TimeEntry(Base):
    __tablename__ = "time_entries"

    id = Column(Integer, primary_key=True, index=True)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    employee_id = Column(Integer, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    hours = Column(Numeric(5, 2), nullable=False)
    rate = Column(Numeric(12, 2), nullable=False)
    description = Column(Text)
    invoiced = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TrustTransaction(Base):
    __tablename__ = "trust_transactions"

    id = Column(Integer, primary_key=True, index=True)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    transaction_type = Column(String(20))  # deposit, withdrawal, transfer
    amount = Column(Numeric(12, 2), nullable=False)
    reference = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
