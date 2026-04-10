"""Initial schema — agencies, clients, users, contacts, invoices, transactions, payroll

Revision ID: 001_initial
Revises:
Create Date: 2026-04-10

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── Agencies ───────────────────────────────────────────
    op.create_table(
        'agencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('subscription_tier', sa.String(50), server_default='starter'),
        sa.Column('countries_enabled', sa.String(255), server_default='ZA,NO,UK'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agencies_slug', 'agencies', ['slug'], unique=True)
    op.create_index('ix_agencies_id', 'agencies', ['id'])

    # ─── Users ─────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agency_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('role', sa.String(50), server_default='agent'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['agency_id'], ['agencies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_agency_id', 'users', ['agency_id'])

    # ─── Clients ───────────────────────────────────────────
    op.create_table(
        'clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agency_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('registration_number', sa.String(100)),
        sa.Column('country', sa.String(3)),
        sa.Column('industry', sa.String(100)),
        sa.Column('fiscal_year_end', sa.String(10)),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['agency_id'], ['agencies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_clients_agency_id', 'clients', ['agency_id'])
    op.create_index('ix_clients_country', 'clients', ['country'])

    # ─── Client Contacts ───────────────────────────────────
    op.create_table(
        'client_contacts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('role', sa.String(100)),
        sa.Column('is_primary', sa.Boolean(), server_default='false'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_client_contacts_client_id', 'client_contacts', ['client_id'])

    # ─── Invoices ──────────────────────────────────────────
    op.create_table(
        'invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('invoice_number', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), server_default='draft'),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(3), server_default='ZAR'),
        sa.Column('due_date', sa.DateTime(timezone=True)),
        sa.Column('issued_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_invoices_invoice_number', 'invoices', ['invoice_number'], unique=True)
    op.create_index('ix_invoices_client_id', 'invoices', ['client_id'])
    op.create_index('ix_invoices_status', 'invoices', ['status'])

    # ─── Invoice Line Items ────────────────────────────────
    op.create_table(
        'invoice_line_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('quantity', sa.Numeric(10, 2), server_default='1'),
        sa.Column('unit_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('total', sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_invoice_line_items_invoice_id', 'invoice_line_items', ['invoice_id'])

    # ─── Transactions ──────────────────────────────────────
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('reference', sa.String(255)),
        sa.Column('matched', sa.Boolean(), server_default='false'),
        sa.Column('matched_invoice_id', sa.Integer()),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['matched_invoice_id'], ['invoices.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_transactions_client_id', 'transactions', ['client_id'])
    op.create_index('ix_transactions_date', 'transactions', ['date'])
    op.create_index('ix_transactions_matched', 'transactions', ['matched'])

    # ─── Payroll Runs ─────────────────────────────────────
    op.create_table(
        'payroll_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(50), server_default='draft'),
        sa.Column('total_gross', sa.Numeric(12, 2), server_default='0'),
        sa.Column('total_paye', sa.Numeric(12, 2), server_default='0'),
        sa.Column('total_uif', sa.Numeric(12, 2), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_payroll_runs_client_id', 'payroll_runs', ['client_id'])
    op.create_index('ix_payroll_runs_status', 'payroll_runs', ['status'])


def downgrade() -> None:
    op.drop_table('payroll_runs')
    op.drop_table('transactions')
    op.drop_table('invoice_line_items')
    op.drop_table('invoices')
    op.drop_table('client_contacts')
    op.drop_table('clients')
    op.drop_table('users')
    op.drop_table('agencies')
