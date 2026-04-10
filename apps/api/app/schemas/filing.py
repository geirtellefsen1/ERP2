from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class FilingRecordCreate(BaseModel):
    client_id: int
    jurisdiction: str
    filing_type: str
    period_start: Optional[date] = None
    period_end: Optional[date] = None


class FilingRecordResponse(BaseModel):
    id: int
    client_id: int
    jurisdiction: str
    filing_type: str
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    status: str
    submission_id: Optional[str] = None
    submitted_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FilingRecordList(BaseModel):
    items: list[FilingRecordResponse]
    total: int
    page: int
    per_page: int


class FilingDeadlineCreate(BaseModel):
    client_id: int
    jurisdiction: str
    filing_type: str
    due_date: date
    frequency: Optional[str] = None


class FilingDeadlineResponse(BaseModel):
    id: int
    client_id: int
    jurisdiction: str
    filing_type: str
    due_date: date
    frequency: Optional[str] = None
    reminder_days_before: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FilingDeadlineList(BaseModel):
    items: list[FilingDeadlineResponse]
    total: int


class VATFilingPrepareRequest(BaseModel):
    client_id: int
    jurisdiction: str
    period_start: date
    period_end: date


class VATFilingResponse(BaseModel):
    jurisdiction: str
    filing_data: dict
    xml_content: Optional[str] = None
