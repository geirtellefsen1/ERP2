"""Add journal entries, journal entry lines, and posting periods tables

Revision ID: 003
Revises: 002
Create Date: 2026-04-10

"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Posting periods table
    op.create_table(
        "posting_periods",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("period_name", sa.String(100), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), server_default="open", nullable=False),
        sa.Column("is_locked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_posting_periods_agency_id", "posting_periods", ["agency_id"])
    op.create_index("idx_posting_periods_client_id", "posting_periods", ["client_id"])

    # Journal entries table
    op.create_table(
        "journal_entries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("posting_period_id", sa.Integer(), nullable=False),
        sa.Column("entry_number", sa.String(50), unique=True, nullable=False),
        sa.Column("entry_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("debit_total", sa.Numeric(19, 2), server_default="0", nullable=False),
        sa.Column("credit_total", sa.Numeric(19, 2), server_default="0", nullable=False),
        sa.Column("status", sa.String(20), server_default="draft", nullable=False),
        sa.Column("is_balanced", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("reversed_by", sa.Integer(), nullable=True),
        sa.Column("ai_validation_notes", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["posting_period_id"], ["posting_periods.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_journal_entries_agency_id", "journal_entries", ["agency_id"])
    op.create_index("idx_journal_entries_client_id", "journal_entries", ["client_id"])
    op.create_index("idx_journal_entries_entry_number", "journal_entries", ["entry_number"])
    op.create_index("idx_journal_entries_status", "journal_entries", ["status"])

    # Journal entry lines table
    op.create_table(
        "journal_entry_lines",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("entry_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("debit_amount", sa.Numeric(19, 2), server_default="0", nullable=False),
        sa.Column("credit_amount", sa.Numeric(19, 2), server_default="0", nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["entry_id"], ["journal_entries.id"]),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_journal_entry_lines_entry_id", "journal_entry_lines", ["entry_id"])
    op.create_index("idx_journal_entry_lines_account_id", "journal_entry_lines", ["account_id"])


def downgrade() -> None:
    op.drop_table("journal_entry_lines")
    op.drop_table("journal_entries")
    op.drop_table("posting_periods")
