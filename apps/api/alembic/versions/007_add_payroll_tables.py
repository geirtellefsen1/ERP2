"""Add employees and payslips tables for SA payroll engine

Revision ID: 007
Revises: 005
Create Date: 2026-04-10

"""
from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Employees table
    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("employee_number", sa.String(50), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("id_number", sa.String(20), nullable=True),
        sa.Column("tax_number", sa.String(20), nullable=True),
        sa.Column("monthly_salary", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=True),
        sa.Column("country", sa.String(10), server_default="ZA", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_employees_agency_id", "employees", ["agency_id"])
    op.create_index("idx_employees_client_id", "employees", ["client_id"])
    op.create_index("idx_employees_is_active", "employees", ["is_active"])

    # Payslips table
    op.create_table(
        "payslips",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("payroll_run_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("gross_salary", sa.Numeric(12, 2), nullable=True),
        sa.Column("paye_tax", sa.Numeric(12, 2), nullable=True),
        sa.Column("uif_employee", sa.Numeric(12, 2), nullable=True),
        sa.Column("sdl", sa.Numeric(12, 2), nullable=True),
        sa.Column("eti", sa.Numeric(12, 2), nullable=True),
        sa.Column("net_salary", sa.Numeric(12, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["payroll_run_id"], ["payroll_runs.id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_payslips_payroll_run_id", "payslips", ["payroll_run_id"])
    op.create_index("idx_payslips_employee_id", "payslips", ["employee_id"])


def downgrade() -> None:
    op.drop_table("payslips")
    op.drop_table("employees")
