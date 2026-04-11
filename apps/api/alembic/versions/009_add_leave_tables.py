"""Add leave_types, leave_balances, leave_requests, leave_blackout_dates tables

Revision ID: 009
Revises: 006
Create Date: 2026-04-10

"""
from alembic import op
import sqlalchemy as sa

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Leave types table
    op.create_table(
        "leave_types",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("code", sa.String(20), nullable=True),
        sa.Column("is_paid", sa.Boolean(), server_default="true", nullable=True),
        sa.Column("carries_over", sa.Boolean(), server_default="false", nullable=True),
        sa.Column("max_balance", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_leave_types_client_id", "leave_types", ["client_id"])

    # Leave balances table
    op.create_table(
        "leave_balances",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("leave_type_id", sa.Integer(), nullable=False),
        sa.Column("calendar_year", sa.Integer(), nullable=False),
        sa.Column("opening_balance", sa.Numeric(5, 2), server_default="0", nullable=True),
        sa.Column("entitlements", sa.Numeric(5, 2), server_default="21", nullable=True),
        sa.Column("used", sa.Numeric(5, 2), server_default="0", nullable=True),
        sa.Column("closing_balance", sa.Numeric(5, 2), server_default="21", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["leave_type_id"], ["leave_types.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_leave_balances_employee_id", "leave_balances", ["employee_id"])
    op.create_index("idx_leave_balances_leave_type_id", "leave_balances", ["leave_type_id"])

    # Leave requests table
    op.create_table(
        "leave_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("leave_type_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("business_days", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), server_default="draft", nullable=True),
        sa.Column("approver_id", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["leave_type_id"], ["leave_types.id"]),
        sa.ForeignKeyConstraint(["approver_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_leave_requests_employee_id", "leave_requests", ["employee_id"])
    op.create_index("idx_leave_requests_status", "leave_requests", ["status"])

    # Leave blackout dates table
    op.create_table(
        "leave_blackout_dates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_leave_blackout_dates_client_id", "leave_blackout_dates", ["client_id"])


def downgrade() -> None:
    op.drop_table("leave_blackout_dates")
    op.drop_table("leave_requests")
    op.drop_table("leave_balances")
    op.drop_table("leave_types")
