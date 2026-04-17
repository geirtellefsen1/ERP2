from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func as sqla_func
from decimal import Decimal
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models import Invoice as InvoiceModel, InvoiceLineItem as LineItemModel, Client as ClientModel
from app.schemas import InvoiceCreate, InvoiceUpdate, Invoice as InvoiceSchema
from app.auth import get_current_user, AuthUser

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])


def _next_invoice_number(db: Session, client_id: int) -> str:
    last = (
        db.query(InvoiceModel.invoice_number)
        .filter(InvoiceModel.client_id == client_id)
        .order_by(InvoiceModel.id.desc())
        .first()
    )
    if last and last[0]:
        parts = last[0].rsplit("-", 1)
        if len(parts) == 2 and parts[1].isdigit():
            return f"{parts[0]}-{int(parts[1]) + 1:04d}"
    return f"INV-0001"


def _verify_client_access(db: Session, client_id: int, agency_id: int) -> ClientModel:
    client = db.query(ClientModel).filter(
        ClientModel.id == client_id,
        ClientModel.agency_id == agency_id,
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.get("", response_model=list[InvoiceSchema])
def list_invoices(
    client_id: int | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    skip: int = 0,
    limit: int = 100,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        db.query(InvoiceModel)
        .join(ClientModel)
        .filter(ClientModel.agency_id == current_user.agency_id)
    )
    if client_id:
        q = q.filter(InvoiceModel.client_id == client_id)
    if status_filter:
        q = q.filter(InvoiceModel.status == status_filter)
    return q.order_by(InvoiceModel.id.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=InvoiceSchema, status_code=status.HTTP_201_CREATED)
def create_invoice(
    data: InvoiceCreate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = _verify_client_access(db, data.client_id, current_user.agency_id)

    subtotal = Decimal(0)
    vat_total = Decimal(0)
    line_models = []
    for li in data.line_items:
        line_total = li.quantity * li.unit_price
        line_vat = (line_total * li.vat_rate / 100).quantize(Decimal("0.01"))
        subtotal += line_total
        vat_total += line_vat
        line_models.append(LineItemModel(
            description=li.description,
            quantity=li.quantity,
            unit_price=li.unit_price,
            vat_rate=li.vat_rate,
            vat_amount=line_vat,
            total=line_total + line_vat,
        ))

    invoice_number = _next_invoice_number(db, data.client_id)
    due_date = datetime.now(timezone.utc) + timedelta(days=data.payment_terms_days)
    currency = data.currency or client.default_currency or "NOK"

    invoice = InvoiceModel(
        client_id=data.client_id,
        invoice_number=invoice_number,
        status="draft",
        currency=currency,
        subtotal=subtotal,
        vat_amount=vat_total,
        amount=subtotal + vat_total,
        customer_name=data.customer_name,
        customer_email=data.customer_email,
        customer_address=data.customer_address,
        customer_org_number=data.customer_org_number,
        reference=data.reference,
        payment_terms_days=data.payment_terms_days,
        notes=data.notes,
        due_date=due_date,
    )
    invoice.line_items = line_models
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("/{invoice_id}", response_model=InvoiceSchema)
def get_invoice(
    invoice_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inv = (
        db.query(InvoiceModel)
        .join(ClientModel)
        .filter(InvoiceModel.id == invoice_id, ClientModel.agency_id == current_user.agency_id)
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return inv


@router.patch("/{invoice_id}", response_model=InvoiceSchema)
def update_invoice(
    invoice_id: int,
    data: InvoiceUpdate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inv = (
        db.query(InvoiceModel)
        .join(ClientModel)
        .filter(InvoiceModel.id == invoice_id, ClientModel.agency_id == current_user.agency_id)
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(inv, key, value)
    db.commit()
    db.refresh(inv)
    return inv


@router.post("/{invoice_id}/send", response_model=InvoiceSchema)
def send_invoice(
    invoice_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inv = (
        db.query(InvoiceModel)
        .join(ClientModel)
        .filter(InvoiceModel.id == invoice_id, ClientModel.agency_id == current_user.agency_id)
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if inv.status not in ("draft",):
        raise HTTPException(status_code=400, detail=f"Cannot send invoice in '{inv.status}' status")
    inv.status = "sent"
    inv.issued_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(inv)
    return inv
