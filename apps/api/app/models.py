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


# ─── Sprint Tier 1.3: Jurisdictions & Audit ────────────────────────────────


class JurisdictionConfig(Base):
    """
    Per-client configuration that selects the jurisdiction module and stores
    client-level overrides. One row per client.

    The primary_jurisdiction field drives which JurisdictionEngine module is
    loaded for this client — NO, SE, or FI. Routers use it to look up VAT
    rates, payroll rules, filing calendars, etc.
    """
    __tablename__ = "jurisdiction_configs"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(
        Integer,
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    primary_jurisdiction = Column(String(3), nullable=False, index=True)
    secondary_jurisdictions = Column(String(255))
    reporting_currency = Column(String(3), nullable=False, default="NOK")
    vat_filing_frequency = Column(String(20))
    fiscal_year_start_month = Column(Integer, nullable=False, default=1)
    language = Column(String(10), nullable=False, default="en")
    config_overrides = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    client = relationship("Client")


class CashflowSnapshot(Base):
    """Stored 13-week cashflow forecast, captured at a point in time."""
    __tablename__ = "cashflow_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(
        Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_date = Column(DateTime(timezone=True), nullable=False, index=True)
    currency = Column(String(3), nullable=False)
    opening_balance_minor = Column(Integer, nullable=False)
    closing_balance_minor = Column(Integer, nullable=False)
    weeks_count = Column(Integer, nullable=False, default=13)
    threshold_minor = Column(Integer)
    breach_week_count = Column(Integer, nullable=False, default=0)
    weeks_json = Column(Text, nullable=False)
    narrative = Column(Text)
    narrative_language = Column(String(10))
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    client = relationship("Client")


class ReportDelivery(Base):
    """Tracks generation and delivery of a month-end report."""
    __tablename__ = "report_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(
        Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    report_type = Column(String(50), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    currency = Column(String(3), nullable=False)
    language = Column(String(10), nullable=False, default="en")
    pdf_path = Column(String(500))
    pdf_size_bytes = Column(Integer)
    status = Column(String(20), nullable=False, default="pending", index=True)
    recipient_email = Column(String(255))
    delivery_provider = Column(String(50))
    delivery_message_id = Column(String(255))
    delivery_error = Column(Text)
    scheduled_for = Column(DateTime(timezone=True), index=True)
    sent_at = Column(DateTime(timezone=True))
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    client = relationship("Client")


# ─── Tier 4: Hospitality vertical ────────────────────────────────────────


class Property(Base):
    """A hotel, guesthouse, or venue owned by a client."""
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(
        Integer, ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    name = Column(String(255), nullable=False)
    country = Column(String(3), nullable=False)
    total_rooms = Column(Integer, nullable=False, default=0)
    opening_date = Column(DateTime(timezone=True))
    timezone = Column(String(50), nullable=False, default="Europe/Oslo")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    client = relationship("Client")


class RoomCategory(Base):
    __tablename__ = "room_categories"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(
        Integer, ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    code = Column(String(20), nullable=False)
    label = Column(String(100), nullable=False)
    room_count = Column(Integer, nullable=False, default=0)
    base_rate_minor = Column(Integer, nullable=False, default=0)
    currency = Column(String(3), nullable=False)


class Outlet(Base):
    __tablename__ = "outlets"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(
        Integer, ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    name = Column(String(100), nullable=False)
    outlet_type = Column(String(30), nullable=False, index=True)


class DailyRevenueImport(Base):
    __tablename__ = "daily_revenue_imports"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(
        Integer, ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    import_date = Column(DateTime(timezone=True), nullable=False, index=True)
    rooms_sold = Column(Integer, nullable=False, default=0)
    rooms_available = Column(Integer, nullable=False, default=0)
    currency = Column(String(3), nullable=False)
    pms_name = Column(String(50))
    raw_reference = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DailyRevenueLine(Base):
    __tablename__ = "daily_revenue_lines"

    id = Column(Integer, primary_key=True, index=True)
    import_id = Column(
        Integer, ForeignKey("daily_revenue_imports.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    outlet_type = Column(String(30), nullable=False)
    gross_amount_minor = Column(Integer, nullable=False)
    cover_count = Column(Integer, nullable=False, default=0)


# ─── Tier 4: Professional Services vertical ──────────────────────────────


class Matter(Base):
    __tablename__ = "matters"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(
        Integer, ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    code = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    matter_type = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default="open", index=True)
    opened_on = Column(DateTime(timezone=True), nullable=False)
    closed_on = Column(DateTime(timezone=True))
    partner_in_charge = Column(Integer)
    billing_contact = Column(String(255))
    fixed_fee_minor = Column(Integer)
    retainer_balance_minor = Column(Integer)
    currency = Column(String(3), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    client = relationship("Client")


class FeeEarner(Base):
    __tablename__ = "fee_earners"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(
        Integer, ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    grade = Column(String(20), nullable=False, index=True)
    default_hourly_rate_minor = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BillingRate(Base):
    __tablename__ = "billing_rates"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    matter_id = Column(Integer, ForeignKey("matters.id", ondelete="CASCADE"), index=True)
    grade = Column(String(20))
    matter_type = Column(String(30))
    hourly_rate_minor = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True))


class WipEntry(Base):
    __tablename__ = "wip_entries"

    id = Column(Integer, primary_key=True, index=True)
    matter_id = Column(
        Integer, ForeignKey("matters.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    fee_earner_id = Column(
        Integer, ForeignKey("fee_earners.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    worked_on = Column(DateTime(timezone=True), nullable=False, index=True)
    hours = Column(Numeric(6, 2), nullable=False)
    hourly_rate_minor = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="unbilled", index=True)
    logged_at = Column(DateTime(timezone=True), server_default=func.now())
    billed_at = Column(DateTime(timezone=True))
    written_off_at = Column(DateTime(timezone=True))


class AuditLog(Base):
    """
    Immutable append-only log of significant state changes.

    Rows are never updated or deleted once written — this is enforced at the
    application layer (no update/delete routers) rather than database layer,
    so migrations and backups can still operate on the table normally.
    """
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(
        Integer, ForeignKey("agencies.id", ondelete="SET NULL"), index=True
    )
    client_id = Column(
        Integer, ForeignKey("clients.id", ondelete="SET NULL"), index=True
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    action = Column(String(50), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(String(50))
    diff = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    request_id = Column(String(64))
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
