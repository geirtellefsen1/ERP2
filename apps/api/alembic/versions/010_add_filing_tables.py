"""Add filing_records and filing_deadlines tables

Revision ID: 010
Revises: 006
Create Date: 2026-04-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision = "010"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Filing records table
    op.create_table(
        "filing_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("jurisdiction", sa.String(10), nullable=False),
        sa.Column("filing_type", sa.String(50), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), server_default="draft", nullable=True),
        sa.Column("submission_id", sa.String(100), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_data", JSON, nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_filing_records_client_id", "filing_records", ["client_id"])
    op.create_index("idx_filing_records_status", "filing_records", ["status"])
    op.create_index("idx_filing_records_jurisdiction", "filing_records", ["jurisdiction"])

    # Filing deadlines table
    op.create_table(
        "filing_deadlines",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("jurisdiction", sa.String(10), nullable=False),
        sa.Column("filing_type", sa.String(50), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("frequency", sa.String(20), nullable=True),
        sa.Column("reminder_days_before", sa.Integer(), server_default="7", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_filing_deadlines_client_id", "filing_deadlines", ["client_id"])
    op.create_index("idx_filing_deadlines_due_date", "filing_deadlines", ["due_date"])


def downgrade() -> None:
    op.drop_table("filing_deadlines")
    op.drop_table("filing_records")
