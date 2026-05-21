"""create sales admin tables — conversations, messages, escalations, activity log

Revision ID: 010
Revises: 009
Create Date: 2026-05-21 16:00:00.000000

Part of: Phase 13 — AI Sales Admin Agent
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'sales_conversations',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('client_id', sa.String(50), nullable=True),
        sa.Column('project_id', sa.String(50), nullable=True),
        sa.Column('lead_id', sa.String(50), nullable=True),
        sa.Column('channel', sa.String(20), nullable=False),
        sa.Column('channel_user_id', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('messages_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('qualification_result', postgresql.JSONB, nullable=True),
        sa.Column('escalation_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_sales_conv_channel_user', 'sales_conversations', ['channel', 'channel_user_id'])
    op.create_index('idx_sales_conv_status', 'sales_conversations', ['status'])
    op.create_index('idx_sales_conv_lead', 'sales_conversations', ['lead_id'])

    op.create_table(
        'sales_messages',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('conversation_id', sa.String(50), sa.ForeignKey('sales_conversations.id'), nullable=False),
        sa.Column('direction', sa.String(10), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('content_type', sa.String(20), nullable=False, server_default='text'),
        sa.Column('sender_id', sa.String(100), nullable=True),
        sa.Column('ai_generated', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('tool_calls', postgresql.JSONB, nullable=True),
        sa.Column('response_time_ms', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_sales_msg_conv', 'sales_messages', ['conversation_id', 'created_at'])

    op.create_table(
        'sales_escalations',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('conversation_id', sa.String(50), sa.ForeignKey('sales_conversations.id'), nullable=False),
        sa.Column('reason', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('context_snapshot', postgresql.JSONB, nullable=True),
        sa.Column('escalated_to', sa.String(50), nullable=True),
        sa.Column('notification_channel', sa.String(20), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_sales_esc_conv', 'sales_escalations', ['conversation_id'])

    op.create_table(
        'sales_agent_activity',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('agent_type', sa.String(30), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('conversation_id', sa.String(50), nullable=True),
        sa.Column('lead_id', sa.String(50), nullable=True),
        sa.Column('details', postgresql.JSONB, nullable=True),
        sa.Column('duration_ms', sa.Integer, nullable=True),
        sa.Column('success', sa.Boolean, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_sales_act_time', 'sales_agent_activity', ['created_at'])
    op.create_index('idx_sales_act_type', 'sales_agent_activity', ['agent_type', 'action'])


def downgrade() -> None:
    op.drop_table('sales_agent_activity')
    op.drop_table('sales_escalations')
    op.drop_table('sales_messages')
    op.drop_table('sales_conversations')
