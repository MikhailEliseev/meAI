"""Add onboarding table

Revision ID: 004
Revises: 003
Create Date: 2026-05-17 01:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create onboardings table."""
    op.create_table(
        'onboardings',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('lead_id', sa.String(length=50), nullable=False),
        sa.Column('payment_id', sa.String(length=50), nullable=True),
        sa.Column('state', sa.String(length=50), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('documents_uploaded', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('documents_validated', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('onboarding_fee', sa.Float(), nullable=False, server_default='50000.0'),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('failed_at', sa.DateTime(), nullable=True),
        sa.Column('failure_reason', sa.String(length=500), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_onboardings_lead_id', 'onboardings', ['lead_id'])
    op.create_index('ix_onboardings_state', 'onboardings', ['state'])
    op.create_index('ix_onboardings_started_at', 'onboardings', ['started_at'])


def downgrade() -> None:
    """Drop onboardings table."""
    op.drop_index('ix_onboardings_started_at', table_name='onboardings')
    op.drop_index('ix_onboardings_state', table_name='onboardings')
    op.drop_index('ix_onboardings_lead_id', table_name='onboardings')
    op.drop_table('onboardings')
