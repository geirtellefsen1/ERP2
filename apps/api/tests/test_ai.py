from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers import ai

# Create a test app with the AI router included
# (main.py will integrate this router later; tests must be self-contained)
test_app = FastAPI()
test_app.include_router(ai.router)

client = TestClient(test_app)


def test_extract_document_requires_auth():
    response = client.post(
        "/ai/extract-document",
        json={"document_text": "Invoice #123", "document_type": "invoice"},
    )
    assert response.status_code == 401


def test_suggest_gl_code_requires_auth():
    response = client.post(
        "/ai/suggest-gl-code",
        json={"description": "Office supplies purchase"},
    )
    assert response.status_code == 401


def test_detect_anomalies_requires_auth():
    response = client.post(
        "/ai/detect-anomalies",
        json={"transactions_json": "[]"},
    )
    assert response.status_code == 401


def test_generate_narrative_requires_auth():
    response = client.post(
        "/ai/generate-narrative",
        json={"financials_json": "{}"},
    )
    assert response.status_code == 401


def test_ai_prompts_module_loads():
    """Test that the AI prompts module loads and functions return strings."""
    from app.services.ai_prompts import (
        document_extraction_prompt,
        gl_coding_prompt,
        anomaly_detection_prompt,
        report_narrative_prompt,
    )

    assert isinstance(document_extraction_prompt("invoice"), str)
    assert "invoice" in document_extraction_prompt("invoice")

    assert isinstance(gl_coding_prompt("office supplies"), str)
    assert isinstance(gl_coding_prompt("rent", "1000 Cash\n2000 Expenses"), str)

    assert isinstance(anomaly_detection_prompt("[]"), str)
    assert isinstance(report_narrative_prompt("{}"), str)


def test_ai_client_module_loads():
    """Test that the AI client module loads and can be instantiated."""
    from app.services.ai_client import ClaudeClient

    ai_client = ClaudeClient()
    assert ai_client.base_url == "https://api.anthropic.com/v1"
    assert isinstance(ai_client.api_key, str)
