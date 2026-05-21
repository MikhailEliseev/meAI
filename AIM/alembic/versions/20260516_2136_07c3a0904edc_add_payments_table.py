"""Add payments table

Revision ID: 07c3a0904edc
Revises: c8de5ad75fa5
Create Date: 2026-05-16 21:36:00.780652+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '07c3a0904edc'
down_revision: Union[str, None] = 'c8de5ad75fa5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'payments',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='RUB'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('payment_method', sa.String(50), nullable=False),
        sa.Column('customer_name_encrypted', sa.String(500), nullable=False),
        sa.Column('customer_email_encrypted', sa.String(500), nullable=False),
        sa.Column('customer_phone_encrypted', sa.String(500), nullable=True),
        sa.Column('card_last4', sa.String(4), nullable=True),
        sa.Column('card_brand', sa.String(20), nullable=True),
        sa.Column('external_transaction_id', sa.String(100), nullable=True),
        sa.Column('lead_id', sa.String(50), nullable=True),
        sa.Column('payment_metadata', sa.JSON(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('error_message', sa.String(500), nullable=True),
        sa.Column('refunded_amount', sa.Float(), nullable=True),
        sa.Column('refund_reason', sa.String(500), nullable=True),
        sa.Column('refunded_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
    )
    op.create_index('ix_payments_status', 'payments', ['status'])
    op.create_index('ix_payments_external_transaction_id', 'payments', ['external_transaction_id'])
    op.create_index('ix_payments_lead_id', 'payments', ['lead_id'])
    op.create_index('ix_payments_created_at', 'payments', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_payments_created_at', table_name='payments')
    op.drop_index('ix_payments_lead_id', table_name='payments')
    op.drop_index('ix_payments_external_transaction_id', table_name='payments')
    op.drop_index('ix_payments_status', table_name='payments')
    op.drop_table('payments')
