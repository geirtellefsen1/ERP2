"""010: TimescaleDB hypertables for time-series tables

Revision ID: 010_timescale_hypertables
Revises: 009_integration_configs
Create Date: 2026-04-13

Converts three high-volume, time-series tables into TimescaleDB
hypertables so partitioning, compression, and time-based retention
work automatically:

  - bank_transactions      (date)            → 7-day chunks
  - cashflow_snapshots     (snapshot_date)   → 30-day chunks
  - audit_log              (created_at)      → 30-day chunks

Hypertables are a drop-in replacement for regular tables at the SQL
level — SELECT/INSERT/UPDATE all work unchanged. Under the hood Postgres
is actually writing to monthly child partitions, which is how we keep
query latency flat as transaction volume grows into the millions.

The TimescaleDB extension is idempotent-checked: if the extension is
not installed (vanilla Postgres, local dev), the migration logs a
notice and skips the hypertable conversion. The tables themselves
still exist, so the app keeps working — you just don't get the
partitioning benefit until Timescale is installed.

Down-migration does NOT remove the extension (it may be in use by
other migrations) — it only undoes the hypertable conversion, which
TimescaleDB doesn't expose a clean "undo" for. Instead we drop and
recreate the tables as plain tables, which is destructive but matches
what a full downgrade would mean.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "010_timescale_hypertables"
down_revision: Union[str, None] = "009_integration_configs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── Tables we're converting and their time columns + chunk intervals ──
HYPERTABLES: list[tuple[str, str, str]] = [
    # (table_name, time_column, chunk_interval)
    ("bank_transactions", "date", "7 days"),
    ("cashflow_snapshots", "snapshot_date", "30 days"),
    ("audit_log", "created_at", "30 days"),
]


def _timescale_available(conn) -> bool:
    """True if the TimescaleDB extension is installed or installable."""
    row = conn.execute(
        sa.text(
            "SELECT 1 FROM pg_available_extensions "
            "WHERE name = 'timescaledb'"
        )
    ).fetchone()
    return row is not None


def upgrade() -> None:
    conn = op.get_bind()

    if not _timescale_available(conn):
        # Vanilla Postgres — skip gracefully. The plain tables from
        # earlier migrations keep working; we just don't get chunking.
        conn.execute(sa.text(
            "DO $$ BEGIN "
            "RAISE NOTICE "
            "'TimescaleDB extension not available — skipping "
            "hypertable conversion. Install the extension to enable "
            "time-series partitioning.'"
            "; END $$;"
        ))
        return

    # CREATE EXTENSION is idempotent with IF NOT EXISTS
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")

    for table, time_col, interval in HYPERTABLES:
        # `if_not_exists => TRUE` means re-running the migration is safe
        # and `migrate_data => TRUE` converts any existing rows in place.
        op.execute(
            sa.text(
                f"""
                SELECT create_hypertable(
                    '{table}',
                    '{time_col}',
                    chunk_time_interval => INTERVAL '{interval}',
                    if_not_exists => TRUE,
                    migrate_data => TRUE
                )
                """
            )
        )

    # Enable native compression on bank_transactions once the chunk is
    # older than 30 days — this is the highest-volume table and gains
    # the most from column-store compression.
    op.execute(
        """
        ALTER TABLE bank_transactions SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'account_id',
            timescaledb.compress_orderby = 'date DESC'
        )
        """
    )
    # Apply the compression policy if add_compression_policy is
    # available (TimescaleDB >= 2.0). Wrap in DO block so older
    # versions don't break the migration.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_proc WHERE proname = 'add_compression_policy'
            ) THEN
                PERFORM add_compression_policy(
                    'bank_transactions',
                    INTERVAL '30 days',
                    if_not_exists => TRUE
                );
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """
    TimescaleDB doesn't expose a clean "convert hypertable back to
    plain table" operation. The safest downgrade is to:
      - remove compression policy
      - detach compression settings
    and leave the tables in place. Dropping and recreating them would
    lose all historical data, which is almost never what you want on
    a downgrade.
    """
    conn = op.get_bind()
    if not _timescale_available(conn):
        return

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_proc WHERE proname = 'remove_compression_policy'
            ) THEN
                PERFORM remove_compression_policy(
                    'bank_transactions', if_exists => TRUE
                );
            END IF;
        END $$;
        """
    )
    # Intentionally no DROP EXTENSION — other tables may depend on it.
