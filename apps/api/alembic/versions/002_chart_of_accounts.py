"""002: Chart of accounts — accounts, journal_entries, journal_lines

Revision ID: 002_chart_of_accounts
Revises: 001_initial
Create Date: 2026-04-10

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_chart_of_accounts'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('account_type', sa.String(20), nullable=False),
        sa.Column('sub_type', sa.String(50)),
        sa.Column('parent_id', sa.Integer()),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('is_control_account', sa.Boolean(), server_default='false'),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['accounts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_accounts_client_id', 'accounts', ['client_id'])
    op.create_index('ix_accounts_code', 'accounts', ['code'])

    op.create_table(
        'journal_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('entry_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('reference', sa.String(100)),
        sa.Column('posted_by', sa.Integer()),
        sa.Column('is_reversal', sa.Boolean(), server_default='false'),
        sa.Column('reversed_id', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['posted_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reversed_id'], ['journal_entries.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_journal_entries_client_id', 'journal_entries', ['client_id'])
    op.create_index('ix_journal_entries_entry_date', 'journal_entries', ['entry_date'])

    op.create_table(
        'journal_lines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entry_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('debit', sa.Numeric(14, 2), server_default='0'),
        sa.Column('credit', sa.Numeric(14, 2), server_default='0'),
        sa.Column('description', sa.Text()),
        sa.ForeignKeyConstraint(['entry_id'], ['journal_entries.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_journal_lines_entry_id', 'journal_lines', ['entry_id'])
    op.create_index('ix_journal_lines_account_id', 'journal_lines', ['account_id'])


def downgrade() -> None:
    op.drop_table('journal_lines')
    op.drop_table('journal_entries')
    op.drop_table('accounts')
