from app.models.base import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func


class ReportTemplate(BaseModel):
    __tablename__ = "report_templates"

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    name = Column(String(255), nullable=False)
    report_type = Column(String(20))  # annual/monthly/quarterly
    tone = Column(String(50), default="formal")  # formal/conversational/technical
    length = Column(String(30), default="full")  # executive_summary/full/extended
    sections = Column(JSON, nullable=True)  # [{section: 'profitability', enabled: true}, ...]
    delivery_config = Column(JSON, nullable=True)  # {frequency: 'monthly', recipients: [...]}
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)


class GeneratedReport(BaseModel):
    __tablename__ = "generated_reports"

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("report_templates.id"), nullable=False)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    status = Column(String(20), default="draft")  # draft/generated/delivered
    html_content = Column(Text, nullable=True)
    narrative_commentary = Column(Text, nullable=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    delivery_email = Column(String(255), nullable=True)
