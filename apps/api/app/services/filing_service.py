"""Statutory filing service for multi-jurisdiction VAT and tax submissions."""

from datetime import date, datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from xml.etree.ElementTree import Element, SubElement, tostring
import uuid
import json

from app.models.filing import FilingRecord, FilingDeadline


def prepare_vat_filing(
    client_id: int,
    jurisdiction: str,
    period_start: date,
    period_end: date,
) -> dict:
    """Prepare VAT filing data summary for a given client and jurisdiction.

    Returns a dict with summary data that can be used to generate
    the jurisdiction-specific XML or JSON submission.
    """
    # In production, this would pull actual ledger/transaction data
    # for the client within the given period. For now, return mock summary.
    filing_data = {
        "client_id": client_id,
        "jurisdiction": jurisdiction,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "total_sales": 100000.00,
        "total_purchases": 60000.00,
        "output_vat": 15000.00,
        "input_vat": 9000.00,
        "net_vat_payable": 6000.00,
        "currency": _get_currency(jurisdiction),
    }
    return filing_data


def _get_currency(jurisdiction: str) -> str:
    """Return the default currency for a jurisdiction."""
    currencies = {
        "NO": "NOK",
        "ZA": "ZAR",
        "UK": "GBP",
        "EU": "EUR",
    }
    return currencies.get(jurisdiction, "USD")


def generate_vat_xml(jurisdiction: str, filing_data: dict) -> str:
    """Generate the jurisdiction-specific XML or JSON for VAT filing.

    - Norway (NO): MVA Return XML
    - South Africa (ZA): VAT201 JSON format
    - UK: HMRC MTD JSON format
    - EU: Generic VAT_RETURN XML
    """
    jurisdiction = jurisdiction.upper()

    if jurisdiction == "NO":
        return _generate_norway_mva(filing_data)
    elif jurisdiction == "ZA":
        return _generate_south_africa_vat201(filing_data)
    elif jurisdiction == "UK":
        return _generate_uk_mtd(filing_data)
    elif jurisdiction == "EU":
        return _generate_eu_vat_return(filing_data)
    else:
        raise ValueError(f"Unsupported jurisdiction: {jurisdiction}")


def _generate_norway_mva(data: dict) -> str:
    """Generate Norway MVA Return XML."""
    root = Element("MVAReturn")
    root.set("xmlns", "urn:skatteetaten:fastsetting:avgift:mva:skattemeldingformerverdiavgift:v1.0")

    period = SubElement(root, "Period")
    SubElement(period, "StartDate").text = data["period_start"]
    SubElement(period, "EndDate").text = data["period_end"]

    details = SubElement(root, "TaxDetails")
    SubElement(details, "TotalSales").text = str(data["total_sales"])
    SubElement(details, "TotalPurchases").text = str(data["total_purchases"])
    SubElement(details, "OutputVAT").text = str(data["output_vat"])
    SubElement(details, "InputVAT").text = str(data["input_vat"])
    SubElement(details, "NetVATPayable").text = str(data["net_vat_payable"])

    SubElement(root, "Currency").text = data.get("currency", "NOK")

    return '<?xml version="1.0" encoding="utf-8"?>\n' + tostring(root, encoding="unicode")


def _generate_south_africa_vat201(data: dict) -> str:
    """Generate South Africa VAT201 JSON format."""
    vat201 = {
        "formType": "VAT201",
        "taxPeriod": {
            "startDate": data["period_start"],
            "endDate": data["period_end"],
        },
        "fields": {
            "field1": data["total_sales"],
            "field2": data["output_vat"],
            "field3": data["total_purchases"],
            "field4": data["input_vat"],
            "field5": data["net_vat_payable"],
        },
        "currency": data.get("currency", "ZAR"),
    }
    return json.dumps(vat201, indent=2)


def _generate_uk_mtd(data: dict) -> str:
    """Generate UK HMRC Making Tax Digital (MTD) JSON format."""
    mtd_return = {
        "periodKey": f"{data['period_start']}_{data['period_end']}",
        "vatDueSales": data["output_vat"],
        "vatDueAcquisitions": 0.0,
        "totalVatDue": data["output_vat"],
        "vatReclaimedCurrPeriod": data["input_vat"],
        "netVatDue": data["net_vat_payable"],
        "totalValueSalesExVAT": data["total_sales"],
        "totalValuePurchasesExVAT": data["total_purchases"],
        "totalValueGoodsSuppliedExVAT": 0.0,
        "totalAcquisitionsExVAT": 0.0,
        "finalised": True,
    }
    return json.dumps(mtd_return, indent=2)


def _generate_eu_vat_return(data: dict) -> str:
    """Generate EU generic VAT_RETURN XML."""
    root = Element("VAT_RETURN")
    root.set("xmlns", "urn:eu:tax:vat:return:v1")

    period = SubElement(root, "ReportingPeriod")
    SubElement(period, "StartDate").text = data["period_start"]
    SubElement(period, "EndDate").text = data["period_end"]

    supplies = SubElement(root, "Supplies")
    SubElement(supplies, "TotalSales").text = str(data["total_sales"])
    SubElement(supplies, "TotalPurchases").text = str(data["total_purchases"])

    tax = SubElement(root, "TaxAmounts")
    SubElement(tax, "OutputVAT").text = str(data["output_vat"])
    SubElement(tax, "InputVAT").text = str(data["input_vat"])
    SubElement(tax, "NetPayable").text = str(data["net_vat_payable"])

    SubElement(root, "Currency").text = data.get("currency", "EUR")

    return '<?xml version="1.0" encoding="utf-8"?>\n' + tostring(root, encoding="unicode")


def get_upcoming_deadlines(
    client_id: Optional[int],
    days_ahead: int,
    db: Session,
) -> list:
    """Get upcoming filing deadlines within the given number of days.

    If client_id is provided, filter to that client. Otherwise return all.
    """
    today = date.today()
    cutoff = today + timedelta(days=days_ahead)

    query = db.query(FilingDeadline).filter(
        FilingDeadline.due_date >= today,
        FilingDeadline.due_date <= cutoff,
    )

    if client_id is not None:
        query = query.filter(FilingDeadline.client_id == client_id)

    return query.order_by(FilingDeadline.due_date.asc()).all()


def submit_filing(filing_id: int, db: Session) -> FilingRecord:
    """Mark a filing as submitted (mock submission).

    In production, this would call the actual tax authority API.
    """
    filing = db.query(FilingRecord).filter(FilingRecord.id == filing_id).first()
    if filing is None:
        raise ValueError(f"Filing record {filing_id} not found")

    if filing.status not in ("draft",):
        raise ValueError(f"Filing {filing_id} cannot be submitted (status: {filing.status})")

    filing.status = "submitted"
    filing.submission_id = f"SUB-{uuid.uuid4().hex[:12].upper()}"
    filing.submitted_at = datetime.now(timezone.utc)
    filing.response_data = {
        "status": "accepted",
        "message": "Filing received successfully (mock)",
        "reference": filing.submission_id,
    }

    db.commit()
    db.refresh(filing)
    return filing
