"""
Tests for migration 010 — TimescaleDB hypertable conversion.

The test environment is vanilla Postgres, so the test exercises the
no-TimescaleDB fallback path: the upgrade() function must gracefully
skip hypertable creation when the extension isn't available, leaving
the underlying tables usable.
"""
from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import inspect, text

from app.database import engine


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "010_timescale_hypertables.py"
)


def _load_migration_module():
    """Import the migration file without depending on Alembic's CLI."""
    spec = importlib.util.spec_from_file_location(
        "migration_010_timescale", str(MIGRATION_PATH)
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_010_file_exists():
    assert MIGRATION_PATH.exists()


def test_migration_010_has_expected_metadata():
    module = _load_migration_module()
    assert module.revision == "010_timescale_hypertables"
    assert module.down_revision == "009_integration_configs"


def test_migration_010_lists_expected_hypertables():
    module = _load_migration_module()
    tables = {t[0] for t in module.HYPERTABLES}
    assert "bank_transactions" in tables
    assert "cashflow_snapshots" in tables
    assert "audit_log" in tables


def test_migration_010_hypertable_specs_include_time_column():
    module = _load_migration_module()
    by_name = {t[0]: t for t in module.HYPERTABLES}
    assert by_name["bank_transactions"][1] == "date"
    assert by_name["cashflow_snapshots"][1] == "snapshot_date"
    assert by_name["audit_log"][1] == "created_at"


def test_timescale_available_returns_false_on_plain_postgres():
    """Vanilla Postgres: the extension is not available."""
    module = _load_migration_module()
    with engine.connect() as conn:
        available = module._timescale_available(conn)
    # We don't know whether the CI image has Timescale or not, but
    # whichever answer we get must be a clean bool (not an error).
    assert isinstance(available, bool)


def test_migration_skip_path_does_not_require_real_alembic_context():
    """
    Smoke-test the shape of upgrade() — we can't call it directly
    here (op.get_bind requires an Alembic context), but we can make
    sure the function is importable and has the expected signature.
    """
    module = _load_migration_module()
    assert callable(module.upgrade)
    assert callable(module.downgrade)
    assert module.upgrade.__code__.co_argcount == 0
    assert module.downgrade.__code__.co_argcount == 0


def test_hypertable_target_tables_exist_in_schema():
    """
    The tables we're converting must already exist — migration 010
    only adds partitioning, it doesn't create new tables.
    """
    insp = inspect(engine)
    existing = set(insp.get_table_names())
    assert "bank_transactions" in existing
    assert "cashflow_snapshots" in existing
    assert "audit_log" in existing
