"""Add whatsapp_messages and conversation_flows tables

Revision ID: 005
Revises: 004
Create Date: 2026-04-10

"""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # WhatsApp messages table
    op.create_table(
        "whatsapp_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("phone_number", sa.String(20), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("direction", sa.String(20), server_default="inbound", nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), server_default="pending", nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("escalated_to_agent_id", sa.Integer(), nullable=True),
        sa.Column("escalation_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["escalated_to_agent_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_whatsapp_messages_client_id", "whatsapp_messages", ["client_id"])
    op.create_index("idx_whatsapp_messages_phone_number", "whatsapp_messages", ["phone_number"])
    op.create_index("idx_whatsapp_messages_status", "whatsapp_messages", ["status"])

    # Conversation flows table
    op.create_table(
        "conversation_flows",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("phone_number", sa.String(20), nullable=True),
        sa.Column("flow_type", sa.String(50), nullable=True),
        sa.Column("state", sa.JSON(), nullable=True),
        sa.Column("completed", sa.Boolean(), server_default=sa.text("false"), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_conversation_flows_client_id", "conversation_flows", ["client_id"])
    op.create_index("idx_conversation_flows_phone_number", "conversation_flows", ["phone_number"])


def downgrade() -> None:
    op.drop_table("conversation_flows")
    op.drop_table("whatsapp_messages")
