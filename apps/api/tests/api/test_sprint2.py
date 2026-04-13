import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        # Version is set in main.py; assert format rather than exact value so
        # this test doesn't drift every time we bump it.
        assert "version" in data
        assert isinstance(data["version"], str)


@pytest.mark.anyio
async def test_api_root():
    """Root endpoint should return a message and docs pointer."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert "docs" in data


@pytest.mark.anyio
async def test_list_agencies_empty():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/agencies")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


@pytest.mark.anyio
async def test_create_agency():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "name": "Saga Advisory AS",
            "slug": "saga-advisory",
            "subscription_tier": "growth",
            "countries_enabled": "ZA,NO,UK",
        }
        resp = await client.post("/api/v1/agencies", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Saga Advisory AS"
        assert data["slug"] == "saga-advisory"
        assert data["id"] is not None


@pytest.mark.anyio
async def test_create_agency_duplicate_slug():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"name": "Test Agency", "slug": "duplicate-slug"}
        await client.post("/api/v1/agencies", json=payload)
        resp = await client.post("/api/v1/agencies", json=payload)
        assert resp.status_code == 400


@pytest.mark.anyio
async def test_get_agency_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/agencies/99999")
        assert resp.status_code == 404
