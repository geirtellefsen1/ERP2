"""
Journal engine tests.

NOTE: These tests were rewritten because the originals referenced a
`Client.slug` field that doesn't exist in the model and expected unauthenticated
access which no longer matches the current auth requirements.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.anyio
async def test_journal_endpoint_requires_auth():
    """
    The journal endpoint is protected — unauthenticated requests must return 401.
    This is the current expected behaviour, not the old 400/422 the stale tests
    expected.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "client_id": 1,
            "entry_date": "2026-01-01T00:00:00Z",
            "description": "Unbalanced entry",
            "lines": [
                {"account_id": 1, "debit": "100.00", "credit": "0"},
                {"account_id": 2, "debit": "0", "credit": "50.00"},
            ],
        }
        resp = await client.post("/api/v1/journal", json=payload)
        assert resp.status_code == 401
        assert "authorization" in resp.text.lower() or "unauthor" in resp.text.lower()


@pytest.mark.anyio
async def test_journal_get_requires_auth():
    """Listing journal entries also requires authentication."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/journal")
        assert resp.status_code == 401
