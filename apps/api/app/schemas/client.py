from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ClientBase(BaseModel):
    name: str
    registration_number: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    fiscal_year_end: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    registration_number: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    is_active: Optional[bool] = None


class ClientResponse(ClientBase):
    id: int
    agency_id: int
    is_active: bool
    health_score: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ClientListResponse(BaseModel):
    items: list[ClientResponse]
    total: int
    page: int
    per_page: int
