"""
Auth tests — refactored to use the shared conftest fixtures that provide
clean DB state between tests. The original module-level setup_db fixture
dropped all tables on teardown, which broke any tests that ran afterwards.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from passlib.context import CryptContext
from app.main import app
from app.models import User, Agency

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture
def test_agency(db):
    agency = Agency(name="Test Agency", slug="test-agency")
    db.add(agency)
    db.commit()
    db.refresh(agency)
    return agency


@pytest.fixture
def test_user(db, test_agency):
    user = User(
        email="test@example.com",
        hashed_password=pwd_context.hash("password123"),
        full_name="Test User",
        agency_id=test_agency.id,
        role="agent",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.mark.anyio
async def test_register(test_agency):
    """Register creates a new user and returns a token."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "email": "new@example.com",
            "password": "securepass123",
            "full_name": "New User",
            "agency_id": test_agency.id,
        }
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["user"]["email"] == "new@example.com"
        assert "access_token" in data


@pytest.mark.anyio
async def test_register_duplicate_email(db, test_user):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Duplicate",
            "agency_id": 1,
        }
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 400


@pytest.mark.anyio
async def test_login_success(db, test_user):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == "test@example.com"


@pytest.mark.anyio
async def test_login_wrong_password(db, test_user):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )
        assert resp.status_code == 401


@pytest.mark.anyio
async def test_login_user_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "notfound@example.com", "password": "password"},
        )
        assert resp.status_code == 401
