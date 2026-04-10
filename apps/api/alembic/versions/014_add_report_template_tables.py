"""Add report_templates and generated_reports tables

Revision ID: 014
Revises: 010
Create Date: 2026-04-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision = "014"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Report templates table
    op.create_table(
        "report_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("report_type", sa.String(20), nullable=True),
        sa.Column("tone", sa.String(50), server_default="formal", nullable=True),
        sa.Column("length", sa.String(30), server_default="full", nullable=True),
        sa.Column("sections", JSON, nullable=True),
        sa.Column("delivery_config", JSON, nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_report_templates_client_id", "report_templates", ["client_id"])

    # Generated reports table
    op.create_table(
        "generated_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), server_default="draft", nullable=True),
        sa.Column("html_content", sa.Text(), nullable=True),
        sa.Column("narrative_commentary", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_email", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["template_id"], ["report_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_generated_reports_client_id", "generated_reports", ["client_id"])
    op.create_index("idx_generated_reports_template_id", "generated_reports", ["template_id"])
    op.create_index("idx_generated_reports_status", "generated_reports", ["status"])


def downgrade() -> None:
    op.drop_table("generated_reports")
    op.drop_table("report_templates")
