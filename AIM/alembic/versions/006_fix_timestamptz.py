"""fix email_workflows + scheduled_emails timestamp columns to timestamptz

Revision ID: 006
Revises: 005
Create Date: 2026-05-21 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # email_workflows: TIMESTAMP WITHOUT TIME ZONE → TIMESTAMP WITH TIME ZONE
    op.execute("""
        ALTER TABLE email_workflows
        ALTER COLUMN started_at TYPE timestamptz,
        ALTER COLUMN completed_at TYPE timestamptz,
        ALTER COLUMN created_at TYPE timestamptz
    """)

    # scheduled_emails: same conversion
    op.execute("""
        ALTER TABLE scheduled_emails
        ALTER COLUMN scheduled_at TYPE timestamptz,
        ALTER COLUMN sent_at TYPE timestamptz,
        ALTER COLUMN created_at TYPE timestamptz
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE email_workflows
        ALTER COLUMN started_at TYPE timestamp,
        ALTER COLUMN completed_at TYPE timestamp,
        ALTER COLUMN created_at TYPE timestamp
    """)

    op.execute("""
        ALTER TABLE scheduled_emails
        ALTER COLUMN scheduled_at TYPE timestamp,
        ALTER COLUMN sent_at TYPE timestamp,
        ALTER COLUMN created_at TYPE timestamp
    """)
