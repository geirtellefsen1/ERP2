"""
Tests for migration 011 — GDPR Data Subject Rights tables and RLS.

Validates:
- Migration file exists and has correct metadata
- dsr_requests and dsr_artifacts tables have the expected columns
- RLS policies deny cross-tenant access (using the app_engine pattern
  from test_rls.py)
"""
from __future__ import annotations

import importlib
import importlib.util
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.database import SessionLocal, engine
from app.models import Agency, Client, DsrRequest, DsrArtifact
from app.services.tenant import set_tenant_context


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "011_dsr_requests.py"
)


def _load_migration_module():
    """Import the migration file without depending on Alembic's CLI."""
    spec = importlib.util.spec_from_file_location(
        "migration_011_dsr_requests", str(MIGRATION_PATH)
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# -- Non-superuser connection for RLS tests (same pattern as test_rls.py) ----

BASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://claud_erp:test@localhost:5432/claud_erp_test",
)
APP_URL = BASE_URL.replace("claud_erp:", "claud_erp_app:")

app_engine = create_engine(APP_URL, pool_pre_ping=True)
AppSession = sessionmaker(bind=app_engine, autocommit=False, autoflush=False)


# -- Migration metadata tests -----------------------------------------------


def test_migration_011_file_exists():
    assert MIGRATION_PATH.exists()


def test_migration_011_has_expected_metadata():
    module = _load_migration_module()
    assert module.revision == "011_dsr_requests"
    assert module.down_revision == "010_timescale_hypertables"


# -- Schema tests ------------------------------------------------------------


def test_dsr_request_table_columns():
    """Verify all expected columns exist on the dsr_requests table."""
    insp = inspect(engine)
    columns = {col["name"] for col in insp.get_columns("dsr_requests")}
    expected = {
        "id",
        "agency_id",
        "client_id",
        "subject_email",
        "subject_name",
        "request_type",
        "status",
        "received_at",
        "deadline_at",
        "completed_at",
        "notes",
        "created_at",
    }
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_dsr_artifact_table_columns():
    """Verify all expected columns exist on the dsr_artifacts table."""
    insp = inspect(engine)
    columns = {col["name"] for col in insp.get_columns("dsr_artifacts")}
    expected = {
        "id",
        "dsr_request_id",
        "artifact_type",
        "uri",
        "sha256",
        "created_at",
    }
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


# -- RLS isolation tests -----------------------------------------------------


@pytest.fixture
def two_agencies_with_dsr(db):
    """
    Seed two agencies, each with a DSR request and artifact.
    Uses the superuser session so RLS doesn't interfere with setup.
    """
    agency_a = Agency(name="DSR Agency A", slug="dsr-agency-a")
    agency_b = Agency(name="DSR Agency B", slug="dsr-agency-b")
    db.add_all([agency_a, agency_b])
    db.flush()

    now = datetime.now(timezone.utc)
    deadline = now + timedelta(days=30)

    dsr_a = DsrRequest(
        agency_id=agency_a.id,
        subject_email="alice@example.com",
        request_type="access",
        status="pending",
        deadline_at=deadline,
    )
    dsr_b = DsrRequest(
        agency_id=agency_b.id,
        subject_email="bob@example.com",
        request_type="erasure",
        status="pending",
        deadline_at=deadline,
    )
    db.add_all([dsr_a, dsr_b])
    db.flush()

    artifact_a = DsrArtifact(
        dsr_request_id=dsr_a.id,
        artifact_type="export_zip",
        uri="s3://bucket/dsr-a.zip",
        sha256="a" * 64,
    )
    artifact_b = DsrArtifact(
        dsr_request_id=dsr_b.id,
        artifact_type="erasure_confirmation",
        uri="s3://bucket/dsr-b.pdf",
        sha256="b" * 64,
    )
    db.add_all([artifact_a, artifact_b])
    db.commit()

    return {
        "agency_a": agency_a,
        "agency_b": agency_b,
        "dsr_a": dsr_a,
        "dsr_b": dsr_b,
        "artifact_a": artifact_a,
        "artifact_b": artifact_b,
    }


def test_rls_denies_cross_tenant(two_agencies_with_dsr):
    """Tenant A cannot see tenant B's DSR requests or artifacts."""
    seed = two_agencies_with_dsr
    app_db = AppSession()
    try:
        # Set context to agency A
        set_tenant_context(app_db, seed["agency_a"].id)

        # Should only see agency A's DSR request
        rows = app_db.execute(
            text("SELECT subject_email FROM dsr_requests")
        ).fetchall()
        assert len(rows) == 1
        assert rows[0].subject_email == "alice@example.com"

        # Should only see agency A's artifact (nested RLS)
        artifacts = app_db.execute(
            text("SELECT uri FROM dsr_artifacts")
        ).fetchall()
        assert len(artifacts) == 1
        assert artifacts[0].uri == "s3://bucket/dsr-a.zip"

        # Switch to agency B
        app_db.commit()
        set_tenant_context(app_db, seed["agency_b"].id)

        rows = app_db.execute(
            text("SELECT subject_email FROM dsr_requests")
        ).fetchall()
        assert len(rows) == 1
        assert rows[0].subject_email == "bob@example.com"

        artifacts = app_db.execute(
            text("SELECT uri FROM dsr_artifacts")
        ).fetchall()
        assert len(artifacts) == 1
        assert artifacts[0].uri == "s3://bucket/dsr-b.pdf"
    finally:
        app_db.close()


def test_rls_failsafe_returns_zero_dsr_rows(two_agencies_with_dsr):
    """Without the session variable set, no DSR rows are returned."""
    app_db = AppSession()
    try:
        rows = app_db.execute(text("SELECT id FROM dsr_requests")).fetchall()
        assert rows == []
        rows = app_db.execute(text("SELECT id FROM dsr_artifacts")).fetchall()
        assert rows == []
    finally:
        app_db.close()
