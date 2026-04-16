"""
Shared pytest fixtures and test hygiene for the BPO Nexus API.

Provides:
- autouse DB reset fixture that truncates all tables between tests so tests
  are isolated (fixes pre-existing state-leak bugs in test_auth.py etc.)
- test_agency fixture
- test_user fixture
- auth_headers fixture for authenticated test requests
"""
from __future__ import annotations

import os
import pytest
from typing import Generator

# Ensure config is loaded with test defaults BEFORE importing app modules
os.environ.setdefault(
    "CLAUDE_API_KEY", "sk-ant-test-key-placeholder-for-jwt-signing-00"
)

from fastapi.testclient import TestClient
from sqlalchemy import text
from app.database import SessionLocal, engine
from app.models import Base
from app.main import app


# ── Schema setup ──────────────────────────────────────────────────────────────


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    """Create all tables once per test session."""
    Base.metadata.create_all(bind=engine)
    yield
    # Intentionally do NOT drop tables — leaves DB state for post-mortem inspection


@pytest.fixture(autouse=True)
def _clean_db():
    """
    Truncate all tables before each test so tests are independent.
    Runs after _create_schema so the tables definitely exist.
    """
    with engine.connect() as conn:
        # Build a single TRUNCATE statement with RESTART IDENTITY CASCADE so
        # FKs don't block us and serial IDs reset to 1.
        table_names = [t.name for t in reversed(Base.metadata.sorted_tables)]
        if table_names:
            joined = ", ".join(f'"{name}"' for name in table_names)
            conn.execute(text(f"TRUNCATE {joined} RESTART IDENTITY CASCADE"))
            conn.commit()
    yield


# ── Async test backend ──────────────────────────────────────────────────────


@pytest.fixture
def anyio_backend():
    return "asyncio"


# ── Convenience fixtures ────────────────────────────────────────────────────


@pytest.fixture
def db() -> Generator:
    """Direct SQLAlchemy session for fixture setup."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    """Provide a FastAPI TestClient for integration tests."""
    return TestClient(app)
