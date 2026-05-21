"""add missing tables: fz152_audit_log, linear_tasks, campaigns, campaign_attributions, experiments

Revision ID: 005
Revises: 004
Create Date: 2026-05-21 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # fz152_audit_log — immutable audit trail for ФЗ-152 compliance
    op.create_table(
        'fz152_audit_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('lead_id', sa.String(100), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('agent', sa.String(100), nullable=False, server_default='lead_capture'),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_fz152_lead_action', 'fz152_audit_log', ['lead_id', 'action'])
    op.create_index('idx_fz152_action_timestamp', 'fz152_audit_log', ['action', 'timestamp'])
    op.create_index(op.f('ix_fz152_audit_log_lead_id'), 'fz152_audit_log', ['lead_id'])
    op.create_index(op.f('ix_fz152_audit_log_action'), 'fz152_audit_log', ['action'])
    op.create_index(op.f('ix_fz152_audit_log_timestamp'), 'fz152_audit_log', ['timestamp'])

    # linear_tasks — Linear issue tracking for leads
    op.create_table(
        'linear_tasks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('lead_id', sa.String(), nullable=False),
        sa.Column('linear_issue_id', sa.String(), nullable=False),
        sa.Column('linear_url', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('assignee_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_linear_tasks_lead_id'), 'linear_tasks', ['lead_id'])
    op.create_index(op.f('ix_linear_tasks_linear_issue_id'), 'linear_tasks', ['linear_issue_id'], unique=True)

    # campaigns — marketing campaign tracking
    op.create_table(
        'campaigns',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('external_id', sa.String(100), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('daily_budget', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('currency', sa.String(10), nullable=False, server_default='RUB'),
        sa.Column('total_spent', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('utm_source', sa.String(100), nullable=True),
        sa.Column('utm_campaign', sa.String(100), nullable=True),
        sa.Column('utm_medium', sa.String(100), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_campaigns_external_id'), 'campaigns', ['external_id'])
    op.create_index(op.f('ix_campaigns_platform'), 'campaigns', ['platform'])
    op.create_index(op.f('ix_campaigns_utm_campaign'), 'campaigns', ['utm_campaign'])

    # campaign_attributions — UTM → lead conversion tracking
    op.create_table(
        'campaign_attributions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.String(50), nullable=False),
        sa.Column('utm_source', sa.String(100), nullable=True),
        sa.Column('utm_campaign', sa.String(100), nullable=True),
        sa.Column('utm_medium', sa.String(100), nullable=True),
        sa.Column('attributed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_conversion', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('conversion_revenue', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('conversion_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id']),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_campaign_attributions_campaign_id'), 'campaign_attributions', ['campaign_id'])
    op.create_index(op.f('ix_campaign_attributions_lead_id'), 'campaign_attributions', ['lead_id'])

    # experiments — A/B test tracking
    op.create_table(
        'experiments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('variant_a_name', sa.String(100), nullable=False),
        sa.Column('variant_b_name', sa.String(100), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='running'),
        sa.Column('visitors_a', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('conversions_a', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('visitors_b', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('conversions_b', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('winner', sa.String(10), nullable=True),
        sa.Column('p_value', sa.Float(), nullable=True),
        sa.Column('relative_lift', sa.Float(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('experiments')
    op.drop_index(op.f('ix_campaign_attributions_lead_id'), table_name='campaign_attributions')
    op.drop_index(op.f('ix_campaign_attributions_campaign_id'), table_name='campaign_attributions')
    op.drop_table('campaign_attributions')
    op.drop_index(op.f('ix_campaigns_utm_campaign'), table_name='campaigns')
    op.drop_index(op.f('ix_campaigns_platform'), table_name='campaigns')
    op.drop_index(op.f('ix_campaigns_external_id'), table_name='campaigns')
    op.drop_table('campaigns')
    op.drop_index(op.f('ix_linear_tasks_linear_issue_id'), table_name='linear_tasks')
    op.drop_index(op.f('ix_linear_tasks_lead_id'), table_name='linear_tasks')
    op.drop_table('linear_tasks')
    op.drop_index(op.f('ix_fz152_audit_log_timestamp'), table_name='fz152_audit_log')
    op.drop_index(op.f('ix_fz152_audit_log_action'), table_name='fz152_audit_log')
    op.drop_index(op.f('ix_fz152_audit_log_lead_id'), table_name='fz152_audit_log')
    op.drop_index('idx_fz152_action_timestamp', table_name='fz152_audit_log')
    op.drop_index('idx_fz152_lead_action', table_name='fz152_audit_log')
    op.drop_table('fz152_audit_log')
