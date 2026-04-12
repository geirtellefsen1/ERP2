"""
BPO Nexus / ClaudERP — Demo Seed Script
========================================

Populates the database with realistic test data so the deployed app feels
"alive" instead of empty. Safe to run multiple times — checks for the demo
agency by slug and exits early if it already exists.

Run inside the API container:
    docker run --rm --env-file /etc/claud-erp/.env \\
      registry.digitalocean.com/claud-erp/api:<TAG> \\
      python scripts/seed.py

Or locally (with .env loaded):
    cd apps/api && python scripts/seed.py

Force re-seed (wipes existing demo agency and all dependent data):
    docker run --rm --env-file /etc/claud-erp/.env \\
      --network claud-erp \\
      registry.digitalocean.com/claud-erp/api:<TAG> \\
      python scripts/seed.py --force

Use --force when a previous seed was interrupted (e.g. before migration
004 was applied) and left an empty demo agency with no clients.

Login credentials created:
    Email:    demo@claud-erp.com
    Password: demo1234

⚠ This is DEMO data. Change the password before exposing the deployment.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import sys
import os

# Allow running as `python scripts/seed.py` from /app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    Agency,
    User,
    Client,
    ClientContact,
    Account,
    Invoice,
    InvoiceLineItem,
    JournalEntry,
    JournalLine,
    BankAccount,
    BankTransaction,
    Employee,
    PayrollPeriod,
    PayrollRun,
    Payslip,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
NOW = datetime.now(timezone.utc)


def utc(days_offset: int = 0) -> datetime:
    return NOW + timedelta(days=days_offset)


def D(value) -> Decimal:
    return Decimal(str(value))


# ─── Seed Definitions ─────────────────────────────────────────────────────────

CLIENTS = [
    {
        "name": "Acme Corporation",
        "country": "ZA",
        "industry": "Hospitality",
        "registration_number": "2018/123456/07",
        "contacts": [
            {"name": "Sarah Mokoena", "email": "sarah@acme.co.za", "phone": "+27821234567", "role": "CFO", "is_primary": True},
            {"name": "James Naidoo", "email": "james@acme.co.za", "phone": "+27822345678", "role": "Operations Manager"},
        ],
    },
    {
        "name": "TechStart Ltd",
        "country": "UK",
        "industry": "Software",
        "registration_number": "12345678",
        "contacts": [
            {"name": "Emily Hartwell", "email": "emily@techstart.co.uk", "phone": "+447700900123", "role": "Founder", "is_primary": True},
        ],
    },
    {
        "name": "BuildRight SA",
        "country": "ZA",
        "industry": "Construction",
        "registration_number": "2015/987654/07",
        "contacts": [
            {"name": "Pieter van der Merwe", "email": "pieter@buildright.co.za", "phone": "+27839876543", "role": "Director", "is_primary": True},
        ],
    },
    {
        "name": "Green Valley Foods",
        "country": "ZA",
        "industry": "Agriculture",
        "registration_number": "2020/445566/07",
        "contacts": [
            {"name": "Thandi Dlamini", "email": "thandi@greenvalley.co.za", "phone": "+27845556677", "role": "Owner", "is_primary": True},
        ],
    },
    {
        "name": "Nordic Logistics AS",
        "country": "NO",
        "industry": "Transport",
        "registration_number": "987654321",
        "contacts": [
            {"name": "Erik Johansen", "email": "erik@nordiclog.no", "phone": "+4798765432", "role": "CEO", "is_primary": True},
            {"name": "Astrid Larsen", "email": "astrid@nordiclog.no", "phone": "+4798112233", "role": "Finance Manager"},
        ],
    },
]

# Standard SA chart of accounts (small set)
CHART_OF_ACCOUNTS = [
    ("1000", "Bank — Current Account", "asset", "current_asset"),
    ("1100", "Accounts Receivable", "asset", "current_asset"),
    ("1500", "Property, Plant & Equipment", "asset", "non_current_asset"),
    ("2000", "Accounts Payable", "liability", "current_liability"),
    ("2100", "VAT Payable", "liability", "current_liability"),
    ("2500", "Long-term Loans", "liability", "non_current_liability"),
    ("3000", "Owner's Equity", "equity", "equity"),
    ("3500", "Retained Earnings", "equity", "equity"),
    ("4000", "Service Revenue", "revenue", "operating_revenue"),
    ("4100", "Product Sales", "revenue", "operating_revenue"),
    ("5000", "Salaries & Wages", "expense", "operating_expense"),
    ("5100", "Rent Expense", "expense", "operating_expense"),
    ("5200", "Software & Subscriptions", "expense", "operating_expense"),
    ("5300", "Travel & Entertainment", "expense", "operating_expense"),
    ("5400", "Marketing", "expense", "operating_expense"),
    ("5500", "Professional Services", "expense", "operating_expense"),
]

INVOICES = [
    # (client_index, invoice_number, status, amount, days_offset_due, lines)
    (0, "INV-2026-0001", "paid",    15000.00, -25, [("Monthly bookkeeping — March 2026", 1, 12000.00), ("VAT submission", 1, 3000.00)]),
    (0, "INV-2026-0002", "sent",    18500.00,  10, [("Monthly bookkeeping — April 2026", 1, 12000.00), ("Annual financial statements", 1, 6500.00)]),
    (1, "INV-2026-0003", "paid",     8500.00, -15, [("Q1 management accounts", 1, 8500.00)]),
    (1, "INV-2026-0004", "sent",     8500.00,  20, [("Q2 management accounts", 1, 8500.00)]),
    (2, "INV-2026-0005", "overdue", 22000.00, -35, [("Bookkeeping Jan–Mar 2026", 3, 6000.00), ("Tax planning consultation", 1, 4000.00)]),
    (2, "INV-2026-0006", "draft",   12500.00,  30, [("Bookkeeping April 2026", 1, 6500.00), ("VAT submission", 1, 3000.00), ("Year-end planning", 1, 3000.00)]),
    (3, "INV-2026-0007", "paid",     4200.00, -10, [("Monthly bookkeeping — March 2026", 1, 4200.00)]),
    (3, "INV-2026-0008", "sent",     4200.00,  18, [("Monthly bookkeeping — April 2026", 1, 4200.00)]),
    (4, "INV-2026-0009", "paid",    32000.00, -20, [("Q1 financial statements", 1, 18000.00), ("Norwegian VAT (MVA) submissions x3", 3, 4000.00), ("Payroll setup", 1, 2000.00)]),
    (4, "INV-2026-0010", "sent",    14000.00,  15, [("Monthly bookkeeping & payroll — April", 1, 14000.00)]),
]

BANK_TRANSACTIONS = [
    # (client_index, days_offset, description, amount, status, reference)
    (0, -25, "PAYMENT FROM ACME CORP",        15000.00, "matched",   "INV-2026-0001"),
    (0,  -8, "ADOBE CREATIVE CLOUD",            -899.00, "matched",   "Adobe sub"),
    (0,  -7, "WOOLWORTHS — OFFICE SUPPLIES",    -350.00, "unmatched", None),
    (0,  -5, "UBER TRIP",                       -185.00, "unmatched", None),
    (1, -15, "WIRE FROM TECHSTART LTD",        8500.00, "matched",   "INV-2026-0003"),
    (1,  -3, "GOOGLE WORKSPACE",               -1200.00, "matched",   "Workspace sub"),
    (2, -28, "EFT FROM BUILDRIGHT SA — PARTIAL",10000.00, "matched", "INV-2026-0005"),
    (2,  -2, "UNKNOWN EFT REFERENCE",          5200.00, "unmatched", None),
    (3, -10, "GREEN VALLEY EFT",               4200.00, "matched",   "INV-2026-0007"),
    (4, -20, "SWIFT TRANSFER NORDIC LOGISTICS",32000.00, "matched",  "INV-2026-0009"),
    (4,  -4, "MAILCHIMP",                       -540.00, "matched",  "Marketing sub"),
    (4,  -1, "OFFICE RENT — CAPE TOWN",       -18000.00, "matched",  "Monthly rent"),
]

EMPLOYEES = [
    # All for client index 0 (Acme Corporation, SA)
    {"first_name": "Sarah",   "last_name": "Mokoena",     "id_number": "8501015800087", "department": "Finance",     "position": "CFO",            "salary": 45000},
    {"first_name": "James",   "last_name": "Naidoo",      "id_number": "8806127900088", "department": "Operations",  "position": "Ops Manager",    "salary": 32000},
    {"first_name": "Lerato",  "last_name": "Sithole",     "id_number": "9203145600089", "department": "Sales",       "position": "Sales Lead",     "salary": 28000},
    {"first_name": "David",   "last_name": "Chen",        "id_number": "8910238700090", "department": "Engineering", "position": "Senior Engineer","salary": 38000},
    {"first_name": "Nomsa",   "last_name": "Khumalo",     "id_number": "9407165400091", "department": "HR",          "position": "HR Officer",     "salary": 22000},
    {"first_name": "Michael", "last_name": "van Wyk",     "id_number": "8512094300092", "department": "Engineering", "position": "DevOps Engineer","salary": 35000},
]


# ─── PAYE & UIF helpers (simplified 2026 SA tax) ──────────────────────────────

def calc_paye(monthly_gross: float) -> float:
    """Simplified PAYE — 2026 SA tax brackets, primary rebate only."""
    annual = monthly_gross * 12
    if annual <= 237100:
        tax = annual * 0.18
    elif annual <= 370500:
        tax = 42678 + (annual - 237100) * 0.26
    elif annual <= 512800:
        tax = 77362 + (annual - 370500) * 0.31
    elif annual <= 673000:
        tax = 121475 + (annual - 512800) * 0.36
    else:
        tax = 179147 + (annual - 673000) * 0.39
    rebate = 17235  # primary rebate 2026
    annual_tax = max(0, tax - rebate)
    return round(annual_tax / 12, 2)


def calc_uif(monthly_gross: float) -> tuple[float, float]:
    """UIF — 1% employee + 1% employer, capped at R177.12 each."""
    capped = min(monthly_gross, 17712)
    contrib = round(capped * 0.01, 2)
    return contrib, contrib


def calc_sdl(monthly_gross: float) -> float:
    """SDL — 1% of gross, only if monthly gross >= R6,600."""
    if monthly_gross < 6600:
        return 0.0
    return round(monthly_gross * 0.01, 2)


# ─── Wipe helper (used by --force) ────────────────────────────────────────────

def wipe_demo_data(db: Session) -> bool:
    """
    Delete the ClaudERP demo agency and all dependent rows in reverse
    dependency order. Returns True if anything was deleted.

    Uses raw SQL with explicit cascading so it works even if a migration
    didn't set ON DELETE CASCADE on some foreign keys.
    """
    from sqlalchemy import text

    result = db.execute(
        text("SELECT id FROM agencies WHERE slug = :slug"),
        {"slug": "claud-erp-demo"},
    ).first()
    if not result:
        print("ℹ No existing demo agency found — nothing to wipe.")
        return False

    agency_id = result[0]
    print(f"⚠ --force: wiping existing demo agency (id={agency_id}) and all dependent rows...")

    # Fetch client IDs so we can scope the nested deletes
    client_rows = db.execute(
        text("SELECT id FROM clients WHERE agency_id = :aid"),
        {"aid": agency_id},
    ).fetchall()
    client_ids = [r[0] for r in client_rows]

    # Delete in strict reverse dependency order. Each DELETE is wrapped in
    # a try/except because some tables may not exist in older databases
    # (e.g. if migration 004 hasn't run yet).
    def safe_exec(sql: str, params: dict | None = None):
        try:
            db.execute(text(sql), params or {})
        except Exception as e:
            # Table might not exist — log and continue
            print(f"   (skipped: {sql[:60]}... — {type(e).__name__})")
            db.rollback()
            # Re-open transaction — SQLAlchemy auto-begins on next execute

    if client_ids:
        ids_csv = ",".join(str(i) for i in client_ids)

        # Payroll chain (Sprint 14 tables — may not exist pre-migration 004)
        safe_exec(
            f"DELETE FROM payslips WHERE employee_id IN "
            f"(SELECT id FROM employees WHERE client_id IN ({ids_csv}))"
        )
        safe_exec(f"DELETE FROM payroll_periods WHERE client_id IN ({ids_csv})")
        safe_exec(f"DELETE FROM employees WHERE client_id IN ({ids_csv})")
        safe_exec(f"DELETE FROM payroll_runs WHERE client_id IN ({ids_csv})")

        # Document chain (Sprint 9/10 — may not exist pre-migration 004)
        safe_exec(
            f"DELETE FROM document_intelligence WHERE document_id IN "
            f"(SELECT id FROM documents WHERE client_id IN ({ids_csv}))"
        )
        safe_exec(f"DELETE FROM documents WHERE client_id IN ({ids_csv})")

        # Banking chain
        safe_exec(
            f"DELETE FROM bank_transactions WHERE account_id IN "
            f"(SELECT id FROM bank_accounts WHERE client_id IN ({ids_csv}))"
        )
        safe_exec(f"DELETE FROM bank_accounts WHERE client_id IN ({ids_csv})")

        # Journal chain
        safe_exec(
            f"DELETE FROM journal_lines WHERE entry_id IN "
            f"(SELECT id FROM journal_entries WHERE client_id IN ({ids_csv}))"
        )
        safe_exec(f"DELETE FROM journal_entries WHERE client_id IN ({ids_csv})")
        safe_exec(f"DELETE FROM accounts WHERE client_id IN ({ids_csv})")

        # Invoices chain
        safe_exec(
            f"DELETE FROM invoice_line_items WHERE invoice_id IN "
            f"(SELECT id FROM invoices WHERE client_id IN ({ids_csv}))"
        )
        safe_exec(f"DELETE FROM invoices WHERE client_id IN ({ids_csv})")

        # Generic transactions (Sprint 2 table)
        safe_exec(f"DELETE FROM transactions WHERE client_id IN ({ids_csv})")

        # Client contacts + clients themselves
        safe_exec(f"DELETE FROM client_contacts WHERE client_id IN ({ids_csv})")
        safe_exec(f"DELETE FROM clients WHERE agency_id = :aid", {"aid": agency_id})

    # Users, then agency itself
    safe_exec("DELETE FROM users WHERE agency_id = :aid", {"aid": agency_id})
    safe_exec("DELETE FROM agencies WHERE id = :aid", {"aid": agency_id})

    db.commit()
    print("✅ Demo agency wiped. Ready to re-seed.\n")
    return True


# ─── Main seed routine ────────────────────────────────────────────────────────

def seed(db: Session, force: bool = False):
    print("\n🌱 BPO Nexus / ClaudERP — Demo Seed\n" + "─" * 48)

    if force:
        wipe_demo_data(db)

    # 1. Agency (idempotency check)
    existing = db.query(Agency).filter(Agency.slug == "claud-erp-demo").first()
    if existing:
        # Count how many clients actually belong to this agency
        client_count = db.query(Client).filter(Client.agency_id == existing.id).count()
        print(f"✅ Demo agency already exists (id={existing.id}, clients={client_count}).")
        if client_count == 0:
            print("   ⚠ Agency has 0 clients — a previous seed was interrupted.")
            print("   Run again with --force to wipe and re-seed:")
            print("     python scripts/seed.py --force")
        else:
            print("   Nothing to do. Run with --force to wipe and re-seed from scratch.")
        return

    agency = Agency(
        name="ClaudERP Demo Agency",
        slug="claud-erp-demo",
        subscription_tier="growth",
        countries_enabled="ZA,NO,UK",
    )
    db.add(agency)
    db.flush()
    print(f"✅ Agency: {agency.name} (id={agency.id})")

    # 2. Admin user
    admin = User(
        agency_id=agency.id,
        email="demo@claud-erp.com",
        hashed_password=pwd_context.hash("demo1234"),
        full_name="Demo Admin",
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.flush()
    print(f"✅ Admin user: demo@claud-erp.com / demo1234 (id={admin.id})")

    # 3. Clients + contacts
    client_objs = []
    for c in CLIENTS:
        client = Client(
            agency_id=agency.id,
            name=c["name"],
            country=c["country"],
            industry=c["industry"],
            registration_number=c["registration_number"],
            fiscal_year_end="2026-12-31",
            is_active=True,
        )
        db.add(client)
        db.flush()
        client_objs.append(client)
        for ct in c["contacts"]:
            db.add(ClientContact(
                client_id=client.id,
                name=ct["name"],
                email=ct["email"],
                phone=ct["phone"],
                role=ct["role"],
                is_primary=ct.get("is_primary", False),
            ))
    print(f"✅ Clients: {len(client_objs)}")
    print(f"✅ Contacts: {sum(len(c['contacts']) for c in CLIENTS)}")

    # 4. Chart of accounts (per client)
    account_lookup: dict[tuple[int, str], Account] = {}
    for client in client_objs:
        for code, name, atype, sub in CHART_OF_ACCOUNTS:
            acc = Account(
                client_id=client.id,
                code=code,
                name=name,
                account_type=atype,
                sub_type=sub,
                is_active=True,
            )
            db.add(acc)
            db.flush()
            account_lookup[(client.id, code)] = acc
    print(f"✅ GL accounts: {len(client_objs) * len(CHART_OF_ACCOUNTS)}")

    # 5. Invoices + line items
    invoice_objs: list[Invoice] = []
    for ci, num, status, amount, due_days, lines in INVOICES:
        client = client_objs[ci]
        currency = "GBP" if client.country == "UK" else ("NOK" if client.country == "NO" else "ZAR")
        inv = Invoice(
            client_id=client.id,
            invoice_number=num,
            status=status,
            amount=D(amount),
            currency=currency,
            due_date=utc(due_days),
            issued_at=utc(due_days - 30),
        )
        db.add(inv)
        db.flush()
        for desc, qty, unit_price in lines:
            db.add(InvoiceLineItem(
                invoice_id=inv.id,
                description=desc,
                quantity=D(qty),
                unit_price=D(unit_price),
                total=D(qty * unit_price),
            ))
        invoice_objs.append(inv)
    print(f"✅ Invoices: {len(invoice_objs)} (with {sum(len(l) for _, _, _, _, _, l in INVOICES)} line items)")

    # 6. Bank accounts (one per client) + transactions
    bank_account_lookup: dict[int, BankAccount] = {}
    for client in client_objs:
        ba = BankAccount(
            client_id=client.id,
            bank_name="FNB" if client.country == "ZA" else ("Barclays" if client.country == "UK" else "DNB"),
            account_number=f"62{client.id:08d}",
            account_type="checking",
            currency="GBP" if client.country == "UK" else ("NOK" if client.country == "NO" else "ZAR"),
            is_active=True,
        )
        db.add(ba)
        db.flush()
        bank_account_lookup[client.id] = ba

    tx_count = 0
    for ci, days_offset, desc, amount, status, ref in BANK_TRANSACTIONS:
        client = client_objs[ci]
        matched_invoice = None
        if ref and ref.startswith("INV-"):
            matched_invoice = next((i for i in invoice_objs if i.invoice_number == ref), None)
        db.add(BankTransaction(
            account_id=bank_account_lookup[client.id].id,
            date=utc(days_offset),
            description=desc,
            amount=D(amount),
            reference=ref,
            status=status,
            matched_invoice_id=matched_invoice.id if matched_invoice else None,
            match_confidence=D(0.95) if status == "matched" else None,
            match_reason="Amount and reference match invoice" if status == "matched" else None,
            category="invoice_payment" if amount > 0 else "expense",
        ))
        tx_count += 1
    print(f"✅ Bank accounts: {len(client_objs)}")
    print(f"✅ Bank transactions: {tx_count}")

    # 7. A few journal entries (Acme Corp) — basic revenue + expense postings
    acme = client_objs[0]
    bank_acc = account_lookup[(acme.id, "1000")]
    revenue_acc = account_lookup[(acme.id, "4000")]
    salaries_acc = account_lookup[(acme.id, "5000")]
    rent_acc = account_lookup[(acme.id, "5100")]

    je1 = JournalEntry(
        client_id=acme.id,
        entry_date=utc(-25),
        description="Receipt from Acme Corp invoice INV-2026-0001",
        reference="INV-2026-0001",
        posted_by=admin.id,
    )
    db.add(je1)
    db.flush()
    db.add(JournalLine(entry_id=je1.id, account_id=bank_acc.id,    debit=D(15000), credit=D(0)))
    db.add(JournalLine(entry_id=je1.id, account_id=revenue_acc.id, debit=D(0),     credit=D(15000)))

    je2 = JournalEntry(
        client_id=acme.id,
        entry_date=utc(-1),
        description="Monthly salaries payment",
        reference="PAY-2026-04",
        posted_by=admin.id,
    )
    db.add(je2)
    db.flush()
    db.add(JournalLine(entry_id=je2.id, account_id=salaries_acc.id, debit=D(200000), credit=D(0)))
    db.add(JournalLine(entry_id=je2.id, account_id=bank_acc.id,     debit=D(0),      credit=D(200000)))

    je3 = JournalEntry(
        client_id=acme.id,
        entry_date=utc(-1),
        description="Office rent April 2026",
        reference="RENT-2026-04",
        posted_by=admin.id,
    )
    db.add(je3)
    db.flush()
    db.add(JournalLine(entry_id=je3.id, account_id=rent_acc.id, debit=D(18000), credit=D(0)))
    db.add(JournalLine(entry_id=je3.id, account_id=bank_acc.id, debit=D(0),     credit=D(18000)))

    print(f"✅ Journal entries: 3 (Acme Corp)")

    # 8. Employees (Acme Corp only)
    employee_objs = []
    for i, e in enumerate(EMPLOYEES, start=1):
        emp = Employee(
            client_id=acme.id,
            employee_number=f"EMP{i:04d}",
            first_name=e["first_name"],
            last_name=e["last_name"],
            id_number=e["id_number"],
            tax_number=f"010{i:07d}",
            employment_type="permanent",
            department=e["department"],
            position=e["position"],
            join_date=utc(-365),
            is_active=True,
        )
        db.add(emp)
        db.flush()
        employee_objs.append((emp, e["salary"]))
    print(f"✅ Employees: {len(employee_objs)}")

    # 9. Payroll period + run + payslips for current month
    period = PayrollPeriod(
        client_id=acme.id,
        year=NOW.year,
        month=NOW.month,
        period_start=NOW.replace(day=1),
        period_end=NOW,
        status="processing",
    )
    db.add(period)
    db.flush()

    payroll_run = PayrollRun(
        client_id=acme.id,
        period_start=period.period_start,
        period_end=period.period_end,
        status="processing",
        total_gross=D(0),
        total_paye=D(0),
        total_uif=D(0),
    )
    db.add(payroll_run)
    db.flush()

    total_gross = 0.0
    total_paye = 0.0
    total_uif = 0.0
    for emp, salary in employee_objs:
        paye = calc_paye(salary)
        uif_e, uif_emp = calc_uif(salary)
        sdl = calc_sdl(salary)
        total_deductions = paye + uif_e
        net = salary - total_deductions
        db.add(Payslip(
            employee_id=emp.id,
            payroll_run_id=payroll_run.id,
            period_id=period.id,
            gross_salary=D(salary),
            total_earnings=D(salary),
            paye=D(paye),
            uif_employee=D(uif_e),
            uif_employer=D(uif_emp),
            sdl=D(sdl),
            pension=D(0),
            medical_aid=D(0),
            other_deductions=D(0),
            total_deductions=D(total_deductions),
            net_salary=D(net),
            eti_amount=D(0),
            status="approved",
        ))
        total_gross += salary
        total_paye += paye
        total_uif += uif_e

    payroll_run.total_gross = D(total_gross)
    payroll_run.total_paye = D(total_paye)
    payroll_run.total_uif = D(total_uif)

    print(f"✅ Payroll period: {NOW.year}-{NOW.month:02d}")
    print(f"✅ Payslips: {len(employee_objs)} (gross total: R{total_gross:,.2f})")

    db.commit()

    # ── Summary ──
    print("\n" + "─" * 48)
    print("🎉 Seed complete!\n")
    print("Login at the deployed web app with:")
    print("    Email:    demo@claud-erp.com")
    print("    Password: demo1234")
    print("\n⚠ Change this password before exposing the deployment publicly.")
    print("─" * 48 + "\n")


if __name__ == "__main__":
    force = "--force" in sys.argv or "--reset" in sys.argv

    db = SessionLocal()
    try:
        seed(db, force=force)
    except Exception as e:
        db.rollback()
        print(f"\n❌ Seed failed: {e}")
        raise
    finally:
        db.close()
