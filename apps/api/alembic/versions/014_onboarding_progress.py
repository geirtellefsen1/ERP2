"""Add onboarding_progress table

Revision ID: 014_onboarding_progress
Revises: 010_timescale_hypertables
Create Date: 2026-04-16
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "014_onboarding_progress"
down_revision = "010_timescale_hypertables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "onboarding_progress",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "agency_id",
            sa.Integer(),
            sa.ForeignKey("agencies.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("current_step", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("step_data", sa.Text(), nullable=True),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Row-Level Security: restrict rows to the owning agency
    # Same pattern as migration 006 — uses direct agency_id column
    op.execute(
        "ALTER TABLE onboarding_progress ENABLE ROW LEVEL SECURITY"
    )
    op.execute(
        "CREATE POLICY onboarding_progress_agency_isolation "
        "ON onboarding_progress "
        "USING ("
        "  current_setting('app.current_agency_id', true) = '0'"
        "  OR agency_id = NULLIF(current_setting('app.current_agency_id', true), '')::int"
        ")"
    )


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS onboarding_progress_agency_isolation "
        "ON onboarding_progress"
    )
    op.drop_table("onboarding_progress")
