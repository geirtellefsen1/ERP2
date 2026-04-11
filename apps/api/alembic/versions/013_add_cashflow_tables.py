"""Add cashflow_forecasts, cashflow_forecast_lines, forecast_alerts tables

Revision ID: 013
Revises: 009
Create Date: 2026-04-10

"""
from alembic import op
import sqlalchemy as sa

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Cashflow forecasts table
    op.create_table(
        "cashflow_forecasts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("forecast_date", sa.Date(), nullable=False),
        sa.Column("forecast_generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), server_default="draft", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_cashflow_forecasts_client_id", "cashflow_forecasts", ["client_id"])
    op.create_index("idx_cashflow_forecasts_status", "cashflow_forecasts", ["status"])

    # Cashflow forecast lines table
    op.create_table(
        "cashflow_forecast_lines",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("forecast_id", sa.Integer(), nullable=False),
        sa.Column("week_commencing", sa.Date(), nullable=False),
        sa.Column("opening_balance", sa.Numeric(15, 2), server_default="0", nullable=True),
        sa.Column("receipts", sa.Numeric(15, 2), server_default="0", nullable=True),
        sa.Column("payments", sa.Numeric(15, 2), server_default="0", nullable=True),
        sa.Column("closing_balance", sa.Numeric(15, 2), server_default="0", nullable=True),
        sa.Column("alert_flag", sa.Boolean(), server_default="false", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["forecast_id"], ["cashflow_forecasts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_cashflow_forecast_lines_forecast_id", "cashflow_forecast_lines", ["forecast_id"])

    # Forecast alerts table
    op.create_table(
        "forecast_alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("forecast_id", sa.Integer(), nullable=False),
        sa.Column("alert_type", sa.String(20), nullable=True),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("week_number", sa.Integer(), nullable=True),
        sa.Column("narrative", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["forecast_id"], ["cashflow_forecasts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_forecast_alerts_client_id", "forecast_alerts", ["client_id"])
    op.create_index("idx_forecast_alerts_forecast_id", "forecast_alerts", ["forecast_id"])
    op.create_index("idx_forecast_alerts_severity", "forecast_alerts", ["severity"])


def downgrade() -> None:
    op.drop_table("forecast_alerts")
    op.drop_table("cashflow_forecast_lines")
    op.drop_table("cashflow_forecasts")
