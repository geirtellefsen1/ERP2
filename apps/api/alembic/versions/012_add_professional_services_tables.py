"""Add professional services tables: matters, time_entries, billing_rate_matrix,
wip_entries, trust_account_transactions, disbursements

Revision ID: 012
Revises: 008
Create Date: 2026-04-10

"""
from alembic import op
import sqlalchemy as sa

revision = "012"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- matters ---
    op.create_table(
        "matters",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(20), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("matter_type", sa.String(50), nullable=True),
        sa.Column("client_reference", sa.String(100), nullable=True),
        sa.Column("opened_date", sa.Date(), nullable=True),
        sa.Column("closed_date", sa.Date(), nullable=True),
        sa.Column("responsible_fee_earner_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["responsible_fee_earner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_matters_client_id", "matters", ["client_id"])
    op.create_index("idx_matters_code", "matters", ["code"])

    # --- time_entries ---
    op.create_table(
        "time_entries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("matter_id", sa.Integer(), nullable=False),
        sa.Column("fee_earner_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("units", sa.Numeric(5, 2), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("billable", sa.Boolean(), server_default=sa.text("true"), nullable=True),
        sa.Column("billed", sa.Boolean(), server_default=sa.text("false"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"]),
        sa.ForeignKeyConstraint(["fee_earner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_time_entries_matter_id", "time_entries", ["matter_id"])
    op.create_index("idx_time_entries_fee_earner_id", "time_entries", ["fee_earner_id"])
    op.create_index("idx_time_entries_date", "time_entries", ["date"])

    # --- billing_rate_matrix ---
    op.create_table(
        "billing_rate_matrix",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("fee_earner_grade", sa.String(50), nullable=True),
        sa.Column("matter_type", sa.String(50), nullable=True),
        sa.Column("hourly_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_billing_rate_matrix_client_id", "billing_rate_matrix", ["client_id"])

    # --- wip_entries ---
    op.create_table(
        "wip_entries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("matter_id", sa.Integer(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("hours_performed", sa.Numeric(8, 2), server_default="0", nullable=True),
        sa.Column("rate_per_hour", sa.Numeric(10, 2), server_default="0", nullable=True),
        sa.Column("wip_value", sa.Numeric(12, 2), server_default="0", nullable=True),
        sa.Column("invoice_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_wip_entries_matter_id", "wip_entries", ["matter_id"])
    op.create_index("idx_wip_entries_period_end", "wip_entries", ["period_end"])

    # --- trust_account_transactions ---
    op.create_table(
        "trust_account_transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("matter_id", sa.Integer(), nullable=True),
        sa.Column("transaction_type", sa.String(20), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("bank_reference", sa.String(100), nullable=True),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_trust_txn_client_id", "trust_account_transactions", ["client_id"])
    op.create_index("idx_trust_txn_matter_id", "trust_account_transactions", ["matter_id"])

    # --- disbursements ---
    op.create_table(
        "disbursements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("matter_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("to_be_rebilled", sa.Boolean(), server_default=sa.text("true"), nullable=True),
        sa.Column("rebilled_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_disbursements_matter_id", "disbursements", ["matter_id"])


def downgrade() -> None:
    op.drop_table("disbursements")
    op.drop_table("trust_account_transactions")
    op.drop_table("wip_entries")
    op.drop_table("billing_rate_matrix")
    op.drop_table("time_entries")
    op.drop_table("matters")
