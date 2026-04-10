from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PostingPeriodCreate(BaseModel):
    client_id: int
    period_name: str
    period_start: datetime
    period_end: datetime


class PostingPeriodResponse(BaseModel):
    id: int
    client_id: int
    agency_id: int
    period_name: str
    period_start: datetime
    period_end: datetime
    status: str
    is_locked: bool
    created_at: datetime

    model_config = {"from_attributes": True}
