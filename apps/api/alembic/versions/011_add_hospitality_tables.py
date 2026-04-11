"""Add hospitality tables: hospitality_clients, room_types, daily_revenue,
gratuity_tips, inventory_stock_takes

Revision ID: 011
Revises: 008
Create Date: 2026-04-10

"""
from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- hospitality_clients ---
    op.create_table(
        "hospitality_clients",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("pms_system", sa.String(50), nullable=True),
        sa.Column("pms_api_key", sa.String(255), nullable=True),
        sa.Column("pms_property_id", sa.String(50), nullable=True),
        sa.Column("currency", sa.String(3), server_default="USD"),
        sa.Column("financial_year_start", sa.Integer(), server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("client_id"),
    )

    # --- room_types ---
    op.create_table(
        "room_types",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hospitality_client_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(20), nullable=True),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("avg_daily_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["hospitality_client_id"], ["hospitality_clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_room_types_hospitality_client_id", "room_types", ["hospitality_client_id"])

    # --- daily_revenue ---
    op.create_table(
        "daily_revenue",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hospitality_client_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("room_type_id", sa.Integer(), nullable=True),
        sa.Column("revenue_stream", sa.String(50), nullable=True),
        sa.Column("rooms_available", sa.Integer(), server_default="0"),
        sa.Column("rooms_occupied", sa.Integer(), server_default="0"),
        sa.Column("total_revenue", sa.Numeric(12, 2), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["hospitality_client_id"], ["hospitality_clients.id"]),
        sa.ForeignKeyConstraint(["room_type_id"], ["room_types.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_daily_revenue_hospitality_client_id", "daily_revenue", ["hospitality_client_id"])
    op.create_index("idx_daily_revenue_date", "daily_revenue", ["date"])

    # --- gratuity_tips ---
    op.create_table(
        "gratuity_tips",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hospitality_client_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["hospitality_client_id"], ["hospitality_clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_gratuity_tips_hospitality_client_id", "gratuity_tips", ["hospitality_client_id"])

    # --- inventory_stock_takes ---
    op.create_table(
        "inventory_stock_takes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hospitality_client_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("item_code", sa.String(50), nullable=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("quantity_counted", sa.Integer(), server_default="0"),
        sa.Column("quantity_expected", sa.Integer(), server_default="0"),
        sa.Column("unit_cost", sa.Numeric(10, 2), server_default="0"),
        sa.Column("variance", sa.Numeric(12, 2), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["hospitality_client_id"], ["hospitality_clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_inventory_stock_takes_hospitality_client_id", "inventory_stock_takes", ["hospitality_client_id"])


def downgrade() -> None:
    op.drop_table("inventory_stock_takes")
    op.drop_table("gratuity_tips")
    op.drop_table("daily_revenue")
    op.drop_table("room_types")
    op.drop_table("hospitality_clients")
