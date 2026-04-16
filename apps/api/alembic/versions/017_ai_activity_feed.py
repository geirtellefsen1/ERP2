"""Add ai_activity_feed table

Revision ID: 017_ai_activity_feed
Revises: 016_mfa_totp
Create Date: 2026-04-16

A single append-only stream of "things the AI did". The hospitality
dashboard (and eventually every vertical) reads this to show "AI did N
things since you last logged in".
"""
from alembic import op
import sqlalchemy as sa


revision = "017_ai_activity_feed"
down_revision = "016_mfa_totp"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_activity_feed",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="info"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("source_kind", sa.String(40), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("requires_review", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_activity_feed_agency_created",
        "ai_activity_feed",
        ["agency_id", "created_at"],
    )
    op.create_index(
        "ix_ai_activity_feed_client_id", "ai_activity_feed", ["client_id"]
    )
    op.create_index(
        "ix_ai_activity_feed_requires_review",
        "ai_activity_feed",
        ["requires_review"],
    )

    op.execute('ALTER TABLE "ai_activity_feed" ENABLE ROW LEVEL SECURITY')
    op.execute(
        """
        CREATE POLICY tenant_isolation ON "ai_activity_feed"
        USING (
            current_setting('app.current_agency_id', true) = '0'
            OR agency_id = NULLIF(current_setting('app.current_agency_id', true), '')::int
        )
        """
    )


def downgrade() -> None:
    op.execute('DROP POLICY IF EXISTS tenant_isolation ON "ai_activity_feed"')
    op.execute('ALTER TABLE "ai_activity_feed" DISABLE ROW LEVEL SECURITY')
    op.drop_table("ai_activity_feed")
