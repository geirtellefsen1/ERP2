"""Add bank_connections and bank_transactions tables

Revision ID: 004
Revises: 003
Create Date: 2026-04-10

"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Bank connections table
    op.create_table(
        "bank_connections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("bank_name", sa.String(255), nullable=False),
        sa.Column("account_number_masked", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), server_default="connected", nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=True),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_bank_connections_agency_id", "bank_connections", ["agency_id"])
    op.create_index("idx_bank_connections_client_id", "bank_connections", ["client_id"])

    # Bank transactions table
    op.create_table(
        "bank_transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("bank_connection_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(255), unique=True, nullable=False),
        sa.Column("transaction_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("amount", sa.Numeric(19, 2), nullable=False),
        sa.Column("currency", sa.String(3), server_default="ZAR", nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("match_status", sa.String(20), server_default="unmatched", nullable=False),
        sa.Column("matched_transaction_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["bank_connection_id"], ["bank_connections.id"]),
        sa.ForeignKeyConstraint(["matched_transaction_id"], ["transactions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_bank_transactions_agency_id", "bank_transactions", ["agency_id"])
    op.create_index("idx_bank_transactions_client_id", "bank_transactions", ["client_id"])
    op.create_index("idx_bank_transactions_connection_id", "bank_transactions", ["bank_connection_id"])
    op.create_index("idx_bank_transactions_match_status", "bank_transactions", ["match_status"])


def downgrade() -> None:
    op.drop_table("bank_transactions")
    op.drop_table("bank_connections")
