"""005: Jurisdiction configs, audit log, and currency columns

Revision ID: 005_jurisdictions_audit_currency
Revises: 004_documents_payroll
Create Date: 2026-04-12

Adds the architectural tables and columns the spec requires for the Nordic
build:

- `jurisdiction_configs` — per-client-company configuration that selects
  which jurisdiction module applies (NO / SE / FI) and stores client-level
  overrides (custom VAT rates, preferred filing frequency, reporting
  currency). One row per client.

- `audit_log` — immutable append-only log of significant state changes
  (reads, writes, exports). Used for SOC2 readiness, GDPR compliance, and
  post-mortem investigation.

- Currency columns on every financial table that represents a monetary
  amount — invoices, journal entries, bank transactions, accounts
  (reporting currency), payslips. Defaults to the client's jurisdiction
  currency via triggers at the application layer (not enforced at DB
  level to keep the migration reversible).

This migration is additive only: no existing columns are dropped or
renamed, and existing rows get sensible defaults so seed data and live
data both continue to work.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "005_jurisdictions_audit_currency"
down_revision: Union[str, None] = "004_documents_payroll"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── jurisdiction_configs ─────────────────────────────────────────
    op.create_table(
        "jurisdiction_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column(
            "primary_jurisdiction",
            sa.String(3),
            nullable=False,
            comment="ISO country code — NO / SE / FI",
        ),
        sa.Column(
            "secondary_jurisdictions",
            sa.String(255),
            nullable=True,
            comment="Comma-separated list for multi-country clients",
        ),
        sa.Column(
            "reporting_currency",
            sa.String(3),
            nullable=False,
            server_default="NOK",
            comment="ISO 4217 — used for consolidated reporting",
        ),
        sa.Column(
            "vat_filing_frequency",
            sa.String(20),
            nullable=True,
            comment="Override for the jurisdiction default (monthly/bimonthly/quarterly/annual)",
        ),
        sa.Column(
            "fiscal_year_start_month",
            sa.Integer(),
            nullable=False,
            server_default="1",
            comment="1 = January, 4 = April, etc.",
        ),
        sa.Column(
            "language",
            sa.String(10),
            nullable=False,
            server_default="en",
            comment="IETF language tag for client-facing documents",
        ),
        sa.Column(
            "config_overrides",
            sa.Text(),
            nullable=True,
            comment="JSON blob of client-specific overrides (VAT rate exceptions, etc.)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            onupdate=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("client_id", name="uq_jurisdiction_configs_client"),
    )
    op.create_index(
        "ix_jurisdiction_configs_client_id", "jurisdiction_configs", ["client_id"]
    )
    op.create_index(
        "ix_jurisdiction_configs_primary",
        "jurisdiction_configs",
        ["primary_jurisdiction"],
    )

    # ── audit_log ────────────────────────────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column(
            "agency_id",
            sa.Integer(),
            nullable=True,
            comment="Tenant scope — NULL for system events",
        ),
        sa.Column(
            "client_id",
            sa.Integer(),
            nullable=True,
            comment="Client scope, if the event is client-scoped",
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=True,
            comment="Actor — NULL for system/automated events",
        ),
        sa.Column(
            "action",
            sa.String(50),
            nullable=False,
            comment="e.g. 'create', 'update', 'delete', 'read', 'export', 'login'",
        ),
        sa.Column(
            "entity_type",
            sa.String(50),
            nullable=True,
            comment="Table name or resource type affected",
        ),
        sa.Column(
            "entity_id",
            sa.String(50),
            nullable=True,
            comment="Primary key of the affected row (string to allow UUIDs)",
        ),
        sa.Column(
            "diff",
            sa.Text(),
            nullable=True,
            comment="JSON patch of changes (RFC 6902), NULL for read events",
        ),
        sa.Column(
            "ip_address",
            sa.String(45),
            nullable=True,
            comment="Client IP, IPv4 or IPv6",
        ),
        sa.Column(
            "user_agent",
            sa.String(500),
            nullable=True,
        ),
        sa.Column(
            "request_id",
            sa.String(64),
            nullable=True,
            comment="Correlation ID for cross-service tracing",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["agency_id"], ["agencies.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["client_id"], ["clients.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_log_agency_id", "audit_log", ["agency_id"])
    op.create_index("ix_audit_log_client_id", "audit_log", ["client_id"])
    op.create_index("ix_audit_log_user_id", "audit_log", ["user_id"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])
    op.create_index(
        "ix_audit_log_entity",
        "audit_log",
        ["entity_type", "entity_id"],
    )

    # ── Currency columns on existing financial tables ──────────────
    # Add `currency` where the model doesn't already carry it. Server default
    # of NOK is deliberately broad — individual clients' actual currencies
    # will be populated from their JurisdictionConfig.reporting_currency
    # when they're migrated.
    with op.batch_alter_table("invoices") as batch:
        # invoices already has a currency column from 001_initial, do nothing.
        pass

    with op.batch_alter_table("journal_entries") as batch:
        batch.add_column(
            sa.Column(
                "currency",
                sa.String(3),
                nullable=False,
                server_default="NOK",
            )
        )
        batch.add_column(
            sa.Column(
                "fx_rate_to_reporting",
                sa.Numeric(18, 8),
                nullable=True,
                comment="FX rate to client reporting currency on entry_date",
            )
        )

    with op.batch_alter_table("journal_lines") as batch:
        batch.add_column(
            sa.Column(
                "currency",
                sa.String(3),
                nullable=False,
                server_default="NOK",
            )
        )

    with op.batch_alter_table("bank_accounts") as batch:
        # bank_accounts already has a currency column from 003, do nothing.
        pass

    with op.batch_alter_table("payslips") as batch:
        batch.add_column(
            sa.Column(
                "currency",
                sa.String(3),
                nullable=False,
                server_default="NOK",
            )
        )

    with op.batch_alter_table("accounts") as batch:
        # Control accounts and reporting currency per GL account
        batch.add_column(
            sa.Column(
                "reporting_currency",
                sa.String(3),
                nullable=True,
                comment="If set, amounts in this account are reported in this currency",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("accounts") as batch:
        batch.drop_column("reporting_currency")

    with op.batch_alter_table("payslips") as batch:
        batch.drop_column("currency")

    with op.batch_alter_table("journal_lines") as batch:
        batch.drop_column("currency")

    with op.batch_alter_table("journal_entries") as batch:
        batch.drop_column("fx_rate_to_reporting")
        batch.drop_column("currency")

    op.drop_index("ix_audit_log_entity", table_name="audit_log")
    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_index("ix_audit_log_user_id", table_name="audit_log")
    op.drop_index("ix_audit_log_client_id", table_name="audit_log")
    op.drop_index("ix_audit_log_agency_id", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index(
        "ix_jurisdiction_configs_primary", table_name="jurisdiction_configs"
    )
    op.drop_index(
        "ix_jurisdiction_configs_client_id", table_name="jurisdiction_configs"
    )
    op.drop_table("jurisdiction_configs")
