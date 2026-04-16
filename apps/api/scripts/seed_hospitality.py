"""Hospitality demo seed — Fjordvik Hotel & Restaurant.

Builds a realistic 24-room hotel + restaurant + bar in Bergen, Norway:

  - 1 client, 1 property, 4 room categories, 3 outlets
  - 180 days of daily revenue imports with seasonality
  - Embedded "problems" the AI surfaces:
      * Bar pour-cost trending up (last 7 days)
      * Dairy supplier price drift (Tine)
      * One duplicate supplier invoice the AI caught
      * Untagged transactions waiting for client confirmation
      * One unusually large electricity bill (Hafslund spike)
  - 12 suppliers with realistic Norwegian names
  - 60 supplier transactions over the last 30 days
  - 8 AI activity feed items demonstrating the "AI did this" workflow

Usage:
    cd apps/api && python scripts/seed_hospitality.py
    cd apps/api && python scripts/seed_hospitality.py --force

Idempotent: checks for the Fjordvik client by name and exits early
unless --force is passed (which deletes the client + cascades).
"""
from __future__ import annotations

import argparse
import math
import os
import random
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

# Allow running as `python scripts/seed_hospitality.py` from /app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    Account,
    Agency,
    AiActivityFeed,
    Client,
    DailyRevenueImport,
    DailyRevenueLine,
    InboxItem,
    Outlet,
    Property,
    RoomCategory,
    Transaction,
)
from app.services.inbox.extraction import extract_from_filename


# Seeded RNG so repeated runs produce identical data
RNG = random.Random(20260416)

CLIENT_NAME = "Fjordvik Hotel & Restaurant"
PROPERTY_NAME = "Fjordvik Hotel & Restaurant"
TOTAL_ROOMS = 24
CURRENCY = "NOK"
COUNTRY = "NO"
HISTORY_DAYS = 180
RECENT_TXN_DAYS = 30


def _kr(amount_nok: float) -> int:
    """Convert NOK amount to minor units (øre). 1 NOK = 100 øre."""
    return int(round(amount_nok * 100))


# --- Agency + client + property ---------------------------------------------


def _get_or_create_demo_agency(db: Session) -> Agency:
    """Reuse the existing demo agency from scripts/seed.py if present,
    otherwise create a minimal one."""
    agency = db.query(Agency).filter(Agency.slug == "claud-erp-demo").first()
    if agency:
        return agency
    agency = Agency(
        name="ClaudERP Demo Agency",
        slug="claud-erp-demo",
        subscription_tier="growth",
    )
    db.add(agency)
    db.commit()
    db.refresh(agency)
    return agency


def _create_fjordvik_client(db: Session, agency: Agency) -> Client:
    client = Client(
        agency_id=agency.id,
        name=CLIENT_NAME,
        registration_number="NO 919 273 154 MVA",
        country=COUNTRY,
        industry="Hospitality",
        fiscal_year_end="2026-12-31",
        is_active=True,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def _create_property(db: Session, client: Client) -> Property:
    prop = Property(
        client_id=client.id,
        name=PROPERTY_NAME,
        country=COUNTRY,
        total_rooms=TOTAL_ROOMS,
        opening_date=datetime(2018, 5, 1, tzinfo=timezone.utc),
        timezone="Europe/Oslo",
    )
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop


def _create_room_categories(db: Session, prop: Property) -> None:
    for code, label, count, rate_nok in [
        ("STD", "Standard double", 12, 1400),
        ("DLX", "Deluxe with fjord view", 8, 1950),
        ("JSUITE", "Junior Suite", 3, 2800),
        ("SVIEW", "Sea View Suite", 1, 4200),
    ]:
        db.add(
            RoomCategory(
                property_id=prop.id,
                code=code,
                label=label,
                room_count=count,
                base_rate_minor=_kr(rate_nok),
                currency=CURRENCY,
            )
        )
    db.commit()


def _create_outlets(db: Session, prop: Property) -> None:
    for name, outlet_type in [
        ("Restaurant", "food"),
        ("Bar", "beverage_alcohol"),
        ("Soft drinks & coffee", "beverage_soft"),
        ("Mini-bar", "beverage_alcohol"),
    ]:
        db.add(Outlet(property_id=prop.id, name=name, outlet_type=outlet_type))
    db.commit()


# --- Daily revenue with seasonality + embedded problems ---------------------


def _seasonal_occupancy(target: date) -> float:
    """Return base occupancy fraction (0-1) for a date.

    Bergen tourism: peak in June-Aug (~0.85-0.95), shoulder May/Sep (~0.65-0.75),
    low Nov-Feb (~0.35-0.50), with a small Christmas-NY bump.
    Modeled as a sine wave centred on July 1 plus a Dec spike.
    """
    day_of_year = target.timetuple().tm_yday
    # Sine wave: peaks at day 182 (July 1), troughs at day 365/0
    seasonal = 0.62 + 0.28 * math.cos((day_of_year - 182) / 365 * 2 * math.pi - math.pi)
    # Christmas/New Year bump: days 355-365 and 1-5
    if day_of_year >= 355 or day_of_year <= 5:
        seasonal += 0.18
    # Weekend boost (Fri/Sat)
    if target.weekday() in (4, 5):
        seasonal += 0.08
    return max(0.10, min(0.98, seasonal))


def _create_daily_revenue(db: Session, prop: Property) -> None:
    """Generate HISTORY_DAYS of imports ending today."""
    today = date.today()
    for offset in range(HISTORY_DAYS, 0, -1):
        d = today - timedelta(days=offset - 1)

        base_occ = _seasonal_occupancy(d)
        # Add ±5% noise
        occ = max(0.05, min(1.0, base_occ + RNG.uniform(-0.05, 0.05)))
        rooms_sold = int(round(TOTAL_ROOMS * occ))

        # ADR varies with demand: NOK 1,400 base, up to 2,200 in peak
        adr_nok = 1400 + 800 * max(0, occ - 0.5) * 2
        adr_nok += RNG.uniform(-50, 50)
        rooms_revenue_nok = rooms_sold * adr_nok

        # F&B: ~80 NOK food per occupied room + walk-ins
        food_covers = int(rooms_sold * 1.4 + RNG.randint(8, 25))
        food_per_cover_nok = 280 + RNG.uniform(-30, 30)
        food_revenue_nok = food_covers * food_per_cover_nok

        # Bar revenue: typically 35-40% of food
        bar_ratio = 0.37 + RNG.uniform(-0.04, 0.04)

        # ── EMBEDDED PROBLEM #1: rising pour cost in last 7 days ──
        # Bar revenue jumps to 50%+ of food (suggesting under-pricing,
        # heavy promo, or unrecorded waste). Anomaly detector should flag.
        if offset <= 7:
            bar_ratio += 0.15

        bar_revenue_nok = food_revenue_nok * bar_ratio

        # Soft drinks: small line, 8% of food
        soft_revenue_nok = food_revenue_nok * 0.08

        imp = DailyRevenueImport(
            property_id=prop.id,
            import_date=datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc),
            rooms_sold=rooms_sold,
            rooms_available=TOTAL_ROOMS,
            currency=CURRENCY,
            pms_name="MockPMS",
            raw_reference=f"FJORDVIK-{d.isoformat()}",
        )
        db.add(imp)
        db.flush()

        for outlet_type, gross_nok, covers in [
            ("rooms", rooms_revenue_nok, 0),
            ("food", food_revenue_nok, food_covers),
            ("beverage_alcohol", bar_revenue_nok, 0),
            ("beverage_soft", soft_revenue_nok, 0),
        ]:
            db.add(
                DailyRevenueLine(
                    import_id=imp.id,
                    outlet_type=outlet_type,
                    gross_amount_minor=_kr(gross_nok),
                    cover_count=covers,
                )
            )
    db.commit()


# --- Chart of accounts (minimal — enough for the demo) ---------------------


HOSPITALITY_COA = [
    # Revenue
    ("3000", "Room revenue", "revenue", "operating"),
    ("3010", "Food revenue", "revenue", "operating"),
    ("3020", "Beverage revenue (alcohol)", "revenue", "operating"),
    ("3030", "Beverage revenue (soft)", "revenue", "operating"),
    # COGS
    ("4000", "Food cost", "expense", "cogs"),
    ("4010", "Beverage cost (alcohol)", "expense", "cogs"),
    ("4020", "Beverage cost (soft)", "expense", "cogs"),
    ("4100", "Linen & laundry", "expense", "operating"),
    # Operating
    ("5000", "Wages — Rooms", "expense", "payroll"),
    ("5010", "Wages — F&B", "expense", "payroll"),
    ("5100", "Electricity", "expense", "operating"),
    ("5110", "Water & waste", "expense", "operating"),
    ("5200", "Cleaning supplies", "expense", "operating"),
    ("5300", "OTA commissions", "expense", "operating"),
    ("5400", "Marketing", "expense", "operating"),
    # Bank / VAT
    ("1000", "Cash at bank — DNB", "asset", "current"),
    ("2400", "Output VAT 12%", "liability", "current"),
    ("2410", "Output VAT 25%", "liability", "current"),
]


def _create_chart_of_accounts(db: Session, client: Client) -> dict[str, Account]:
    """Create the COA. Returns code -> Account map for use by transactions."""
    accounts: dict[str, Account] = {}
    for code, name, atype, sub in HOSPITALITY_COA:
        a = Account(
            client_id=client.id,
            code=code,
            name=name,
            account_type=atype,
            sub_type=sub,
            is_active=True,
        )
        db.add(a)
        db.flush()
        accounts[code] = a
    db.commit()
    return accounts


# --- Suppliers + transactions with embedded problems ------------------------


SUPPLIERS = [
    # (name, account_code, base_amount_nok, frequency_days, vendor_id)
    ("Tine SA", "4000", 3800, 4, "tine"),                    # dairy — RISING PRICES
    ("Bama Gruppen", "4000", 2400, 5, "bama"),               # produce
    ("Vinmonopolet", "4010", 6500, 7, "vinmono"),            # spirits
    ("Hansa Borg Bryggerier", "4010", 4200, 5, "hansa"),     # beer
    ("Ringnes", "4020", 1200, 7, "ringnes"),                 # soft drinks
    ("Berg Linservice AS", "4100", 1850, 7, "berg-lin"),     # laundry
    ("Hafslund Eco", "5100", 8400, 30, "hafslund"),          # electricity
    ("Bergen Vann KF", "5110", 1100, 30, "bvann"),           # water
    ("Lilleborg", "5200", 1450, 14, "lilleborg"),            # cleaning
    ("Booking.com", "5300", 12500, 30, "bdc"),               # OTA
    ("Expedia Group", "5300", 4800, 30, "expedia"),          # OTA
    ("Meta (Facebook ads)", "5400", 3200, 30, "meta"),       # marketing
]


def _create_recent_transactions(
    db: Session, client: Client, accounts: dict[str, Account]
) -> list[Transaction]:
    """Generate ~60 supplier invoices over the last RECENT_TXN_DAYS days.

    Embeds 3 problems:
      - Tine prices drift up 8% in last 14 days (food cost creep)
      - One duplicate invoice from Bama (4 days ago) — same amount, day apart
      - One unusually large Hafslund electricity bill (3x normal)
    """
    today = date.today()
    txns: list[Transaction] = []

    for name, account_code, base_nok, freq_days, vendor_id in SUPPLIERS:
        for offset in range(0, RECENT_TXN_DAYS, freq_days):
            d = today - timedelta(days=offset)
            amount = base_nok + RNG.uniform(-base_nok * 0.05, base_nok * 0.05)

            # Embedded problem: Tine rising 8% in last 14 days
            if vendor_id == "tine" and offset <= 14:
                amount *= 1.08

            # Embedded problem: Hafslund 3x spike on the most recent bill
            if vendor_id == "hafslund" and offset == 0:
                amount *= 3.1

            txn = Transaction(
                client_id=client.id,
                date=datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc),
                description=f"{name} — invoice",
                amount=Decimal(str(round(amount, 2))),
                reference=f"{vendor_id.upper()}-{d.strftime('%Y%m%d')}",
                matched=False,
            )
            db.add(txn)
            txns.append(txn)

    # Embedded problem: duplicate Bama invoice (same amount, 1 day apart)
    dup_date = today - timedelta(days=4)
    dup_amount = Decimal("2415.50")
    for n in (0, 1):
        db.add(
            Transaction(
                client_id=client.id,
                date=datetime.combine(
                    dup_date - timedelta(days=n),
                    datetime.min.time(),
                    tzinfo=timezone.utc,
                ),
                description="Bama Gruppen — invoice 2026-04-12",
                amount=dup_amount,
                reference=f"BAMA-DUPE-{n}",
                matched=False,
            )
        )

    db.commit()
    return txns


# --- AI activity feed: the "AI did this since you last logged in" panel ----


def _create_ai_activity(db: Session, agency: Agency, client: Client) -> None:
    """Create 8 AI activity items demonstrating the workflow.

    Mix of completed work (info/no review needed) and pending review items
    so the demo shows both the "AI did N things" celebration and the
    "you have N to approve" call to action.
    """
    now = datetime.now(timezone.utc)

    items = [
        # Anomalies — surfaced from the seed data above
        dict(
            category="anomaly",
            severity="warning",
            title="Bar pour cost rose to 52% of food revenue (was 37%)",
            detail=(
                "Last 7 days: bar revenue is 52% of food revenue, up from a 30-day "
                "baseline of 37%. Possible causes: unrecorded happy hour discounts, "
                "missing comp tickets, or pour-cost leak. Suggest spot-check the bar "
                "stock count and review Friday/Saturday voids."
            ),
            requires_review=True,
            source_kind="anomaly_detector",
            hours_ago=2,
        ),
        dict(
            category="anomaly",
            severity="warning",
            title="Dairy supplier Tine increased prices 8% over last 14 days",
            detail=(
                "Tine SA invoices in the last 14 days are 8% higher per delivery "
                "than the prior 14-day average. Other dairy suppliers (Q-Meieriene, "
                "Synnøve Finden) currently offer comparable products at 5-9% lower "
                "unit cost. Suggest requesting a quote."
            ),
            requires_review=True,
            source_kind="supplier_price_drift",
            hours_ago=6,
        ),
        dict(
            category="duplicate_detection",
            severity="critical",
            title="Possible duplicate invoice from Bama Gruppen — NOK 2,415.50",
            detail=(
                "Two invoices from Bama Gruppen for NOK 2,415.50 dated 12 April and "
                "13 April. Description is identical. Held back from payment run "
                "pending your review."
            ),
            requires_review=True,
            source_kind="transaction",
            hours_ago=18,
        ),
        dict(
            category="anomaly",
            severity="critical",
            title="Hafslund electricity bill 3.1× higher than usual",
            detail=(
                "This month's Hafslund Eco invoice (NOK 26,100) is 3.1× the trailing "
                "6-month average of NOK 8,400. Possible meter misread, tariff change, "
                "or equipment fault. Suggest checking meter reading vs invoiced kWh."
            ),
            requires_review=True,
            source_kind="transaction",
            hours_ago=22,
        ),
        # Completed AI work — no review needed
        dict(
            category="auto_coded",
            severity="info",
            title="Auto-coded 47 supplier invoices to the chart of accounts",
            detail=(
                "AI matched 47 of 62 incoming invoices to existing supplier patterns "
                "and posted them to the correct GL accounts. 15 needed manual review "
                "and are in the approvals queue."
            ),
            requires_review=False,
            source_kind="auto_coding",
            hours_ago=4,
        ),
        dict(
            category="bank_reconciliation",
            severity="info",
            title="Matched 23 bank transactions to invoices",
            detail=(
                "DNB feed for the last 7 days: 23 transactions auto-matched to open "
                "invoices (high confidence). 4 transactions remain unmatched and "
                "need your review."
            ),
            requires_review=False,
            source_kind="bank_match",
            hours_ago=8,
        ),
        dict(
            category="vat_draft",
            severity="info",
            title="Drafted Q1 2026 VAT return — ready for your review",
            detail=(
                "Output VAT 12% (rooms): NOK 142,560. Output VAT 25% (F&B): NOK "
                "98,420. Input VAT recoverable: NOK 38,910. Net payable: NOK "
                "202,070. Due date: 10 May 2026."
            ),
            requires_review=True,
            source_kind="vat_return",
            hours_ago=14,
        ),
        dict(
            category="forecast",
            severity="info",
            title="Updated 13-week cashflow forecast",
            detail=(
                "Projected cash position 13 weeks out: NOK 1.42M (vs NOK 1.18M "
                "current). Largest expected outflows: payroll (3 cycles), Q1 VAT, "
                "Bookling.com commission true-up. No liquidity gap detected."
            ),
            requires_review=False,
            source_kind="cashflow",
            hours_ago=12,
        ),
    ]

    for item in items:
        db.add(
            AiActivityFeed(
                agency_id=agency.id,
                client_id=client.id,
                category=item["category"],
                severity=item["severity"],
                title=item["title"],
                detail=item["detail"],
                source_kind=item["source_kind"],
                requires_review=item["requires_review"],
                created_at=now - timedelta(hours=item["hours_ago"]),
            )
        )
    db.commit()


# --- Inbox items: the AI-first receipt drop zone -----------------------------


def _create_inbox_items(
    db: Session, agency: Agency, client: Client, accounts: dict[str, Account]
) -> None:
    """Create 12 inbox items showing the full AI-first workflow.

    Mix of:
      - 5 pending review (high-confidence AI extraction, awaiting approval)
      - 4 already-approved (tied to a Transaction, what "good" looks like)
      - 2 low-confidence (AI failed, manual coding required)
      - 1 rejected (duplicate that the accountant rejected)
    """
    now = datetime.now(timezone.utc)

    # (filename, hours_ago, status_override, source)
    pending_extracted = [
        # Recent uploads with high-confidence extraction
        ("tine_2026-04-15_4120nok_inv-2401.pdf", 2, None, "email"),
        ("vinmonopolet_2026-04-15_7200nok_inv-3815.pdf", 4, None, "email"),
        ("hansa_2026-04-14_4500nok.pdf", 22, None, "ehf"),
        ("booking_2026-04-12_12500nok.pdf", 48, None, "email"),
        ("hafslund_2026-04-15_26100nok.pdf", 6, None, "email"),  # the spike
    ]

    approved = [
        ("bama_2026-04-10_2380nok_inv-4421.pdf", 120, "approved", "email"),
        ("berglin_2026-04-09_1850nok.pdf", 168, "approved", "email"),
        ("ringnes_2026-04-08_1180nok.pdf", 192, "approved", "email"),
        ("lilleborg_2026-04-07_1450nok.pdf", 216, "approved", "mobile"),
    ]

    pending_low_confidence = [
        ("scan_2026-04-14_001.jpg", 26, None, "mobile"),
        ("IMG_4582.jpeg", 30, None, "mobile"),
    ]

    rejected = [
        # The duplicate Bama invoice from the embedded problems
        ("bama_2026-04-13_2415nok_DUPLICATE.pdf", 18, "rejected", "email"),
    ]

    all_items = pending_extracted + approved + pending_low_confidence + rejected

    for filename, hours_ago, status_override, source in all_items:
        result = extract_from_filename(filename)

        suggested_account_id = None
        if result.suggested_account_code and result.suggested_account_code in accounts:
            suggested_account_id = accounts[result.suggested_account_code].id

        extracted_date_dt = None
        if result.date:
            extracted_date_dt = datetime.combine(
                result.date, datetime.min.time(), tzinfo=timezone.utc
            )

        item = InboxItem(
            agency_id=agency.id,
            client_id=client.id,
            source=source,
            original_filename=filename,
            status=status_override or ("extracted" if result.vendor else "pending"),
            extracted_vendor=result.vendor,
            extracted_date=extracted_date_dt,
            extracted_amount_minor=result.amount_minor,
            extracted_vat_minor=result.vat_minor,
            extracted_currency=result.currency,
            extracted_invoice_number=result.invoice_number,
            suggested_account_id=suggested_account_id,
            suggested_outlet_type=result.suggested_outlet_type,
            ai_confidence=result.confidence,
            ai_reasoning=result.reasoning,
            created_at=now - timedelta(hours=hours_ago),
        )

        if status_override == "approved":
            item.approved_at = now - timedelta(hours=hours_ago - 1)
        elif status_override == "rejected":
            item.rejected_at = now - timedelta(hours=hours_ago - 1)
            item.rejection_reason = (
                "Possible duplicate of invoice INV-4421 from 12 April. "
                "Cross-checked against Bama invoice register."
            )

        db.add(item)

    db.commit()


# --- Main --------------------------------------------------------------------


def _existing_fjordvik(db: Session) -> Client | None:
    return db.query(Client).filter(Client.name == CLIENT_NAME).first()


def _wipe_fjordvik(db: Session, client: Client) -> None:
    """Cascade delete via the client. Property -> RoomCategory/Outlet/imports
    will cascade through ondelete=CASCADE FKs. AI activity scoped to this
    client is removed explicitly."""
    db.query(InboxItem).filter(InboxItem.client_id == client.id).delete()
    db.query(AiActivityFeed).filter(AiActivityFeed.client_id == client.id).delete()
    db.query(Transaction).filter(Transaction.client_id == client.id).delete()
    db.query(Account).filter(Account.client_id == client.id).delete()
    db.delete(client)
    db.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed Fjordvik Hotel demo data")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Wipe existing Fjordvik client and re-seed",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        existing = _existing_fjordvik(db)
        if existing and not args.force:
            print(
                f"✓ Fjordvik client already exists (id={existing.id}). "
                "Use --force to wipe and re-seed."
            )
            return 0
        if existing and args.force:
            print(f"⚠ Wiping existing Fjordvik client (id={existing.id})...")
            _wipe_fjordvik(db, existing)

        agency = _get_or_create_demo_agency(db)
        print(f"✓ Demo agency: id={agency.id} ({agency.slug})")

        client = _create_fjordvik_client(db, agency)
        print(f"✓ Client: {client.name} (id={client.id})")

        prop = _create_property(db, client)
        print(f"✓ Property: {prop.name} (id={prop.id}, {prop.total_rooms} rooms)")

        _create_room_categories(db, prop)
        _create_outlets(db, prop)
        print("✓ Room categories + outlets")

        _create_daily_revenue(db, prop)
        print(f"✓ {HISTORY_DAYS} days of daily revenue (with seasonality + pour-cost spike)")

        accounts = _create_chart_of_accounts(db, client)
        print(f"✓ Chart of accounts ({len(accounts)} accounts)")

        txns = _create_recent_transactions(db, client, accounts)
        print(f"✓ {len(txns)} supplier transactions (with embedded duplicate + spike)")

        _create_ai_activity(db, agency, client)
        print("✓ 8 AI activity feed items (4 require review)")

        _create_inbox_items(db, agency, client, accounts)
        print("✓ 12 inbox items (5 awaiting review, 4 approved, 2 low-confidence, 1 rejected)")

        print()
        print("🎉 Hospitality demo seed complete!")
        print(f"   Client:  {CLIENT_NAME}")
        print(f"   Property ID: {prop.id}")
        print(f"   Dashboard URL (after login):")
        print(f"     /dashboard/hospitality/{prop.id}")
        return 0
    except Exception as e:
        db.rollback()
        print(f"✗ Seed failed: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
