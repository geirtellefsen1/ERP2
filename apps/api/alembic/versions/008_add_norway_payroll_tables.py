"""Add Norway payroll tables: payroll_runs_no and employee_no_settings

Revision ID: 008
Revises: 005
Create Date: 2026-04-10

"""
from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- payroll_runs_no ---
    op.create_table(
        "payroll_runs_no",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("payroll_run_id", sa.Integer(), nullable=True),
        sa.Column("a_melding_submitted", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("a_melding_id", sa.String(50), nullable=True),
        sa.Column("a_melding_submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("otp_percentage", sa.Numeric(5, 2), server_default="2.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["payroll_run_id"], ["payroll_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payroll_run_id"),
    )
    op.create_index("idx_payroll_runs_no_payroll_run_id", "payroll_runs_no", ["payroll_run_id"])

    # --- employee_no_settings ---
    op.create_table(
        "employee_no_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("otp_member", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("pension_percentage", sa.Numeric(5, 2), server_default="2.0"),
        sa.Column("holiday_pay_type", sa.String(20), server_default="'percentage'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_employee_no_settings_employee_id", "employee_no_settings", ["employee_id"])


def downgrade() -> None:
    op.drop_table("employee_no_settings")
    op.drop_table("payroll_runs_no")
