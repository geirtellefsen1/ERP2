from sqlalchemy.orm import Session
from app.models import Agency, User, Client, ClientContact, Account, Invoice, InvoiceLineItem, Transaction
from datetime import datetime, timezone, timedelta
from passlib.hash import bcrypt


def seed_database(db: Session):
    """Seed database with initial development data."""

    # Check if already seeded
    if db.query(Agency).first():
        print("Database already seeded, skipping.")
        return

    # --- Agency ---
    agency = Agency(
        name="Saga Advisory AS",
        slug="saga-advisory",
        subscription_tier="enterprise",
        countries_enabled="ZA,NO,UK,EU",
    )
    db.add(agency)
    db.flush()

    # --- Users ---
    admin = User(
        agency_id=agency.id,
        email="admin@sagaadvisory.no",
        hashed_password=bcrypt.hash("admin123"),
        full_name="Admin User",
        role="admin",
        is_active=True,
        auth0_id="auth0|dev_admin",
    )
    agent = User(
        agency_id=agency.id,
        email="agent@sagaadvisory.no",
        hashed_password=bcrypt.hash("agent123"),
        full_name="Agent Smith",
        role="agent",
        is_active=True,
        auth0_id="auth0|dev_agent",
    )
    db.add_all([admin, agent])
    db.flush()

    # --- Clients ---
    client_za = Client(
        agency_id=agency.id,
        name="Cape Hospitality Group",
        registration_number="2020/123456/07",
        country="ZA",
        industry="hospitality",
        fiscal_year_end="2025-02-28",
        is_active=True,
        health_score="good",
    )
    client_no = Client(
        agency_id=agency.id,
        name="Nordic Fish AS",
        registration_number="NO-987654321",
        country="NO",
        industry="aquaculture",
        fiscal_year_end="2025-12-31",
        is_active=True,
        health_score="excellent",
    )
    db.add_all([client_za, client_no])
    db.flush()

    # --- Client Contacts ---
    contact_za = ClientContact(
        client_id=client_za.id,
        name="John Mbeki",
        email="john@capehospitality.co.za",
        phone="+27821234567",
        role="CFO",
        is_primary=True,
    )
    contact_no = ClientContact(
        client_id=client_no.id,
        name="Lars Hansen",
        email="lars@nordicfish.no",
        phone="+4798765432",
        role="Finance Manager",
        is_primary=True,
    )
    db.add_all([contact_za, contact_no])
    db.flush()

    # --- Accounts (CoA for ZA client) ---
    accounts_data = [
        ("1000", "Cash and Cash Equivalents", "asset"),
        ("1100", "Accounts Receivable", "asset"),
        ("1200", "Inventory", "asset"),
        ("2000", "Accounts Payable", "liability"),
        ("2100", "VAT Payable", "liability"),
        ("3000", "Share Capital", "equity"),
        ("3100", "Retained Earnings", "equity"),
        ("4000", "Revenue", "revenue"),
        ("4100", "Room Revenue", "revenue"),
        ("4200", "F&B Revenue", "revenue"),
        ("5000", "Cost of Sales", "expense"),
        ("5100", "Salaries & Wages", "expense"),
        ("5200", "Rent", "expense"),
        ("5300", "Utilities", "expense"),
    ]
    account_objs = {}
    for acc_num, acc_name, acc_type in accounts_data:
        acc = Account(
            agency_id=agency.id,
            client_id=client_za.id,
            account_number=acc_num,
            name=acc_name,
            account_type=acc_type,
            is_active="active",
            balance=0,
        )
        db.add(acc)
        db.flush()
        account_objs[acc_num] = acc

    # --- Invoice ---
    invoice = Invoice(
        client_id=client_za.id,
        invoice_number="INV-2025-001",
        status="sent",
        amount=15000.00,
        currency="ZAR",
        due_date=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(invoice)
    db.flush()

    line1 = InvoiceLineItem(
        invoice_id=invoice.id,
        description="Monthly bookkeeping",
        quantity=1,
        unit_price=10000.00,
        total=10000.00,
    )
    line2 = InvoiceLineItem(
        invoice_id=invoice.id,
        description="Payroll processing (25 employees)",
        quantity=1,
        unit_price=5000.00,
        total=5000.00,
    )
    db.add_all([line1, line2])
    db.flush()

    # --- Transactions ---
    now = datetime.now(timezone.utc)
    txns = [
        Transaction(
            agency_id=agency.id,
            client_id=client_za.id,
            account_id=account_objs["1000"].id,
            transaction_date=now - timedelta(days=5),
            description="Client deposit received",
            amount=50000.00,
            debit_amount=50000.00,
            credit_amount=0,
            reference="DEP-001",
            transaction_type="bank",
            status="posted",
            matched=False,
        ),
        Transaction(
            agency_id=agency.id,
            client_id=client_za.id,
            account_id=account_objs["5100"].id,
            transaction_date=now - timedelta(days=3),
            description="Salary payment - March 2025",
            amount=35000.00,
            debit_amount=35000.00,
            credit_amount=0,
            reference="SAL-MAR-2025",
            transaction_type="payment",
            status="posted",
            matched=False,
        ),
        Transaction(
            agency_id=agency.id,
            client_id=client_za.id,
            account_id=account_objs["4000"].id,
            transaction_date=now - timedelta(days=1),
            description="Room booking revenue",
            amount=12500.00,
            debit_amount=0,
            credit_amount=12500.00,
            reference="REV-001",
            transaction_type="journal",
            status="posted",
            matched=False,
        ),
    ]
    db.add_all(txns)

    db.commit()
    print("Database seeded successfully with development data.")
