"""Add user feedback table for priority accuracy tracking

Revision ID: 002_user_feedback
Revises: 001_audit_trail
Create Date: 2026-05-11 21:34:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_user_feedback'
down_revision: Union[str, None] = '001_audit_trail'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create user_feedback table"""
    op.create_table(
        'user_feedback',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('keyword', sa.String(length=500), nullable=False),
        sa.Column('original_priority_score', sa.Float(), nullable=False),
        sa.Column('user_rating', sa.Integer(), nullable=True),
        sa.Column('user_priority_score', sa.Float(), nullable=True),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('feedback_type', sa.String(length=50), nullable=False),
        sa.Column('original_volume', sa.Integer(), nullable=True),
        sa.Column('original_difficulty', sa.Integer(), nullable=True),
        sa.Column('original_cpc', sa.Float(), nullable=True),
        sa.Column('original_intent', sa.String(length=50), nullable=True),
        sa.Column('agent_id', sa.String(length=100), nullable=False),
        sa.Column('task_id', sa.String(length=100), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_keyword_feedback_type', 'user_feedback', ['keyword', 'feedback_type'])
    op.create_index('idx_feedback_type_timestamp', 'user_feedback', ['feedback_type', 'timestamp'])
    op.create_index(op.f('ix_user_feedback_keyword'), 'user_feedback', ['keyword'])
    op.create_index(op.f('ix_user_feedback_feedback_type'), 'user_feedback', ['feedback_type'])
    op.create_index(op.f('ix_user_feedback_timestamp'), 'user_feedback', ['timestamp'])


def downgrade() -> None:
    """Drop user_feedback table"""
    op.drop_index(op.f('ix_user_feedback_timestamp'), table_name='user_feedback')
    op.drop_index(op.f('ix_user_feedback_feedback_type'), table_name='user_feedback')
    op.drop_index(op.f('ix_user_feedback_keyword'), table_name='user_feedback')
    op.drop_index('idx_feedback_type_timestamp', table_name='user_feedback')
    op.drop_index('idx_keyword_feedback_type', table_name='user_feedback')
    op.drop_table('user_feedback')
