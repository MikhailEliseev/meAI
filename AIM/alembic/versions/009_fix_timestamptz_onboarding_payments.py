"""fix onboardings + payments timestamp columns to timestamptz

Revision ID: 009
Revises: 008
Create Date: 2026-05-21 13:15:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # onboardings: TIMESTAMP WITHOUT TIME ZONE → TIMESTAMP WITH TIME ZONE
    op.execute("""
        ALTER TABLE onboardings
        ALTER COLUMN started_at TYPE timestamptz,
        ALTER COLUMN completed_at TYPE timestamptz,
        ALTER COLUMN failed_at TYPE timestamptz
    """)

    # payments: same conversion
    op.execute("""
        ALTER TABLE payments
        ALTER COLUMN refunded_at TYPE timestamptz,
        ALTER COLUMN created_at TYPE timestamptz,
        ALTER COLUMN updated_at TYPE timestamptz,
        ALTER COLUMN completed_at TYPE timestamptz
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE onboardings
        ALTER COLUMN started_at TYPE timestamp,
        ALTER COLUMN completed_at TYPE timestamp,
        ALTER COLUMN failed_at TYPE timestamp
    """)

    op.execute("""
        ALTER TABLE payments
        ALTER COLUMN refunded_at TYPE timestamp,
        ALTER COLUMN created_at TYPE timestamp,
        ALTER COLUMN updated_at TYPE timestamp,
        ALTER COLUMN completed_at TYPE timestamp
    """)
