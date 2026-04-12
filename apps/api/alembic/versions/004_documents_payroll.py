"""004: Documents + SA Payroll — documents, document_intelligence, employees, payroll_periods, payslips

Revision ID: 004_documents_payroll
Revises: 003_bank_reconciliation
Create Date: 2026-04-12

These tables exist in app/models.py but were never added to migrations:
- documents              (Sprint 9)
- document_intelligence  (Sprint 10)
- employees              (Sprint 14)
- payroll_periods        (Sprint 14)
- payslips               (Sprint 14)

The payroll_runs table is already created in 001_initial.py.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '004_documents_payroll'
down_revision: Union[str, None] = '003_bank_reconciliation'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Documents (Sprint 9) ────────────────────────────────────────────────
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100)),
        sa.Column('file_path', sa.String(500)),
        sa.Column('file_size', sa.Integer()),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('uploaded_by', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_documents_client_id', 'documents', ['client_id'])
    op.create_index('ix_documents_category', 'documents', ['category'])

    # ── Document Intelligence (Sprint 10) ───────────────────────────────────
    op.create_table(
        'document_intelligence',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('extraction_model', sa.String(50)),
        sa.Column('raw_text', sa.Text()),
        sa.Column('extracted_data', sa.Text()),
        sa.Column('confidence_score', sa.Numeric(5, 4)),
        sa.Column('is_fraud_flagged', sa.Boolean(), server_default='false'),
        sa.Column('fraud_reasons', sa.Text()),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('processed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_document_intelligence_document_id', 'document_intelligence', ['document_id'])
    op.create_index('ix_document_intelligence_status', 'document_intelligence', ['status'])

    # ── Employees (Sprint 14: SA Payroll) ───────────────────────────────────
    op.create_table(
        'employees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('employee_number', sa.String(50)),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('id_number', sa.String(13)),
        sa.Column('tax_number', sa.String(10)),
        sa.Column('uif_number', sa.String(10)),
        sa.Column('employment_type', sa.String(20), server_default='permanent'),
        sa.Column('department', sa.String(100)),
        sa.Column('position', sa.String(100)),
        sa.Column('join_date', sa.DateTime(timezone=True)),
        sa.Column('leave_date', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_number', name='uq_employees_employee_number'),
    )
    op.create_index('ix_employees_client_id', 'employees', ['client_id'])
    op.create_index('ix_employees_is_active', 'employees', ['is_active'])

    # ── Payroll Periods (Sprint 14) ─────────────────────────────────────────
    op.create_table(
        'payroll_periods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(20), server_default='open'),
        sa.Column('pay_date', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_payroll_periods_client_id', 'payroll_periods', ['client_id'])
    op.create_index('ix_payroll_periods_year_month', 'payroll_periods', ['year', 'month'])

    # ── Payslips (Sprint 14) ────────────────────────────────────────────────
    op.create_table(
        'payslips',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('payroll_run_id', sa.Integer(), nullable=False),
        sa.Column('period_id', sa.Integer(), nullable=False),
        # Earnings
        sa.Column('gross_salary', sa.Numeric(12, 2), nullable=False),
        sa.Column('total_earnings', sa.Numeric(12, 2), nullable=False),
        # Deductions
        sa.Column('paye', sa.Numeric(12, 2), server_default='0'),
        sa.Column('uif_employee', sa.Numeric(12, 2), server_default='0'),
        sa.Column('uif_employer', sa.Numeric(12, 2), server_default='0'),
        sa.Column('sdl', sa.Numeric(12, 2), server_default='0'),
        sa.Column('pension', sa.Numeric(12, 2), server_default='0'),
        sa.Column('medical_aid', sa.Numeric(12, 2), server_default='0'),
        sa.Column('other_deductions', sa.Numeric(12, 2), server_default='0'),
        # Net
        sa.Column('total_deductions', sa.Numeric(12, 2), nullable=False),
        sa.Column('net_salary', sa.Numeric(12, 2), nullable=False),
        # ETI
        sa.Column('eti_amount', sa.Numeric(12, 2), server_default='0'),
        sa.Column('status', sa.String(20), server_default='draft'),
        sa.Column('paid_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['payroll_run_id'], ['payroll_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['period_id'], ['payroll_periods.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_payslips_employee_id', 'payslips', ['employee_id'])
    op.create_index('ix_payslips_payroll_run_id', 'payslips', ['payroll_run_id'])
    op.create_index('ix_payslips_period_id', 'payslips', ['period_id'])


def downgrade() -> None:
    op.drop_table('payslips')
    op.drop_table('payroll_periods')
    op.drop_table('employees')
    op.drop_table('document_intelligence')
    op.drop_table('documents')
