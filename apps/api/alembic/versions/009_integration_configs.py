"""009: Integration configs (encrypted per-agency secrets)

Revision ID: 009_integration_configs
Revises: 008_verticals
Create Date: 2026-04-13

The central table for everything Tier 5 needs to configure:
  - OAuth providers (Google, Microsoft)
  - Aiia / Tink open banking
  - BankID (NO/SE) + Finnish Trust Network
  - DO Spaces file storage
  - Resend email delivery
  - OpenClaw / Twilio WhatsApp
  - Claude API key (per-agency override)
  - Altinn / Skatteverket / OmaVero / Tulorekisteri
  - PMS integrations (Mews, Opera, Apaleo)
  - White-label settings

Each (agency_id, provider, key) triple has ONE row. Values are
encrypted with Fernet before INSERT; decryption happens only inside
service code that needs the plaintext, never in routers.

The `is_secret` flag marks which rows must be masked in API responses
— e.g. Google client_id is public (can be returned), client_secret is
not.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "009_integration_configs"
down_revision: Union[str, None] = "008_verticals"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "integration_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=False),
        sa.Column(
            "provider",
            sa.String(50),
            nullable=False,
            comment="e.g. 'google_oauth', 'aiia', 'bankid_no', 'do_spaces', 'resend', 'altinn', 'mews'",
        ),
        sa.Column(
            "key",
            sa.String(100),
            nullable=False,
            comment="Config key within the provider, e.g. 'client_id', 'client_secret', 'api_key'",
        ),
        sa.Column(
            "value_encrypted",
            sa.Text(),
            nullable=False,
            comment="Fernet-encrypted value — decrypt via services/secrets.py",
        ),
        sa.Column(
            "is_secret",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment="True = never return plaintext in API responses, mask in UI",
        ),
        sa.Column(
            "last_verified_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When 'test connection' was last clicked and succeeded",
        ),
        sa.Column(
            "last_verification_error",
            sa.Text(),
            nullable=True,
            comment="If last verification failed, the error message",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            onupdate=sa.func.now(),
        ),
        sa.Column(
            "updated_by",
            sa.Integer(),
            nullable=True,
            comment="User id who last changed this config",
        ),
        sa.ForeignKeyConstraint(
            ["agency_id"], ["agencies.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "agency_id", "provider", "key",
            name="uq_integration_configs_agency_provider_key",
        ),
    )
    op.create_index(
        "ix_integration_configs_agency_id",
        "integration_configs",
        ["agency_id"],
    )
    op.create_index(
        "ix_integration_configs_provider",
        "integration_configs",
        ["provider"],
    )

    # RLS — scoped by agency_id, same fail-safe pattern as the other
    # tenant tables. Admin bypass (current_setting = '0') still works
    # for migrations and background jobs.
    op.execute(
        'ALTER TABLE "integration_configs" ENABLE ROW LEVEL SECURITY'
    )
    op.execute(
        """
        CREATE POLICY tenant_isolation ON "integration_configs"
        USING (
            current_setting('app.current_agency_id', true) = '0'
            OR agency_id = NULLIF(current_setting('app.current_agency_id', true), '')::int
        )
        """
    )


def downgrade() -> None:
    op.execute(
        'DROP POLICY IF EXISTS tenant_isolation ON "integration_configs"'
    )
    op.execute(
        'ALTER TABLE "integration_configs" DISABLE ROW LEVEL SECURITY'
    )
    op.drop_index("ix_integration_configs_provider", table_name="integration_configs")
    op.drop_index("ix_integration_configs_agency_id", table_name="integration_configs")
    op.drop_table("integration_configs")
