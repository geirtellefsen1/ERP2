from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class ReportTemplateCreate(BaseModel):
    name: str
    report_type: Optional[str] = "monthly"
    tone: Optional[str] = "formal"
    length: Optional[str] = "full"
    sections: Optional[list] = None
    client_id: Optional[int] = None


class ReportTemplateUpdate(BaseModel):
    name: Optional[str] = None
    report_type: Optional[str] = None
    tone: Optional[str] = None
    length: Optional[str] = None
    sections: Optional[list] = None
    delivery_config: Optional[dict] = None
    client_id: Optional[int] = None


class ReportTemplateResponse(BaseModel):
    id: int
    name: str
    report_type: Optional[str] = None
    tone: Optional[str] = None
    length: Optional[str] = None
    sections: Optional[list] = None
    delivery_config: Optional[dict] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReportTemplateList(BaseModel):
    items: list[ReportTemplateResponse]
    total: int


class GenerateReportRequest(BaseModel):
    template_id: int
    client_id: int
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    financial_data: dict = {}


class GeneratedReportResponse(BaseModel):
    id: int
    client_id: int
    template_id: int
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    status: Optional[str] = None
    narrative_commentary: Optional[str] = None
    generated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class GeneratedReportList(BaseModel):
    items: list[GeneratedReportResponse]
    total: int
