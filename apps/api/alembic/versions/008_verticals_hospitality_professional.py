"""008: Hospitality + Professional Services verticals

Revision ID: 008_verticals
Revises: 007_cashflow_and_reports
Create Date: 2026-04-13

Adds the persistent storage for Tier 4 vertical modules.

Hospitality:
- properties: hotels/venues owned by a client
- room_categories: room types with base rate per property
- outlets: revenue centers (restaurant, bar, spa, ...) per property
- daily_revenue_imports: one row per property per day, PMS-sourced
- daily_revenue_lines: per-outlet-type revenue for each import

Professional Services:
- matters: billable units of client work
- fee_earners: billable staff
- billing_rates: rate matrix (grade, matter type, client override)
- wip_entries: 6-minute increment time entries

All tables get RLS policies that scope through clients.agency_id so
nothing leaks cross-tenant.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "008_verticals"
down_revision: Union[str, None] = "007_cashflow_and_reports"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Hospitality: properties ─────────────────────────────────────
    op.create_table(
        "properties",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("country", sa.String(3), nullable=False),
        sa.Column("total_rooms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("opening_date", sa.Date(), nullable=True),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="Europe/Oslo"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_properties_client_id", "properties", ["client_id"])

    # ── Hospitality: room categories ───────────────────────────────
    op.create_table(
        "room_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("room_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("base_rate_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("property_id", "code", name="uq_room_categories_property_code"),
    )
    op.create_index("ix_room_categories_property_id", "room_categories", ["property_id"])

    # ── Hospitality: outlets ───────────────────────────────────────
    op.create_table(
        "outlets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("outlet_type", sa.String(30), nullable=False),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_outlets_property_id", "outlets", ["property_id"])
    op.create_index("ix_outlets_outlet_type", "outlets", ["outlet_type"])

    # ── Hospitality: daily revenue imports + lines ─────────────────
    op.create_table(
        "daily_revenue_imports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("import_date", sa.Date(), nullable=False),
        sa.Column("rooms_sold", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rooms_available", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("pms_name", sa.String(50)),
        sa.Column("raw_reference", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("property_id", "import_date", name="uq_daily_revenue_property_date"),
    )
    op.create_index("ix_daily_revenue_imports_property_id", "daily_revenue_imports", ["property_id"])
    op.create_index("ix_daily_revenue_imports_date", "daily_revenue_imports", ["import_date"])

    op.create_table(
        "daily_revenue_lines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("import_id", sa.Integer(), nullable=False),
        sa.Column("outlet_type", sa.String(30), nullable=False),
        sa.Column("gross_amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("cover_count", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["import_id"], ["daily_revenue_imports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_daily_revenue_lines_import_id", "daily_revenue_lines", ["import_id"])

    # ── Professional services: matters ─────────────────────────────
    op.create_table(
        "matters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("matter_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("opened_on", sa.Date(), nullable=False),
        sa.Column("closed_on", sa.Date(), nullable=True),
        sa.Column("partner_in_charge", sa.Integer(), nullable=True),
        sa.Column("billing_contact", sa.String(255)),
        sa.Column("fixed_fee_minor", sa.BigInteger(), nullable=True),
        sa.Column("retainer_balance_minor", sa.BigInteger(), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("client_id", "code", name="uq_matters_client_code"),
    )
    op.create_index("ix_matters_client_id", "matters", ["client_id"])
    op.create_index("ix_matters_status", "matters", ["status"])

    # ── Professional services: fee earners ─────────────────────────
    op.create_table(
        "fee_earners",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("grade", sa.String(20), nullable=False),
        sa.Column("default_hourly_rate_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fee_earners_client_id", "fee_earners", ["client_id"])
    op.create_index("ix_fee_earners_grade", "fee_earners", ["grade"])

    # ── Professional services: billing rates ───────────────────────
    op.create_table(
        "billing_rates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("matter_id", sa.Integer(), nullable=True),
        sa.Column("grade", sa.String(20), nullable=True),
        sa.Column("matter_type", sa.String(30), nullable=True),
        sa.Column("hourly_rate_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_billing_rates_client_id", "billing_rates", ["client_id"])
    op.create_index("ix_billing_rates_matter_id", "billing_rates", ["matter_id"])

    # ── Professional services: wip entries ─────────────────────────
    op.create_table(
        "wip_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("matter_id", sa.Integer(), nullable=False),
        sa.Column("fee_earner_id", sa.Integer(), nullable=False),
        sa.Column("worked_on", sa.Date(), nullable=False),
        sa.Column("hours", sa.Numeric(6, 2), nullable=False),
        sa.Column("hourly_rate_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="unbilled"),
        sa.Column("logged_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("billed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("written_off_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fee_earner_id"], ["fee_earners.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_wip_entries_matter_id", "wip_entries", ["matter_id"])
    op.create_index("ix_wip_entries_fee_earner_id", "wip_entries", ["fee_earner_id"])
    op.create_index("ix_wip_entries_status", "wip_entries", ["status"])
    op.create_index("ix_wip_entries_worked_on", "wip_entries", ["worked_on"])

    # ── RLS policies ─────────────────────────────────────────────────
    # Tables scoped directly by client_id
    client_scoped = [
        "properties",
        "matters",
        "fee_earners",
    ]
    for table in client_scoped:
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

    # billing_rates has BOTH client_id AND matter_id — filter via either
    op.execute('ALTER TABLE "billing_rates" ENABLE ROW LEVEL SECURITY')
    op.execute(
        """
        CREATE POLICY tenant_isolation ON "billing_rates"
        USING (
            current_setting('app.current_agency_id', true) = '0'
            OR (
                client_id IS NULL
                OR client_id IN (
                    SELECT id FROM clients
                    WHERE agency_id = NULLIF(current_setting('app.current_agency_id', true), '')::int
                )
            )
        )
        """
    )

    # Tables scoped through properties → clients
    property_scoped = [
        "room_categories",
        "outlets",
        "daily_revenue_imports",
    ]
    for table in property_scoped:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON "{table}"
            USING (
                current_setting('app.current_agency_id', true) = '0'
                OR property_id IN (
                    SELECT p.id FROM properties p
                    JOIN clients c ON c.id = p.client_id
                    WHERE c.agency_id = NULLIF(current_setting('app.current_agency_id', true), '')::int
                )
            )
            """
        )

    # Tables scoped through parent → matter → client or import → property → client
    op.execute('ALTER TABLE "wip_entries" ENABLE ROW LEVEL SECURITY')
    op.execute(
        """
        CREATE POLICY tenant_isolation ON "wip_entries"
        USING (
            current_setting('app.current_agency_id', true) = '0'
            OR matter_id IN (
                SELECT m.id FROM matters m
                JOIN clients c ON c.id = m.client_id
                WHERE c.agency_id = NULLIF(current_setting('app.current_agency_id', true), '')::int
            )
        )
        """
    )
    op.execute('ALTER TABLE "daily_revenue_lines" ENABLE ROW LEVEL SECURITY')
    op.execute(
        """
        CREATE POLICY tenant_isolation ON "daily_revenue_lines"
        USING (
            current_setting('app.current_agency_id', true) = '0'
            OR import_id IN (
                SELECT dri.id FROM daily_revenue_imports dri
                JOIN properties p ON p.id = dri.property_id
                JOIN clients c ON c.id = p.client_id
                WHERE c.agency_id = NULLIF(current_setting('app.current_agency_id', true), '')::int
            )
        )
        """
    )


def downgrade() -> None:
    for table in (
        "wip_entries",
        "billing_rates",
        "fee_earners",
        "matters",
        "daily_revenue_lines",
        "daily_revenue_imports",
        "outlets",
        "room_categories",
        "properties",
    ):
        op.execute(f'DROP POLICY IF EXISTS tenant_isolation ON "{table}"')
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY')
    op.drop_table("wip_entries")
    op.drop_table("billing_rates")
    op.drop_table("fee_earners")
    op.drop_table("matters")
    op.drop_table("daily_revenue_lines")
    op.drop_table("daily_revenue_imports")
    op.drop_table("outlets")
    op.drop_table("room_categories")
    op.drop_table("properties")
