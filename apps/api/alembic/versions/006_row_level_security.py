"""006: Row-Level Security on tenant-scoped tables

Revision ID: 006_row_level_security
Revises: 005_jurisdictions_audit_currency
Create Date: 2026-04-12

Enables Postgres Row-Level Security (RLS) on every table that carries an
agency_id or is reachable from an agency_id. Each table gets a policy that
filters rows by `app.current_agency_id`, a session-local GUC set by the
auth middleware before every request.

Design decisions:

1. FAIL-SAFE DEFAULT. If `app.current_agency_id` is not set, the policy
   returns zero rows. Forgetting to set the variable can never leak cross-
   tenant data — it just breaks the feature loudly.

2. ADMIN BYPASS. If the variable is set to 0, the policy allows all rows.
   Used by background jobs, migrations, and the seed script. Requires
   explicit intent — you can't accidentally trip it.

3. SUPERUSERS BYPASS RLS ENTIRELY. Postgres gives any SUPERUSER role
   automatic BYPASSRLS, which means the existing test connection (which
   uses a superuser) does not see RLS filtering at all. This is correct:
   tests running as superuser can set up fixtures freely, and a dedicated
   test connects as a non-superuser role to prove RLS actually works.

4. DEFENSE IN DEPTH. API-level agency_id filters remain in the routers.
   RLS is a second fence — if a router forgets its filter (several already
   did before this sprint), the database still refuses to return the row.

Tables protected:
- clients, users, client_contacts (direct agency_id or via client)
- accounts, journal_entries, journal_lines, invoices, invoice_line_items
- transactions, bank_accounts, bank_transactions
- employees, payroll_periods, payroll_runs, payslips
- documents, document_intelligence
- jurisdiction_configs
- audit_log

The agency table itself is NOT protected — everyone can see the list of
agencies, but only one's own rows inside them.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "006_row_level_security"
down_revision: Union[str, None] = "005_jurisdictions_audit_currency"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables with a direct agency_id column. Get a straightforward policy.
DIRECT_AGENCY_TABLES = [
    "clients",
    "users",
    "audit_log",
]

# Tables scoped by client_id — the policy joins through clients.agency_id.
# We use a subquery rather than a materialized view for simplicity.
CLIENT_SCOPED_TABLES = [
    "client_contacts",
    "accounts",
    "journal_entries",
    "invoices",
    "transactions",
    "bank_accounts",
    "employees",
    "payroll_periods",
    "payroll_runs",
    "documents",
    "jurisdiction_configs",
]

# Tables nested deeper — scope via their parent's client_id.
NESTED_TABLES = {
    "journal_lines": "SELECT je.client_id FROM journal_entries je WHERE je.id = journal_lines.entry_id",
    "invoice_line_items": "SELECT inv.client_id FROM invoices inv WHERE inv.id = invoice_line_items.invoice_id",
    "bank_transactions": "SELECT ba.client_id FROM bank_accounts ba WHERE ba.id = bank_transactions.account_id",
    "payslips": "SELECT emp.client_id FROM employees emp WHERE emp.id = payslips.employee_id",
    "document_intelligence": "SELECT doc.client_id FROM documents doc WHERE doc.id = document_intelligence.document_id",
}


def _enable_rls_with_direct_agency(table: str) -> None:
    """Table has an agency_id column directly."""
    op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
    op.execute(
        f"""
        CREATE POLICY tenant_isolation ON "{table}"
        USING (
            current_setting('app.current_agency_id', true) = '0'
            OR agency_id = NULLIF(current_setting('app.current_agency_id', true), '')::int
        )
        """
    )


def _enable_rls_via_client(table: str) -> None:
    """Table has a client_id — join through clients to find agency_id."""
    op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
    op.execute(
        f"""
        CREATE POLICY tenant_isolation ON "{table}"
        USING (
            current_setting('app.current_agency_id', true) = '0'
            OR client_id IN (
                SELECT id FROM clients
                WHERE agency_id = NULLIF(current_setting('app.current_agency_id', true), '')::int
            )
        )
        """
    )


def _enable_rls_via_nested(table: str, parent_lookup_sql: str) -> None:
    """Table is nested two levels deep — scope via the parent lookup SQL."""
    op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
    op.execute(
        f"""
        CREATE POLICY tenant_isolation ON "{table}"
        USING (
            current_setting('app.current_agency_id', true) = '0'
            OR ({parent_lookup_sql}) IN (
                SELECT id FROM clients
                WHERE agency_id = NULLIF(current_setting('app.current_agency_id', true), '')::int
            )
        )
        """
    )


def upgrade() -> None:
    for table in DIRECT_AGENCY_TABLES:
        _enable_rls_with_direct_agency(table)

    for table in CLIENT_SCOPED_TABLES:
        _enable_rls_via_client(table)

    for table, lookup in NESTED_TABLES.items():
        _enable_rls_via_nested(table, lookup)


def downgrade() -> None:
    tables = (
        list(NESTED_TABLES.keys())
        + list(reversed(CLIENT_SCOPED_TABLES))
        + list(reversed(DIRECT_AGENCY_TABLES))
    )
    for table in tables:
        op.execute(f'DROP POLICY IF EXISTS tenant_isolation ON "{table}"')
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY')
