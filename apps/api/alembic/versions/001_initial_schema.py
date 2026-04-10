"""Initial schema: agencies, users, clients, accounts, transactions, documents, invoices, payroll

Revision ID: 001
Revises:
Create Date: 2025-04-10

"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- agencies ---
    op.create_table(
        "agencies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("subscription_tier", sa.String(50), server_default="starter"),
        sa.Column("countries_enabled", sa.String(255), server_default="ZA,NO,UK"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("idx_agencies_slug", "agencies", ["slug"])

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("auth0_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("auth0_id"),
    )
    op.create_index("idx_users_agency_id", "users", ["agency_id"])
    op.create_index("idx_users_auth0_id", "users", ["auth0_id"])

    # --- clients ---
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("registration_number", sa.String(100), nullable=True),
        sa.Column("country", sa.String(3), nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("fiscal_year_end", sa.String(10), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("health_score", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_clients_agency_id", "clients", ["agency_id"])

    # --- client_contacts ---
    op.create_table(
        "client_contacts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("role", sa.String(100), nullable=True),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- accounts (Chart of Accounts) ---
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("account_number", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("account_type", sa.String(50), nullable=False),
        sa.Column("parent_account_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.String(10), server_default="active"),
        sa.Column("balance", sa.Numeric(19, 2), server_default="0"),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["parent_account_id"], ["accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_accounts_agency_id", "accounts", ["agency_id"])
    op.create_index("idx_accounts_client_id", "accounts", ["client_id"])
    op.create_index("idx_accounts_account_number", "accounts", ["account_number"])

    # --- invoices ---
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("invoice_number", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), server_default="ZAR"),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invoice_number"),
    )
    op.create_index("idx_invoices_client_id", "invoices", ["client_id"])
    op.create_index("idx_invoices_status", "invoices", ["status"])

    # --- invoice_line_items ---
    op.create_table(
        "invoice_line_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Numeric(10, 2), server_default="1"),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- transactions ---
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=True),
        sa.Column("transaction_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("amount", sa.Numeric(19, 2), nullable=False),
        sa.Column("debit_amount", sa.Numeric(19, 2), server_default="0"),
        sa.Column("credit_amount", sa.Numeric(19, 2), server_default="0"),
        sa.Column("reference", sa.String(255), nullable=True),
        sa.Column("transaction_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), server_default="posted"),
        sa.Column("matched", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("matched_invoice_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["matched_invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_transactions_agency_id", "transactions", ["agency_id"])
    op.create_index("idx_transactions_client_id", "transactions", ["client_id"])
    op.create_index("idx_transactions_account_id", "transactions", ["account_id"])
    op.create_index("idx_transactions_date", "transactions", ["transaction_date"])

    # --- documents ---
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_url", sa.String(500), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("extraction_confidence", sa.Integer(), nullable=True),
        sa.Column("extracted_data", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_documents_agency_id", "documents", ["agency_id"])
    op.create_index("idx_documents_client_id", "documents", ["client_id"])
    op.create_index("idx_documents_status", "documents", ["status"])

    # --- payroll_runs ---
    op.create_table(
        "payroll_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("total_gross", sa.Numeric(12, 2), server_default="0"),
        sa.Column("total_paye", sa.Numeric(12, 2), server_default="0"),
        sa.Column("total_uif", sa.Numeric(12, 2), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_payroll_runs_client_id", "payroll_runs", ["client_id"])
    op.create_index("idx_payroll_runs_status", "payroll_runs", ["status"])

    # --- Row-Level Security policies ---
    # Enable RLS on multi-tenant tables
    for table in ["users", "clients", "accounts", "transactions", "documents"]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")

    # Create RLS policies (enforced when app connects as non-superuser)
    op.execute("""
        CREATE POLICY agency_isolation_users ON users
        USING (agency_id = current_setting('app.current_agency_id', true)::int)
    """)
    op.execute("""
        CREATE POLICY agency_isolation_clients ON clients
        USING (agency_id = current_setting('app.current_agency_id', true)::int)
    """)
    op.execute("""
        CREATE POLICY agency_isolation_accounts ON accounts
        USING (agency_id = current_setting('app.current_agency_id', true)::int)
    """)
    op.execute("""
        CREATE POLICY agency_isolation_transactions ON transactions
        USING (agency_id = current_setting('app.current_agency_id', true)::int)
    """)
    op.execute("""
        CREATE POLICY agency_isolation_documents ON documents
        USING (agency_id = current_setting('app.current_agency_id', true)::int)
    """)


def downgrade() -> None:
    # Drop RLS policies
    for table in ["documents", "transactions", "accounts", "clients", "users"]:
        op.execute(f"DROP POLICY IF EXISTS agency_isolation_{table} ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    # Drop tables in reverse dependency order
    op.drop_table("payroll_runs")
    op.drop_table("documents")
    op.drop_table("transactions")
    op.drop_table("invoice_line_items")
    op.drop_table("invoices")
    op.drop_table("accounts")
    op.drop_table("client_contacts")
    op.drop_table("clients")
    op.drop_table("users")
    op.drop_table("agencies")
