"""003: Bank Reconciliation — bank_accounts, bank_transactions

Revision ID: 003_bank_reconciliation
Revises: 002_chart_of_accounts
Create Date: 2026-04-11

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_bank_reconciliation'
down_revision: Union[str, None] = '002_chart_of_accounts'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'bank_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('bank_name', sa.String(100)),
        sa.Column('account_number', sa.String(50)),
        sa.Column('account_type', sa.String(20)),
        sa.Column('currency', sa.String(3), server_default='ZAR'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_bank_accounts_client_id', 'bank_accounts', ['client_id'])

    op.create_table(
        'bank_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(255)),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('reference', sa.String(255)),
        sa.Column('category', sa.String(100)),
        sa.Column('status', sa.String(20), server_default='unmatched'),
        sa.Column('matched_invoice_id', sa.Integer()),
        sa.Column('matched_journal_line_id', sa.Integer()),
        sa.Column('match_confidence', sa.Numeric(5, 4)),
        sa.Column('match_reason', sa.Text()),
        sa.Column('imported_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['account_id'], ['bank_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['matched_invoice_id'], ['invoices.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['matched_journal_line_id'], ['journal_lines.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_bank_transactions_account_id', 'bank_transactions', ['account_id'])
    op.create_index('ix_bank_transactions_status', 'bank_transactions', ['status'])
    op.create_index('ix_bank_transactions_date', 'bank_transactions', ['date'])


def downgrade() -> None:
    op.drop_table('bank_transactions')
    op.drop_table('bank_accounts')
