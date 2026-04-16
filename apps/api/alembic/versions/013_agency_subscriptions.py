"""Add agency_subscriptions table

Revision ID: 013_agency_subscriptions
Revises: 012_legal_hold
Create Date: 2026-04-16
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "013_agency_subscriptions"
down_revision = "012_legal_hold"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agency_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "agency_id",
            sa.Integer(),
            sa.ForeignKey("agencies.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("stripe_customer_id", sa.String(255), nullable=False),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column(
            "tier",
            sa.String(50),
            nullable=False,
            server_default="starter",
        ),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "current_period_end",
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
    # Same pattern as migration 006 -- uses direct agency_id column
    op.execute(
        "ALTER TABLE agency_subscriptions ENABLE ROW LEVEL SECURITY"
    )
    op.execute(
        "CREATE POLICY agency_subscriptions_agency_isolation "
        "ON agency_subscriptions "
        "USING ("
        "  current_setting('app.current_agency_id', true) = '0'"
        "  OR agency_id = NULLIF(current_setting('app.current_agency_id', true), '')::int"
        ")"
    )


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS agency_subscriptions_agency_isolation "
        "ON agency_subscriptions"
    )
    op.drop_table("agency_subscriptions")
