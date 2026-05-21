"""fix email_events + email_templates timestamp columns to timestamptz

Revision ID: 007
Revises: 006
Create Date: 2026-05-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # email_events: TIMESTAMP WITHOUT TIME ZONE → TIMESTAMP WITH TIME ZONE
    op.execute("""
        ALTER TABLE email_events
        ALTER COLUMN occurred_at TYPE timestamptz,
        ALTER COLUMN created_at TYPE timestamptz
    """)

    # email_templates: same conversion
    op.execute("""
        ALTER TABLE email_templates
        ALTER COLUMN created_at TYPE timestamptz,
        ALTER COLUMN updated_at TYPE timestamptz
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE email_events
        ALTER COLUMN occurred_at TYPE timestamp,
        ALTER COLUMN created_at TYPE timestamp
    """)

    op.execute("""
        ALTER TABLE email_templates
        ALTER COLUMN created_at TYPE timestamp,
        ALTER COLUMN updated_at TYPE timestamp
    """)
