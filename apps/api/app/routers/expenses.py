from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.models import Expense as ExpenseModel, Client as ClientModel
from app.schemas import ExpenseCreate, ExpenseUpdate, Expense as ExpenseSchema
from app.auth import get_current_user, AuthUser

router = APIRouter(prefix="/api/v1/expenses", tags=["expenses"])


def _verify_client_access(db: Session, client_id: int, agency_id: int) -> ClientModel:
    client = db.query(ClientModel).filter(
        ClientModel.id == client_id,
        ClientModel.agency_id == agency_id,
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.get("", response_model=list[ExpenseSchema])
def list_expenses(
    client_id: int | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    category: str | None = Query(None),
    skip: int = 0,
    limit: int = 100,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        db.query(ExpenseModel)
        .join(ClientModel)
        .filter(ClientModel.agency_id == current_user.agency_id)
    )
    if client_id:
        q = q.filter(ExpenseModel.client_id == client_id)
    if status_filter:
        q = q.filter(ExpenseModel.status == status_filter)
    if category:
        q = q.filter(ExpenseModel.category == category)
    return q.order_by(ExpenseModel.id.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=ExpenseSchema, status_code=status.HTTP_201_CREATED)
def create_expense(
    data: ExpenseCreate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = _verify_client_access(db, data.client_id, current_user.agency_id)
    currency = data.currency or client.default_currency or "NOK"

    expense = ExpenseModel(
        client_id=data.client_id,
        vendor_name=data.vendor_name,
        vendor_org_number=data.vendor_org_number,
        description=data.description,
        date=data.date,
        due_date=data.due_date,
        amount=data.amount,
        vat_amount=data.vat_amount,
        vat_rate=data.vat_rate,
        currency=currency,
        category=data.category,
        status="pending",
        account_id=data.account_id,
        inbox_item_id=data.inbox_item_id,
        payment_method=data.payment_method,
        notes=data.notes,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("/{expense_id}", response_model=ExpenseSchema)
def get_expense(
    expense_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exp = (
        db.query(ExpenseModel)
        .join(ClientModel)
        .filter(ExpenseModel.id == expense_id, ClientModel.agency_id == current_user.agency_id)
        .first()
    )
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    return exp


@router.patch("/{expense_id}", response_model=ExpenseSchema)
def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exp = (
        db.query(ExpenseModel)
        .join(ClientModel)
        .filter(ExpenseModel.id == expense_id, ClientModel.agency_id == current_user.agency_id)
        .first()
    )
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(exp, key, value)
    db.commit()
    db.refresh(exp)
    return exp


@router.post("/{expense_id}/approve", response_model=ExpenseSchema)
def approve_expense(
    expense_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exp = (
        db.query(ExpenseModel)
        .join(ClientModel)
        .filter(ExpenseModel.id == expense_id, ClientModel.agency_id == current_user.agency_id)
        .first()
    )
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    exp.status = "approved"
    exp.approved_at = datetime.now(timezone.utc)
    exp.approved_by_user_id = current_user.id
    db.commit()
    db.refresh(exp)
    return exp
