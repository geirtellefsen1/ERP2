"""007: Cashflow snapshots and report deliveries

Revision ID: 007_cashflow_and_reports
Revises: 006_row_level_security
Create Date: 2026-04-12

Adds the persistent storage tables for Tier 3 features:

- cashflow_snapshots: a forecast result captured at a point in time so
  the dashboard can show "the forecast as of [date]" history and so
  alerts can compare current forecast vs. last week's forecast.

- report_deliveries: tracks every monthly report that was generated and
  sent (or scheduled to send), with a pointer to the PDF in object
  storage and the delivery receipt from the deliverer.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "007_cashflow_and_reports"
down_revision: Union[str, None] = "006_row_level_security"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── cashflow_snapshots ─────────────────────────────────────────
    op.create_table(
        "cashflow_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column(
            "snapshot_date",
            sa.Date(),
            nullable=False,
            comment="The day this forecast was generated",
        ),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column(
            "opening_balance_minor",
            sa.BigInteger(),
            nullable=False,
            comment="Opening balance in currency minor units (øre/cents)",
        ),
        sa.Column(
            "closing_balance_minor",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "weeks_count",
            sa.Integer(),
            nullable=False,
            server_default="13",
        ),
        sa.Column(
            "threshold_minor",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "breach_week_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "weeks_json",
            sa.Text(),
            nullable=False,
            comment="Full week-by-week breakdown as JSON array",
        ),
        sa.Column(
            "narrative",
            sa.Text(),
            nullable=True,
            comment="AI-generated commentary in the client's language",
        ),
        sa.Column(
            "narrative_language",
            sa.String(10),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cashflow_snapshots_client_id", "cashflow_snapshots", ["client_id"])
    op.create_index(
        "ix_cashflow_snapshots_snapshot_date",
        "cashflow_snapshots",
        ["snapshot_date"],
    )

    # ── report_deliveries ──────────────────────────────────────────
    op.create_table(
        "report_deliveries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column(
            "report_type",
            sa.String(50),
            nullable=False,
            comment="e.g. 'monthly_management', 'quarterly_summary'",
        ),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column(
            "pdf_path",
            sa.String(500),
            nullable=True,
            comment="DO Spaces path to the rendered PDF (empty for failed runs)",
        ),
        sa.Column(
            "pdf_size_bytes",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
            comment="pending, generated, sent, failed",
        ),
        sa.Column("recipient_email", sa.String(255), nullable=True),
        sa.Column(
            "delivery_provider",
            sa.String(50),
            nullable=True,
            comment="resend, mock, etc.",
        ),
        sa.Column("delivery_message_id", sa.String(255), nullable=True),
        sa.Column("delivery_error", sa.Text(), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_report_deliveries_client_id", "report_deliveries", ["client_id"])
    op.create_index("ix_report_deliveries_status", "report_deliveries", ["status"])
    op.create_index(
        "ix_report_deliveries_scheduled_for",
        "report_deliveries",
        ["scheduled_for"],
    )

    # Both new tables get RLS — same fail-safe pattern as the ones in
    # migration 006. They go through clients to find agency_id.
    for table in ("cashflow_snapshots", "report_deliveries"):
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON "{table}"
            USING (
                current_setting('app.current_agency_id', true) = '0'
                OR client_id IN (
                    SELECT id FROM clients
                    WHERE agency_id = NULLIF(current_setting('app.current_agency_id', true), '')::int
                )
            )
            """
        )


def downgrade() -> None:
    for table in ("report_deliveries", "cashflow_snapshots"):
        op.execute(f'DROP POLICY IF EXISTS tenant_isolation ON "{table}"')
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY')
    op.drop_index("ix_report_deliveries_scheduled_for", table_name="report_deliveries")
    op.drop_index("ix_report_deliveries_status", table_name="report_deliveries")
    op.drop_index("ix_report_deliveries_client_id", table_name="report_deliveries")
    op.drop_table("report_deliveries")
    op.drop_index("ix_cashflow_snapshots_snapshot_date", table_name="cashflow_snapshots")
    op.drop_index("ix_cashflow_snapshots_client_id", table_name="cashflow_snapshots")
    op.drop_table("cashflow_snapshots")
