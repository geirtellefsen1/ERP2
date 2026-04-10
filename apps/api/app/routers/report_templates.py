from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.auth.middleware import get_current_user, security
from app.models.report_template import ReportTemplate, GeneratedReport
from app.schemas.report_template import (
    ReportTemplateCreate,
    ReportTemplateUpdate,
    ReportTemplateResponse,
    ReportTemplateList,
    GenerateReportRequest,
    GeneratedReportResponse,
    GeneratedReportList,
)
from app.services.commentary_service import generate_commentary, build_report_html

router = APIRouter(prefix="/reporting", tags=["reporting"])


@router.post("/templates", response_model=ReportTemplateResponse)
async def create_template(
    payload: ReportTemplateCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Create a new report template."""
    ctx = await get_current_user(credentials)

    template = ReportTemplate(
        name=payload.name,
        report_type=payload.report_type,
        tone=payload.tone,
        length=payload.length,
        sections=payload.sections,
        client_id=payload.client_id,
        created_by=int(ctx.user_id) if ctx.user_id else None,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/templates", response_model=ReportTemplateList)
async def list_templates(
    client_id: Optional[int] = Query(None, description="Filter by client ID"),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List report templates, optionally filtered by client_id."""
    ctx = await get_current_user(credentials)

    query = db.query(ReportTemplate)
    if client_id is not None:
        query = query.filter(ReportTemplate.client_id == client_id)

    templates = query.order_by(ReportTemplate.created_at.desc()).all()
    return ReportTemplateList(items=templates, total=len(templates))


@router.get("/templates/{template_id}", response_model=ReportTemplateResponse)
async def get_template(
    template_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get a specific report template."""
    ctx = await get_current_user(credentials)

    template = db.query(ReportTemplate).filter(
        ReportTemplate.id == template_id
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.put("/templates/{template_id}", response_model=ReportTemplateResponse)
async def update_template(
    template_id: int,
    payload: ReportTemplateUpdate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Update an existing report template."""
    ctx = await get_current_user(credentials)

    template = db.query(ReportTemplate).filter(
        ReportTemplate.id == template_id
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    db.commit()
    db.refresh(template)
    return template


@router.post("/generate", response_model=GeneratedReportResponse)
async def generate_report(
    payload: GenerateReportRequest,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Generate a report with AI-powered narrative commentary."""
    ctx = await get_current_user(credentials)

    # Verify template exists
    template = db.query(ReportTemplate).filter(
        ReportTemplate.id == payload.template_id
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Build period string
    period = ""
    if payload.period_start and payload.period_end:
        period = f"{payload.period_start.isoformat()} to {payload.period_end.isoformat()}"
    else:
        period = "Current period"

    # Determine client name from financial data or use a default
    client_name = payload.financial_data.get("client_name", f"Client {payload.client_id}")

    # Generate AI commentary
    commentary = await generate_commentary(
        client_name=client_name,
        period=period,
        financial_data=payload.financial_data,
        tone=template.tone or "formal",
        length=template.length or "full",
    )

    # Build HTML report
    html_content = build_report_html(
        client_name=client_name,
        period=period,
        commentary=commentary,
        financial_data=payload.financial_data,
    )

    # Save generated report
    report = GeneratedReport(
        client_id=payload.client_id,
        template_id=payload.template_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        status="generated",
        html_content=html_content,
        narrative_commentary=commentary,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/reports", response_model=GeneratedReportList)
async def list_reports(
    client_id: Optional[int] = Query(None, description="Filter by client ID"),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List generated reports, optionally filtered by client_id."""
    ctx = await get_current_user(credentials)

    query = db.query(GeneratedReport)
    if client_id is not None:
        query = query.filter(GeneratedReport.client_id == client_id)

    reports = query.order_by(GeneratedReport.generated_at.desc()).all()
    return GeneratedReportList(items=reports, total=len(reports))


@router.get("/reports/{report_id}", response_model=GeneratedReportResponse)
async def get_report(
    report_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get a generated report with content."""
    ctx = await get_current_user(credentials)

    report = db.query(GeneratedReport).filter(
        GeneratedReport.id == report_id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/reports/{report_id}/html", response_class=HTMLResponse)
async def get_report_html(
    report_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get raw HTML content for a generated report."""
    ctx = await get_current_user(credentials)

    report = db.query(GeneratedReport).filter(
        GeneratedReport.id == report_id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if not report.html_content:
        raise HTTPException(status_code=404, detail="Report HTML not available")

    return HTMLResponse(content=report.html_content)
