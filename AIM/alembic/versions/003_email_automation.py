"""add email automation tables

Revision ID: 003_email_automation
Revises: 003
Create Date: 2026-05-16 20:04:12.655000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_email_automation'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create email_workflows table
    op.create_table(
        'email_workflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lead_id', sa.String(length=50), nullable=False),
        sa.Column('tier', sa.String(length=10), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('current_step', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_workflows_lead_id'), 'email_workflows', ['lead_id'], unique=False)
    op.create_index(op.f('ix_email_workflows_status'), 'email_workflows', ['status'], unique=False)

    # Create email_templates table
    op.create_table(
        'email_templates',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('tier', sa.String(length=10), nullable=False),
        sa.Column('step', sa.Integer(), nullable=False),
        sa.Column('subject_template', sa.Text(), nullable=False),
        sa.Column('html_template', sa.Text(), nullable=False),
        sa.Column('text_template', sa.Text(), nullable=False),
        sa.Column('ai_prompt', sa.Text(), nullable=True),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_templates_tier'), 'email_templates', ['tier'], unique=False)

    # Create scheduled_emails table
    op.create_table(
        'scheduled_emails',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_id', sa.String(length=50), nullable=False),
        sa.Column('recipient_email', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.Text(), nullable=False),
        sa.Column('html_content', sa.Text(), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('sendgrid_message_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['workflow_id'], ['email_workflows.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scheduled_emails_workflow_id'), 'scheduled_emails', ['workflow_id'], unique=False)
    op.create_index(op.f('ix_scheduled_emails_status'), 'scheduled_emails', ['status'], unique=False)
    op.create_index(op.f('ix_scheduled_emails_scheduled_at'), 'scheduled_emails', ['scheduled_at'], unique=False)

    # Create email_events table
    op.create_table(
        'email_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=20), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['email_id'], ['scheduled_emails.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_events_email_id'), 'email_events', ['email_id'], unique=False)
    op.create_index(op.f('ix_email_events_event_type'), 'email_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_email_events_occurred_at'), 'email_events', ['occurred_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order (respect foreign keys)
    op.drop_index(op.f('ix_email_events_occurred_at'), table_name='email_events')
    op.drop_index(op.f('ix_email_events_event_type'), table_name='email_events')
    op.drop_index(op.f('ix_email_events_email_id'), table_name='email_events')
    op.drop_table('email_events')

    op.drop_index(op.f('ix_scheduled_emails_scheduled_at'), table_name='scheduled_emails')
    op.drop_index(op.f('ix_scheduled_emails_status'), table_name='scheduled_emails')
    op.drop_index(op.f('ix_scheduled_emails_workflow_id'), table_name='scheduled_emails')
    op.drop_table('scheduled_emails')

    op.drop_index(op.f('ix_email_templates_tier'), table_name='email_templates')
    op.drop_table('email_templates')

    op.drop_index(op.f('ix_email_workflows_status'), table_name='email_workflows')
    op.drop_index(op.f('ix_email_workflows_lead_id'), table_name='email_workflows')
    op.drop_table('email_workflows')
