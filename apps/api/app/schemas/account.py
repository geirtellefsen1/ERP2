from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AccountBase(BaseModel):
    account_number: str
    name: str
    account_type: str
    description: Optional[str] = None
    parent_account_id: Optional[int] = None


class AccountCreate(AccountBase):
    client_id: int


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[str] = None


class AccountResponse(AccountBase):
    id: int
    client_id: int
    agency_id: int
    is_active: str
    balance: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AccountHierarchyNode(AccountResponse):
    children: list["AccountHierarchyNode"] = []
