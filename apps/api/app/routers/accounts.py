from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import csv, io
from app.database import get_db
from app.models import Account
from app.auth import AuthUser, get_current_user

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])

class AccountBase(BaseModel):
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=255)
    account_type: str = Field(..., pattern=r"^(asset|liability|equity|revenue|expense)$")
    sub_type: Optional[str] = None
    parent_id: Optional[int] = None
    is_control_account: bool = False
    description: Optional[str] = None

class AccountCreate(AccountBase):
    client_id: int

class AccountUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    account_type: Optional[str] = None
    sub_type: Optional[str] = None
    is_control_account: Optional[bool] = None
    is_active: Optional[bool] = None

class AccountOut(AccountBase):
    id: int; client_id: int; is_active: bool
    class Config: from_attributes = True

@router.get("", response_model=list[AccountOut])
def list_accounts(client_id: int=Query(...), account_type: Optional[str]=None, is_active: bool=True, skip: int=0, limit: int=500, db: Session=Depends(get_db), current_user: AuthUser=Depends(get_current_user)):
    from app.models import Client
    client = db.query(Client).filter(Client.id==client_id, Client.agency_id==current_user.agency_id).first()
    if not client: raise HTTPException(status_code=403, detail="Client not found")
    q = db.query(Account).filter(Account.client_id==client_id)
    if account_type: q = q.filter(Account.account_type==account_type)
    if is_active is not None: q = q.filter(Account.is_active==is_active)
    return q.order_by(Account.code).offset(skip).limit(limit).all()

@router.post("", response_model=AccountOut, status_code=201)
def create_account(data: AccountCreate, db: Session=Depends(get_db), current_user: AuthUser=Depends(get_current_user)):
    from app.models import Client
    client = db.query(Client).filter(Client.id==data.client_id, Client.agency_id==current_user.agency_id).first()
    if not client: raise HTTPException(status_code=404, detail="Client not found")
    existing = db.query(Account).filter(Account.client_id==data.client_id, Account.code==data.code).first()
    if existing: raise HTTPException(status_code=400, detail="Account code already exists")
    account = Account(**data.model_dump())
    db.add(account); db.commit(); db.refresh(account)
    return account

@router.get("/{account_id}", response_model=AccountOut)
def get_account(account_id: int, db: Session=Depends(get_db)):
    account = db.query(Account).filter(Account.id==account_id).first()
    if not account: raise HTTPException(status_code=404, detail="Account not found")
    return account

@router.patch("/{account_id}", response_model=AccountOut)
def update_account(account_id: int, data: AccountUpdate, db: Session=Depends(get_db)):
    account = db.query(Account).filter(Account.id==account_id).first()
    if not account: raise HTTPException(status_code=404, detail="Account not found")
    for key, value in data.model_dump(exclude_unset=True).items(): setattr(account, key, value)
    db.commit(); db.refresh(account)
    return account

@router.post("/{client_id}/import-csv")
async def import_accounts_csv(client_id: int, file: UploadFile=File(...), db: Session=Depends(get_db), current_user: AuthUser=Depends(get_current_user)):
    if not file.filename.lower().endswith(".csv"): raise HTTPException(status_code=400, detail="File must be CSV")
    content = await file.read()
    try: reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    except UnicodeError: raise HTTPException(status_code=400, detail="Invalid encoding — use UTF-8")
    VALID_TYPES = {"asset","liability","equity","revenue","expense"}
    imported, errors = [], []
    for i, row in enumerate(reader, start=2):
        code = row.get("code","").strip(); name = row.get("name","").strip()
        account_type = row.get("account_type","").strip().lower()
        sub_type = row.get("sub_type","").strip() or None
        description = row.get("description","").strip() or None
        if not code or not name: errors.append(f"Row {i}: missing code or name"); continue
        if account_type not in VALID_TYPES: errors.append(f"Row {i}: invalid account_type '{account_type}'"); continue
        existing = db.query(Account).filter(Account.client_id==client_id, Account.code==code).first()
        if existing: errors.append(f"Row {i}: code {code} already exists — skipped"); continue
        db.add(Account(client_id=client_id, code=code, name=name, account_type=account_type, sub_type=sub_type, description=description))
        imported.append(code)
    db.commit()
    return {"imported": len(imported), "codes": imported, "errors": errors}
