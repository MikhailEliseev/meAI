"""Add audit trail table for compliance tracking

Revision ID: 001_audit_trail
Revises:
Create Date: 2026-05-11 21:33:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_audit_trail'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create audit_trail table"""
    op.create_table(
        'audit_trail',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('keyword', sa.String(length=500), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('likelihood_score', sa.Integer(), nullable=True),
        sa.Column('severity_score', sa.Integer(), nullable=True),
        sa.Column('risk_score', sa.Integer(), nullable=True),
        sa.Column('matched_patterns', sa.Text(), nullable=True),
        sa.Column('pattern_severity', sa.Integer(), nullable=True),
        sa.Column('fda_enforcement_found', sa.Integer(), nullable=True),
        sa.Column('fda_enforcement_count', sa.Integer(), nullable=True),
        sa.Column('fda_enforcement_details', sa.Text(), nullable=True),
        sa.Column('agent_id', sa.String(length=100), nullable=False),
        sa.Column('task_id', sa.String(length=100), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_keyword_timestamp', 'audit_trail', ['keyword', 'timestamp'])
    op.create_index('idx_risk_level_timestamp', 'audit_trail', ['risk_level', 'timestamp'])
    op.create_index('idx_action_timestamp', 'audit_trail', ['action', 'timestamp'])
    op.create_index(op.f('ix_audit_trail_keyword'), 'audit_trail', ['keyword'])
    op.create_index(op.f('ix_audit_trail_risk_level'), 'audit_trail', ['risk_level'])
    op.create_index(op.f('ix_audit_trail_timestamp'), 'audit_trail', ['timestamp'])


def downgrade() -> None:
    """Drop audit_trail table"""
    op.drop_index(op.f('ix_audit_trail_timestamp'), table_name='audit_trail')
    op.drop_index(op.f('ix_audit_trail_risk_level'), table_name='audit_trail')
    op.drop_index(op.f('ix_audit_trail_keyword'), table_name='audit_trail')
    op.drop_index('idx_action_timestamp', table_name='audit_trail')
    op.drop_index('idx_risk_level_timestamp', table_name='audit_trail')
    op.drop_index('idx_keyword_timestamp', table_name='audit_trail')
    op.drop_table('audit_trail')
