"""add_leads_table

Revision ID: c8de5ad75fa5
Revises: 002_user_feedback
Create Date: 2026-05-16 20:26:36.673230+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8de5ad75fa5'
down_revision: Union[str, None] = '002_user_feedback'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create leads table
    op.create_table(
        'leads',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name_encrypted', sa.Text(), nullable=False),
        sa.Column('phone_encrypted', sa.Text(), nullable=False),
        sa.Column('email_encrypted', sa.Text(), nullable=False),
        sa.Column('email_hash', sa.String(64), nullable=False),
        sa.Column('clinic_name_encrypted', sa.Text(), nullable=False),
        sa.Column('message_encrypted', sa.Text(), nullable=True),
        sa.Column('specialty', sa.String(50), nullable=False),
        sa.Column('fz152_consent', sa.Boolean(), nullable=False),
        sa.Column('fz152_consent_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fz152_consent_ip', sa.String(45), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('utm_source', sa.String(100), nullable=True),
        sa.Column('utm_medium', sa.String(100), nullable=True),
        sa.Column('utm_campaign', sa.String(100), nullable=True),
        sa.Column('utm_content', sa.String(100), nullable=True),
        sa.Column('utm_term', sa.String(100), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=False, default=False),
        sa.Column('linear_task_id', sa.String(50), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('tier', sa.String(20), nullable=True),
    )

    # Create indexes
    op.create_index('ix_leads_email_hash', 'leads', ['email_hash'])
    op.create_index('ix_leads_specialty', 'leads', ['specialty'])
    op.create_index('ix_leads_source', 'leads', ['source'])


def downgrade() -> None:
    op.drop_index('ix_leads_source', 'leads')
    op.drop_index('ix_leads_specialty', 'leads')
    op.drop_index('ix_leads_email_hash', 'leads')
    op.drop_table('leads')

