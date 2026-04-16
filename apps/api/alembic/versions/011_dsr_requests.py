"""011: GDPR Data Subject Rights tables

Revision ID: 011_dsr_requests
Revises: 010_timescale_hypertables
Create Date: 2026-04-16

Adds two tables for tracking GDPR Data Subject Rights (DSR) requests:

  - dsr_requests      — the incoming request (access, erasure, portability,
                         rectification) with its deadline and status
  - dsr_artifacts     — files produced while fulfilling a DSR (export zips,
                         erasure confirmation PDFs, etc.)

RLS policies follow the same pattern established in migration 006:

  - dsr_requests has a direct agency_id column -> _enable_rls_with_direct_agency
  - dsr_artifacts is nested via dsr_request_id -> _enable_rls_via_nested with a
    subquery through dsr_requests.agency_id
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "011_dsr_requests"
down_revision: Union[str, None] = "010_timescale_hypertables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# -- RLS helpers (same pattern as 006_row_level_security) --------------------


def _enable_rls_with_direct_agency(table: str) -> None:
    """Table has an agency_id column directly."""
    op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
    op.execute(
        f"""
        CREATE POLICY tenant_isolation ON "{table}"
        USING (
            current_setting('app.current_agency_id', true) = '0'
            OR agency_id = NULLIF(current_setting('app.current_agency_id', true), '')::int
        )
        """
    )


def _enable_rls_via_nested(table: str, parent_lookup_sql: str) -> None:
    """Table is nested — scope via the parent lookup SQL to reach agency_id."""
    op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
    op.execute(
        f"""
        CREATE POLICY tenant_isolation ON "{table}"
        USING (
            current_setting('app.current_agency_id', true) = '0'
            OR dsr_request_id IN (
                SELECT id FROM dsr_requests
                WHERE agency_id = NULLIF(current_setting('app.current_agency_id', true), '')::int
            )
        )
        """
    )


def upgrade() -> None:
    # -- dsr_requests --------------------------------------------------------
    op.create_table(
        "dsr_requests",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "agency_id",
            sa.Integer,
            sa.ForeignKey("agencies.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "client_id",
            sa.Integer,
            sa.ForeignKey("clients.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("subject_email", sa.String(255), nullable=False, index=True),
        sa.Column("subject_name", sa.String(255)),
        sa.Column("request_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("notes", sa.Text),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # -- dsr_artifacts -------------------------------------------------------
    op.create_table(
        "dsr_artifacts",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "dsr_request_id",
            sa.Integer,
            sa.ForeignKey("dsr_requests.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("artifact_type", sa.String(50), nullable=False),
        sa.Column("uri", sa.String(500), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # -- RLS policies --------------------------------------------------------
    _enable_rls_with_direct_agency("dsr_requests")
    _enable_rls_via_nested(
        "dsr_artifacts",
        "SELECT dr.agency_id FROM dsr_requests dr WHERE dr.id = dsr_artifacts.dsr_request_id",
    )


def downgrade() -> None:
    # Drop policies first, then tables (reverse order of creation)
    for table in ("dsr_artifacts", "dsr_requests"):
        op.execute(f'DROP POLICY IF EXISTS tenant_isolation ON "{table}"')
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY')

    op.drop_table("dsr_artifacts")
    op.drop_table("dsr_requests")
