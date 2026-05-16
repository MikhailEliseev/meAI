"""add documents table

Revision ID: 003
Revises: 002
Create Date: 2026-05-17 01:12:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create documents table for clinic onboarding."""
    op.create_table(
        'documents',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('lead_id', sa.String(length=50), nullable=False),
        sa.Column('document_type', sa.String(length=20), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('ocr_text', sa.Text(), nullable=True),
        sa.Column('extracted_data', sa.JSON(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('validation_status', sa.String(length=20), nullable=True),
        sa.Column('validation_errors', sa.JSON(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=50), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_documents_lead_id', 'documents', ['lead_id'])
    op.create_index('ix_documents_document_type', 'documents', ['document_type'])
    op.create_index('ix_documents_status', 'documents', ['status'])
    op.create_index('ix_documents_uploaded_at', 'documents', ['uploaded_at'])


def downgrade() -> None:
    """Drop documents table."""
    op.drop_index('ix_documents_uploaded_at', table_name='documents')
    op.drop_index('ix_documents_status', table_name='documents')
    op.drop_index('ix_documents_document_type', table_name='documents')
    op.drop_index('ix_documents_lead_id', table_name='documents')
    op.drop_table('documents')
