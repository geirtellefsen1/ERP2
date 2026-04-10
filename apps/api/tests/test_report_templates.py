import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routers.report_templates import router as report_templates_router
from app.services.commentary_service import (
    generate_commentary,
    build_report_html,
    get_tone_guidance,
)

# Register the report_templates router so endpoints are available for testing
app.include_router(report_templates_router)

client = TestClient(app)


# --- Auth tests: all endpoints return 401 without auth token ---

def test_create_template_requires_auth():
    response = client.post("/reporting/templates", json={"name": "Test Template"})
    assert response.status_code == 401


def test_list_templates_requires_auth():
    response = client.get("/reporting/templates")
    assert response.status_code == 401


def test_get_template_requires_auth():
    response = client.get("/reporting/templates/1")
    assert response.status_code == 401


def test_update_template_requires_auth():
    response = client.put("/reporting/templates/1", json={"name": "Updated"})
    assert response.status_code == 401


def test_generate_report_requires_auth():
    response = client.post("/reporting/generate", json={
        "template_id": 1,
        "client_id": 1,
        "financial_data": {},
    })
    assert response.status_code == 401


def test_list_reports_requires_auth():
    response = client.get("/reporting/reports")
    assert response.status_code == 401


def test_get_report_requires_auth():
    response = client.get("/reporting/reports/1")
    assert response.status_code == 401


def test_get_report_html_requires_auth():
    response = client.get("/reporting/reports/1/html")
    assert response.status_code == 401


# --- Commentary service tests ---

@pytest.mark.asyncio
async def test_generate_commentary_returns_non_empty():
    """generate_commentary returns a non-empty string."""
    result = await generate_commentary(
        client_name="Acme Corp",
        period="2026-01-01 to 2026-03-31",
        financial_data={
            "total_revenue": 500000,
            "total_expenses": 350000,
            "net_income": 150000,
        },
        tone="formal",
        length="full",
    )
    assert isinstance(result, str)
    assert len(result) > 0


def test_build_report_html_contains_client_name():
    """build_report_html returns valid HTML containing the client name."""
    html = build_report_html(
        client_name="Acme Corp",
        period="Q1 2026",
        commentary="The company performed well during this quarter.",
        financial_data={
            "total_revenue": 500000,
            "total_expenses": 350000,
            "net_income": 150000,
        },
    )
    assert isinstance(html, str)
    assert "<html" in html
    assert "Acme Corp" in html
    assert "</html>" in html


def test_build_report_html_contains_commentary():
    """build_report_html includes the commentary text."""
    commentary = "Revenue grew by 15% year-over-year."
    html = build_report_html(
        client_name="Test Co",
        period="2026",
        commentary=commentary,
        financial_data={"total_revenue": 100000},
    )
    assert commentary in html


def test_tone_guidance_returns_different_text():
    """All 3 tones return different guidance text."""
    formal = get_tone_guidance("formal")
    conversational = get_tone_guidance("conversational")
    technical = get_tone_guidance("technical")

    assert isinstance(formal, str)
    assert isinstance(conversational, str)
    assert isinstance(technical, str)

    # All three must be non-empty and distinct
    assert len(formal) > 0
    assert len(conversational) > 0
    assert len(technical) > 0
    assert formal != conversational
    assert formal != technical
    assert conversational != technical


def test_tone_guidance_unknown_falls_back_to_formal():
    """Unknown tone falls back to formal guidance."""
    unknown = get_tone_guidance("unknown_tone")
    formal = get_tone_guidance("formal")
    assert unknown == formal
