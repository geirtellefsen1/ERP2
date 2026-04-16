"""Add inbox_items table

Revision ID: 018_inbox_items
Revises: 017_ai_activity_feed
Create Date: 2026-04-16

The "Innboks" — every receipt, invoice, and bank statement that's been
forwarded by email, uploaded via drag-drop, or sent from the iOS/Android
mobile app lands here as an inbox_item.

The AI extracts vendor / date / amount / VAT / suggested_account and
queues the item for the accountant (or the client) to approve. On
approval, a Transaction row is created and the inbox_item is marked
"approved" with a reference back.
"""
from alembic import op
import sqlalchemy as sa


revision = "018_inbox_items"
down_revision = "017_ai_activity_feed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inbox_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column(
            "source", sa.String(20), nullable=False, server_default="upload"
        ),  # upload | email | mobile | ehf
        sa.Column("source_reference", sa.String(255), nullable=True),
        sa.Column("original_filename", sa.String(255), nullable=True),
        sa.Column("storage_uri", sa.String(500), nullable=True),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="pending"
        ),  # pending | extracted | approved | rejected
        # AI extraction outputs
        sa.Column("extracted_vendor", sa.String(255), nullable=True),
        sa.Column("extracted_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extracted_amount_minor", sa.BigInteger(), nullable=True),
        sa.Column("extracted_vat_minor", sa.BigInteger(), nullable=True),
        sa.Column("extracted_currency", sa.String(3), nullable=True),
        sa.Column("extracted_invoice_number", sa.String(100), nullable=True),
        sa.Column("suggested_account_id", sa.Integer(), nullable=True),
        sa.Column("suggested_outlet_type", sa.String(30), nullable=True),
        sa.Column("ai_confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("ai_reasoning", sa.Text(), nullable=True),
        # Linkage after approval
        sa.Column("transaction_id", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["suggested_account_id"], ["accounts.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["transaction_id"], ["transactions.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inbox_items_agency_status", "inbox_items", ["agency_id", "status"])
    op.create_index("ix_inbox_items_client_id", "inbox_items", ["client_id"])
    op.create_index("ix_inbox_items_created_at", "inbox_items", ["created_at"])

    op.execute('ALTER TABLE "inbox_items" ENABLE ROW LEVEL SECURITY')
    op.execute(
        """
        CREATE POLICY tenant_isolation ON "inbox_items"
        USING (
            current_setting('app.current_agency_id', true) = '0'
            OR agency_id = NULLIF(current_setting('app.current_agency_id', true), '')::int
        )
        """
    )


def downgrade() -> None:
    op.execute('DROP POLICY IF EXISTS tenant_isolation ON "inbox_items"')
    op.execute('ALTER TABLE "inbox_items" DISABLE ROW LEVEL SECURITY')
    op.drop_table("inbox_items")
