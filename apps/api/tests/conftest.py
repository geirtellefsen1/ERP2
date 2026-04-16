"""Shared test fixtures for BPO Nexus API tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import Base
from app.database import get_db
from app.auth import get_current_user, CurrentUser

# In-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    """Yield a database session for direct DB operations in tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def _override_get_db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def _override_get_current_user():
    return CurrentUser(id=1, agency_id=1, email="test@example.com", role="admin")


app.dependency_overrides[get_db] = _override_get_db
app.dependency_overrides[get_current_user] = _override_get_current_user


@pytest.fixture()
def client():
    """Return a TestClient wired to the overridden app."""
    return TestClient(app)
