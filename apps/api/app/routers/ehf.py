"""
EHF invoice import router.
- Generate sample EHF invoices for demo
- Upload and parse EHF XML
- Auto-book purchase invoices to GL per NS 4102
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from decimal import Decimal
from datetime import date, datetime
from typing import Optional
import zipfile
import io

from app.database import get_db
from app.models import Account, JournalEntry, JournalLine, Client
from app.auth import AuthUser, get_current_user
from app.services.ehf import (
    generate_sample_invoices,
    generate_ehf_xml,
    parse_ehf_xml,
    suggest_account_code,
    EHFInvoice,
)
from app.services.nordic import get_coa_template

router = APIRouter(prefix="/api/v1/ehf", tags=["ehf"])

INPUT_VAT_CODE = "2710"
ACCOUNTS_PAYABLE_CODE = "2400"


class ParsedLine(BaseModel):
    description: str
    quantity: str
    unit_price: str
    line_amount: str
    vat_rate: str
    vat_amount: str
    suggested_account: str


class ParsedInvoice(BaseModel):
    invoice_number: str
    issue_date: str
    due_date: str
    supplier_name: str
    supplier_org_number: str
    currency: str
    subtotal: str
    total_vat: str
    total: str
    lines: list[ParsedLine]
    note: str = ""


class BookingResult(BaseModel):
    invoice_number: str
    journal_entry_id: int
    lines_posted: int
    total_debit: str
    total_credit: str


class ImportResult(BaseModel):
    invoices_parsed: int
    invoices_booked: int
    journal_entries: list[BookingResult]
    errors: list[str]
    notices: list[str] = []


def _ehf_to_parsed(inv: EHFInvoice) -> ParsedInvoice:
    return ParsedInvoice(
        invoice_number=inv.invoice_number,
        issue_date=inv.issue_date.isoformat(),
        due_date=inv.due_date.isoformat(),
        supplier_name=inv.supplier_name,
        supplier_org_number=inv.supplier_org_number,
        currency=inv.currency,
        subtotal=str(inv.subtotal),
        total_vat=str(inv.total_vat),
        total=str(inv.total),
        note=inv.note,
        lines=[
            ParsedLine(
                description=l.description,
                quantity=str(l.quantity),
                unit_price=str(l.unit_price),
                line_amount=str(l.line_amount),
                vat_rate=str(l.vat_rate),
                vat_amount=str(l.vat_amount),
                suggested_account=l.account_code or suggest_account_code(l.description),
            )
            for l in inv.lines
        ],
    )


@router.get("/sample-invoices", response_model=list[ParsedInvoice])
def get_sample_invoices(
    buyer_name: str = Query("Test Hotell AS"),
    buyer_org: str = Query("974760673"),
):
    """Preview the 10 sample EHF invoices without downloading."""
    invoices = generate_sample_invoices(buyer_name, buyer_org)
    return [_ehf_to_parsed(inv) for inv in invoices]


@router.get("/sample-invoices/download")
def download_sample_invoices(
    buyer_name: str = Query("Test Hotell AS"),
    buyer_org: str = Query("974760673"),
):
    """Download 10 sample EHF XML invoices as a ZIP file."""
    invoices = generate_sample_invoices(buyer_name, buyer_org)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for inv in invoices:
            xml = generate_ehf_xml(inv)
            filename = f"{inv.invoice_number}.xml"
            zf.writestr(filename, xml)
    buf.seek(0)
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=ehf-sample-invoices.zip"},
    )


@router.post("/parse", response_model=list[ParsedInvoice])
async def parse_uploaded_ehf(
    files: list[UploadFile] = File(...),
):
    """Parse uploaded EHF XML files and return structured data (no booking yet)."""
    results = []
    for f in files:
        content = await f.read()
        try:
            xml_str = content.decode("utf-8")
            inv = parse_ehf_xml(xml_str)
            for line in inv.lines:
                if not line.account_code:
                    line.account_code = suggest_account_code(line.description)
            results.append(_ehf_to_parsed(inv))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse {f.filename}: {str(e)}")
    return results


def _ensure_coa_seeded(db: Session, client: Client) -> Optional[str]:
    """
    Auto-seed NS 4102 / BAS 2024 if the client has no chart of accounts.
    Returns a notice string if seeding happened, None otherwise.
    Refuses to seed if partial COA exists (avoids corrupting customised setups).
    """
    existing = db.query(Account).filter(Account.client_id == client.id).count()
    if existing > 0:
        return None

    country = (client.country or "NO").upper()
    if country not in ("NO", "SE"):
        country = "NO"

    template = get_coa_template(country)
    name_key = "name_no" if country == "NO" else "name_sv"
    parent_map: dict[str, int] = {}

    for acct in template:
        parent_id = parent_map.get(acct.parent_code) if acct.parent_code else None
        account = Account(
            client_id=client.id,
            code=acct.code,
            name=getattr(acct, name_key),
            account_type=acct.type,
            parent_id=parent_id,
            is_active=True,
        )
        db.add(account)
        db.flush()
        parent_map[acct.code] = account.id

    return (
        f"Chart of accounts auto-seeded for {client.name}: "
        f"{len(template)} accounts ({country} — "
        f"{'NS 4102' if country == 'NO' else 'BAS 2024'})."
    )


def _book_invoice(inv: EHFInvoice, client_id: int, user_id: int, db: Session) -> BookingResult:
    """Create journal entries for a purchase invoice per NS 4102."""
    accounts = {a.code: a for a in db.query(Account).filter(Account.client_id == client_id).all()}

    ap_account = accounts.get(ACCOUNTS_PAYABLE_CODE)
    if not ap_account:
        raise HTTPException(
            status_code=400,
            detail=f"Missing account {ACCOUNTS_PAYABLE_CODE} (Leverandørgjeld). Seed chart of accounts first.",
        )

    input_vat_account = accounts.get(INPUT_VAT_CODE)
    if not input_vat_account:
        raise HTTPException(
            status_code=400,
            detail=f"Missing account {INPUT_VAT_CODE} (Inngående MVA). Seed chart of accounts first.",
        )

    entry = JournalEntry(
        client_id=client_id,
        entry_date=datetime.combine(inv.issue_date, datetime.min.time()),
        description=f"Purchase invoice {inv.invoice_number} — {inv.supplier_name}",
        reference=inv.invoice_number,
        posted_by=user_id,
    )
    db.add(entry)
    db.flush()

    journal_lines = []
    total_debit = Decimal("0")
    total_credit = Decimal("0")

    for line in inv.lines:
        expense_code = line.account_code or suggest_account_code(line.description)
        expense_account = accounts.get(expense_code)
        if not expense_account:
            expense_account = accounts.get("4300")
        if not expense_account:
            for code in ["6000", "7000", "4000"]:
                if code in accounts:
                    expense_account = accounts[code]
                    break
        if not expense_account:
            raise HTTPException(
                status_code=400,
                detail=f"No suitable expense account found for '{line.description}'. Seed chart of accounts first.",
            )

        # DR: Expense account (net amount)
        expense_line = JournalLine(
            entry_id=entry.id,
            account_id=expense_account.id,
            debit=line.line_amount,
            credit=Decimal("0"),
            description=line.description,
        )
        db.add(expense_line)
        journal_lines.append(expense_line)
        total_debit += line.line_amount

        # DR: Input VAT (if vat > 0)
        if line.vat_amount > 0:
            vat_line = JournalLine(
                entry_id=entry.id,
                account_id=input_vat_account.id,
                debit=line.vat_amount,
                credit=Decimal("0"),
                description=f"Inng. MVA {line.vat_rate}% — {line.description}",
            )
            db.add(vat_line)
            journal_lines.append(vat_line)
            total_debit += line.vat_amount

    # CR: Accounts payable (total including VAT)
    ap_line = JournalLine(
        entry_id=entry.id,
        account_id=ap_account.id,
        debit=Decimal("0"),
        credit=inv.total,
        description=f"Leverandørgjeld — {inv.supplier_name} ({inv.invoice_number})",
    )
    db.add(ap_line)
    journal_lines.append(ap_line)
    total_credit += inv.total

    return BookingResult(
        invoice_number=inv.invoice_number,
        journal_entry_id=entry.id,
        lines_posted=len(journal_lines),
        total_debit=str(total_debit),
        total_credit=str(total_credit),
    )


@router.post("/import", response_model=ImportResult)
async def import_and_book_ehf(
    client_id: int = Query(...),
    files: list[UploadFile] = File(...),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload EHF XML files, parse them, and auto-book to the general ledger."""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.agency_id == current_user.agency_id,
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    notices: list[str] = []
    seed_notice = _ensure_coa_seeded(db, client)
    if seed_notice:
        notices.append(seed_notice)

    parsed_invoices: list[EHFInvoice] = []
    errors: list[str] = []

    for f in files:
        content = await f.read()
        try:
            xml_str = content.decode("utf-8")
            inv = parse_ehf_xml(xml_str)
            for line in inv.lines:
                if not line.account_code:
                    line.account_code = suggest_account_code(line.description)
            parsed_invoices.append(inv)
        except Exception as e:
            errors.append(f"Parse error in {f.filename}: {str(e)}")

    results: list[BookingResult] = []
    for inv in parsed_invoices:
        try:
            result = _book_invoice(inv, client_id, current_user.id, db)
            results.append(result)
        except HTTPException as e:
            errors.append(f"Booking error for {inv.invoice_number}: {e.detail}")
        except Exception as e:
            errors.append(f"Booking error for {inv.invoice_number}: {str(e)}")

    if results or notices:
        db.commit()

    return ImportResult(
        invoices_parsed=len(parsed_invoices),
        invoices_booked=len(results),
        journal_entries=results,
        errors=errors,
        notices=notices,
    )


@router.post("/import-samples", response_model=ImportResult)
def import_sample_invoices(
    client_id: int = Query(...),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate and immediately book the 10 sample EHF invoices for a client."""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.agency_id == current_user.agency_id,
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    notices: list[str] = []
    seed_notice = _ensure_coa_seeded(db, client)
    if seed_notice:
        notices.append(seed_notice)

    invoices = generate_sample_invoices(client.name, client.registration_number or "974760673")
    results: list[BookingResult] = []
    errors: list[str] = []

    for inv in invoices:
        try:
            result = _book_invoice(inv, client_id, current_user.id, db)
            results.append(result)
        except HTTPException as e:
            errors.append(f"Booking error for {inv.invoice_number}: {e.detail}")
        except Exception as e:
            errors.append(f"Booking error for {inv.invoice_number}: {str(e)}")

    if results or notices:
        db.commit()

    return ImportResult(
        invoices_parsed=len(invoices),
        invoices_booked=len(results),
        journal_entries=results,
        errors=errors,
        notices=notices,
    )
