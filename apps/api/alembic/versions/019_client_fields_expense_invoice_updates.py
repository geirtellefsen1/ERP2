"""Extend Client with address/contact fields, add Expense model, update Invoice with customer fields

Revision ID: 019_client_fields_expense_invoice_updates
Revises: 018_inbox_items
Create Date: 2026-04-17
"""
from alembic import op
import sqlalchemy as sa

revision = "019_client_fields_expense_invoice_updates"
down_revision = "018_inbox_items"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Client: add address, contact, VAT fields ---
    op.add_column("clients", sa.Column("vat_number", sa.String(50)))
    op.add_column("clients", sa.Column("address", sa.String(500)))
    op.add_column("clients", sa.Column("city", sa.String(100)))
    op.add_column("clients", sa.Column("postal_code", sa.String(20)))
    op.add_column("clients", sa.Column("email", sa.String(255)))
    op.add_column("clients", sa.Column("phone", sa.String(50)))
    op.add_column("clients", sa.Column("default_currency", sa.String(3), server_default="NOK"))

    # --- Invoice: add customer fields, fix currency default ---
    op.add_column("invoices", sa.Column("subtotal", sa.Numeric(12, 2), server_default="0"))
    op.add_column("invoices", sa.Column("vat_amount", sa.Numeric(12, 2), server_default="0"))
    op.add_column("invoices", sa.Column("customer_name", sa.String(255)))
    op.add_column("invoices", sa.Column("customer_email", sa.String(255)))
    op.add_column("invoices", sa.Column("customer_address", sa.String(500)))
    op.add_column("invoices", sa.Column("customer_org_number", sa.String(50)))
    op.add_column("invoices", sa.Column("reference", sa.String(255)))
    op.add_column("invoices", sa.Column("payment_terms_days", sa.Integer(), server_default="30"))
    op.add_column("invoices", sa.Column("notes", sa.Text()))

    op.alter_column("invoices", "currency", server_default="NOK")

    # --- InvoiceLineItem: add vat_rate and vat_amount ---
    op.add_column("invoice_line_items", sa.Column("vat_rate", sa.Numeric(5, 2), server_default="25"))
    op.add_column("invoice_line_items", sa.Column("vat_amount", sa.Numeric(12, 2), server_default="0"))

    # --- Expense table ---
    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("client_id", sa.Integer, sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("vendor_name", sa.String(255), nullable=False),
        sa.Column("vendor_org_number", sa.String(50)),
        sa.Column("description", sa.Text),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True)),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("vat_amount", sa.Numeric(12, 2), server_default="0"),
        sa.Column("vat_rate", sa.Numeric(5, 2), server_default="25"),
        sa.Column("currency", sa.String(3), server_default="NOK"),
        sa.Column("category", sa.String(50)),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("account_id", sa.Integer, sa.ForeignKey("accounts.id"), nullable=True),
        sa.Column("inbox_item_id", sa.Integer, sa.ForeignKey("inbox_items.id"), nullable=True),
        sa.Column("payment_method", sa.String(30)),
        sa.Column("notes", sa.Text),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("approved_by_user_id", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_expenses_client_id", "expenses", ["client_id"])
    op.create_index("ix_expenses_status", "expenses", ["status"])

    # RLS for expenses
    op.execute("""
        ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;
    """)
    op.execute("""
        CREATE POLICY tenant_isolation ON expenses
        USING (client_id IN (
            SELECT id FROM clients
            WHERE agency_id = current_setting('app.current_agency_id', true)::int
        ));
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON expenses;")
    op.drop_table("expenses")

    op.drop_column("invoice_line_items", "vat_amount")
    op.drop_column("invoice_line_items", "vat_rate")

    op.drop_column("invoices", "notes")
    op.drop_column("invoices", "payment_terms_days")
    op.drop_column("invoices", "reference")
    op.drop_column("invoices", "customer_org_number")
    op.drop_column("invoices", "customer_address")
    op.drop_column("invoices", "customer_email")
    op.drop_column("invoices", "customer_name")
    op.drop_column("invoices", "vat_amount")
    op.drop_column("invoices", "subtotal")

    op.drop_column("clients", "default_currency")
    op.drop_column("clients", "phone")
    op.drop_column("clients", "email")
    op.drop_column("clients", "postal_code")
    op.drop_column("clients", "city")
    op.drop_column("clients", "address")
    op.drop_column("clients", "vat_number")
