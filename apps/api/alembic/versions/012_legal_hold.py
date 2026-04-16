"""Add legal_holds table

Revision ID: 012_legal_hold
Revises: 011_dsr_requests
Create Date: 2026-04-16
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "012_legal_hold"
down_revision = "011_dsr_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "legal_holds",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "agency_id",
            sa.Integer(),
            sa.ForeignKey("agencies.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "client_id",
            sa.Integer(),
            sa.ForeignKey("clients.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("subject_email", sa.String(255), nullable=True, index=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
    )

    # RLS policy — restrict to agency rows
    op.execute(
        "ALTER TABLE legal_holds ENABLE ROW LEVEL SECURITY"
    )
    op.execute(
        """
        CREATE POLICY legal_holds_agency_isolation ON legal_holds
        USING (
            current_setting('app.current_agency_id', true) = '0'
            OR agency_id = NULLIF(current_setting('app.current_agency_id', true), '')::int
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS legal_holds_agency_isolation ON legal_holds")
    op.drop_table("legal_holds")
