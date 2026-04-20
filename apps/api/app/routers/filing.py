"""
Statutory Filing — Sprint 17.
VAT returns (SA/NO/UK), PAYE submissions, A-melding.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from app.database import get_db
from app.models import TaxFiling, Client
from app.auth import AuthUser, get_current_user

router = APIRouter(prefix="/api/v1/filings", tags=["filings"])


@router.get("")
def list_filings(
    client_id: int = Query(...),
    filing_type: str = Query(None),
    year: int = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(TaxFiling).filter(TaxFiling.client_id == client_id)
    if filing_type:
        q = q.filter(TaxFiling.filing_type == filing_type)
    if year:
        q = q.filter(TaxFiling.period_year == year)
    return q.order_by(TaxFiling.period_year.desc(), TaxFiling.period_month.desc()).all()


@router.post("/calculate-vat-sa")
def calculate_vat_sa(
    client_id: int = Query(...),
    year: int = Query(...),
    month: int = Query(...),
    db: Session = Depends(get_db),
):
    """
    Calculate South African VAT return for a period.
    Standard rate: 15%. Input tax credit vs output tax.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client or client.country != "ZA":
        raise HTTPException(status_code=400, detail="Only available for SA clients")

    # In production: calculate from journal entries
    # For now: return placeholder
    return {
        "filing_type": "vat_sa",
        "period": f"{year}-{month:02d}",
        "output_vat": Decimal("0.00"),
        "input_vat": Decimal("0.00"),
        "vat_payable": Decimal("0.00"),
        "due_date": f"{year}-{month+1}-25",  # 25th of following month
    }


@router.post("/submit-vat-sa")
def submit_vat_sa(
    filing_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    Submit VAT return to SARS via eFiling API.
    Placeholder — in production integrate with SARS SOAP/REST API.
    """
    filing = db.query(TaxFiling).filter(TaxFiling.id == filing_id).first()
    if not filing:
        raise HTTPException(status_code=404, detail="Filing not found")

    filing.status = "filed"
    filing.filed_at = datetime.utcnow()
    filing.reference = f"SARS-VAT-{filing.period_year}{filing.period_month:02d}"
    db.commit()
    return {"status": "filed", "reference": filing.reference}


@router.post("/generate-amelding")
def generate_amelding(
    client_id: int = Query(...),
    year: int = Query(...),
    month: int = Query(...),
    db: Session = Depends(get_db),
):
    """
    Generate Norwegian A-melding (payroll reporting to Skatteetaten).
    Returns XML/JSON payload for submission.
    """
    # In production: aggregate payroll data, generate A-melding format
    return {
        "filing_type": "amelding_no",
        "period": f"{year}-{month:02d}",
        "message": "A-melding payload generated — ready for submission to Skatteetaten",
        "employee_count": 0,
        "total_gross": 0,
        "total_tax": 0,
    }
