from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers import filings
import json

# Create a test app with the filings router included
# (main.py will integrate this router later; tests must be self-contained)
test_app = FastAPI()
test_app.include_router(filings.router)

client = TestClient(test_app)


# ---- Auth-required endpoint tests (401 without token) ----

def test_create_filing_requires_auth():
    response = client.post("/filings", json={
        "client_id": 1,
        "jurisdiction": "NO",
        "filing_type": "VAT",
    })
    assert response.status_code == 401


def test_list_filings_requires_auth():
    response = client.get("/filings")
    assert response.status_code == 401


def test_get_filing_requires_auth():
    response = client.get("/filings/1")
    assert response.status_code == 401


def test_submit_filing_requires_auth():
    response = client.post("/filings/1/submit")
    assert response.status_code == 401


def test_prepare_vat_requires_auth():
    response = client.post("/filings/prepare-vat", json={
        "client_id": 1,
        "jurisdiction": "NO",
        "period_start": "2026-01-01",
        "period_end": "2026-03-31",
    })
    assert response.status_code == 401


def test_create_deadline_requires_auth():
    response = client.post("/filings/deadlines", json={
        "client_id": 1,
        "jurisdiction": "NO",
        "filing_type": "VAT",
        "due_date": "2026-05-10",
    })
    assert response.status_code == 401


def test_upcoming_deadlines_requires_auth():
    response = client.get("/filings/deadlines/upcoming")
    assert response.status_code == 401


# ---- VAT XML generation tests ----

def test_vat_xml_norway():
    from app.services.filing_service import prepare_vat_filing, generate_vat_xml
    from datetime import date

    filing_data = prepare_vat_filing(1, "NO", date(2026, 1, 1), date(2026, 3, 31))
    xml = generate_vat_xml("NO", filing_data)
    assert "<MVAReturn" in xml
    assert "<OutputVAT>" in xml
    assert "<InputVAT>" in xml
    assert "<NetVATPayable>" in xml
    assert "NOK" in xml


def test_vat_xml_south_africa():
    from app.services.filing_service import prepare_vat_filing, generate_vat_xml
    from datetime import date

    filing_data = prepare_vat_filing(1, "ZA", date(2026, 1, 1), date(2026, 3, 31))
    result = generate_vat_xml("ZA", filing_data)
    parsed = json.loads(result)
    assert parsed["formType"] == "VAT201"
    assert "fields" in parsed
    assert parsed["currency"] == "ZAR"


def test_vat_xml_uk():
    from app.services.filing_service import prepare_vat_filing, generate_vat_xml
    from datetime import date

    filing_data = prepare_vat_filing(1, "UK", date(2026, 1, 1), date(2026, 3, 31))
    result = generate_vat_xml("UK", filing_data)
    parsed = json.loads(result)
    assert "vatDueSales" in parsed
    assert "netVatDue" in parsed
    assert "totalValueSalesExVAT" in parsed
    assert parsed["finalised"] is True


def test_vat_xml_eu():
    from app.services.filing_service import prepare_vat_filing, generate_vat_xml
    from datetime import date

    filing_data = prepare_vat_filing(1, "EU", date(2026, 1, 1), date(2026, 3, 31))
    xml = generate_vat_xml("EU", filing_data)
    assert "<VAT_RETURN" in xml
    assert "<OutputVAT>" in xml
    assert "<InputVAT>" in xml
    assert "<NetPayable>" in xml
    assert "EUR" in xml


def test_vat_xml_unsupported_jurisdiction():
    from app.services.filing_service import generate_vat_xml
    import pytest

    with pytest.raises(ValueError, match="Unsupported jurisdiction"):
        generate_vat_xml("XX", {"period_start": "2026-01-01", "period_end": "2026-03-31"})


# ---- Service import test ----

def test_filing_service_imports():
    from app.services.filing_service import (
        prepare_vat_filing,
        generate_vat_xml,
        get_upcoming_deadlines,
        submit_filing,
    )
    assert callable(prepare_vat_filing)
    assert callable(generate_vat_xml)
    assert callable(get_upcoming_deadlines)
    assert callable(submit_filing)


def test_filing_model_imports():
    from app.models.filing import FilingRecord, FilingDeadline
    assert FilingRecord.__tablename__ == "filing_records"
    assert FilingDeadline.__tablename__ == "filing_deadlines"
