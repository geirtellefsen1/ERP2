import pytest
from httpx import AsyncClient, ASGITransport
from decimal import Decimal
from app.main import app
from app.database import SessionLocal, engine
from app.models import Base, Agency, User, Client, Account
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    # Keep DB for inspection

@pytest.fixture
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_data(db):
    agency = Agency(name="Journal Test Agency", slug="journal-test")
    db.add(agency); db.commit(); db.refresh(agency)
    user = User(
        email="journal@test.com",
        hashed_password=pwd_context.hash("test1234"),
        full_name="Journal Tester",
        agency_id=agency.id, role="admin", is_active=True,
    )
    db.add(user); db.commit(); db.refresh(user)
    client = Client(
        name="Test Client",
        slug="test-client-j",
        agency_id=agency.id, country="ZA",
    )
    db.add(client); db.commit(); db.refresh(client)
    accounts = []
    for code, name, atype in [
        ("1000", "Bank Account", "asset"),
        ("2000", "Accounts Payable", "liability"),
        ("3000", "Owner's Equity", "equity"),
        ("4000", "Sales Revenue", "revenue"),
        ("5000", "Rent Expense", "expense"),
    ]:
        a = Account(code=code, name=name, account_type=atype, client_id=client.id)
        db.add(a); accounts.append(a)
    db.commit()
    for a in accounts: db.refresh(a)
    return {"agency": agency, "user": user, "client": client, "accounts": accounts}


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_journal_must_balance():
    """Journal entries with unbalanced debits/credits must be rejected."""
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
        assert resp.status_code in [400, 422], f"Expected 400/422, got {resp.status_code}: {resp.text}"


@pytest.mark.anyio
async def test_journal_min_two_lines():
    """Journal entries must have at least 2 lines."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "client_id": 1,
            "entry_date": "2026-01-01T00:00:00Z",
            "lines": [
                {"account_id": 1, "debit": "100.00", "credit": "0"},
            ],
        }
        resp = await client.post("/api/v1/journal", json=payload)
        assert resp.status_code in [400, 422]
