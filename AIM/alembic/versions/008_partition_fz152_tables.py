"""partition fz152_audit_log + documents by RANGE for ФЗ-152 7-year retention

Revision ID: 008
Revises: 007
Create Date: 2026-05-21 13:00:00.000000

Partitions:
  - fz152_audit_log BY RANGE (timestamp) — yearly 2026–2033
  - documents BY RANGE (uploaded_at) — yearly 2026–2033

leads table is NOT partitioned because 3 FK constraints reference leads.id
(linear_tasks, email_workflows, campaign_attributions) and PostgreSQL does
not support foreign keys pointing to partitioned tables.
If partitioning becomes necessary, the FKs must be dropped and referential
integrity enforced at the application layer.

Also fixes documents.uploaded_at + processed_at: TIMESTAMP → TIMESTAMPTZ.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


YEARS = list(range(2026, 2034))  # 2026–2033 inclusive (8 years, 7-year retention window)


def _partition_fz152_audit_log_up() -> None:
    """Convert fz152_audit_log to PARTITION BY RANGE (timestamp)."""
    op.execute("ALTER TABLE fz152_audit_log RENAME TO fz152_audit_log_old")

    op.execute("""
        CREATE TABLE fz152_audit_log (
            id INTEGER NOT NULL,
            lead_id VARCHAR(100) NOT NULL,
            action VARCHAR(50) NOT NULL,
            ip_address VARCHAR(45) NOT NULL,
            details JSON,
            agent VARCHAR(100) NOT NULL DEFAULT 'lead_capture',
            timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id, timestamp)
        ) PARTITION BY RANGE (timestamp)
    """)

    op.execute("CREATE TABLE fz152_audit_log_default PARTITION OF fz152_audit_log DEFAULT")

    for year in YEARS:
        op.execute(f"""
            CREATE TABLE fz152_audit_log_{year}
            PARTITION OF fz152_audit_log
            FOR VALUES FROM ('{year}-01-01') TO ('{year + 1}-01-01')
        """)

    op.execute("CREATE INDEX idx_fz152_lead_action ON fz152_audit_log (lead_id, action)")
    op.execute("CREATE INDEX idx_fz152_action_timestamp ON fz152_audit_log (action, timestamp)")

    # Create sequence for id and wire it as default
    op.execute("CREATE SEQUENCE fz152_audit_log_id_seq OWNED BY fz152_audit_log.id")
    op.execute("""
        ALTER TABLE fz152_audit_log
        ALTER COLUMN id SET DEFAULT nextval('fz152_audit_log_id_seq')
    """)

    op.execute("""
        INSERT INTO fz152_audit_log
        SELECT * FROM fz152_audit_log_old
    """)

    op.execute("""
        SELECT setval('fz152_audit_log_id_seq',
            COALESCE((SELECT max(id) FROM fz152_audit_log), 0))
    """)

    op.execute("DROP TABLE fz152_audit_log_old")


def _partition_fz152_audit_log_down() -> None:
    """Revert fz152_audit_log to regular table."""
    op.execute("ALTER TABLE fz152_audit_log RENAME TO fz152_audit_log_partitioned")

    # Drop the sequence owned by the partitioned table so SERIAL won't conflict
    op.execute("DROP SEQUENCE IF EXISTS fz152_audit_log_id_seq CASCADE")

    op.execute("""
        CREATE TABLE fz152_audit_log (
            id SERIAL PRIMARY KEY,
            lead_id VARCHAR(100) NOT NULL,
            action VARCHAR(50) NOT NULL,
            ip_address VARCHAR(45) NOT NULL,
            details JSON,
            agent VARCHAR(100) NOT NULL DEFAULT 'lead_capture',
            timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        INSERT INTO fz152_audit_log
        (id, lead_id, action, ip_address, details, agent, timestamp)
        SELECT id, lead_id, action, ip_address, details, agent, timestamp
        FROM fz152_audit_log_partitioned
    """)

    op.execute("""
        SELECT setval('fz152_audit_log_id_seq',
            COALESCE((SELECT max(id) FROM fz152_audit_log), 0))
    """)

    op.execute("""
        CREATE INDEX idx_fz152_lead_action ON fz152_audit_log (lead_id, action)
    """)
    op.execute("""
        CREATE INDEX idx_fz152_action_timestamp ON fz152_audit_log (action, timestamp)
    """)

    op.execute("DROP TABLE fz152_audit_log_partitioned")


def _partition_documents_up() -> None:
    """Convert documents to PARTITION BY RANGE (uploaded_at)."""
    op.execute("ALTER TABLE documents RENAME TO documents_old")

    op.execute("""
        CREATE TABLE documents (
            id VARCHAR(50) NOT NULL,
            lead_id VARCHAR(50) NOT NULL,
            document_type VARCHAR(20) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            file_size INTEGER NOT NULL,
            mime_type VARCHAR(100) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            ocr_text TEXT,
            extracted_data JSON,
            confidence_score FLOAT,
            validation_status VARCHAR(20),
            validation_errors JSON,
            uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            processed_at TIMESTAMPTZ,
            created_by VARCHAR(50) NOT NULL,
            ip_address VARCHAR(45),
            PRIMARY KEY (id, uploaded_at)
        ) PARTITION BY RANGE (uploaded_at)
    """)

    op.execute("CREATE TABLE documents_default PARTITION OF documents DEFAULT")

    for year in YEARS:
        op.execute(f"""
            CREATE TABLE documents_{year}
            PARTITION OF documents
            FOR VALUES FROM ('{year}-01-01') TO ('{year + 1}-01-01')
        """)

    op.execute("CREATE INDEX ix_documents_lead_id ON documents (lead_id)")
    op.execute("CREATE INDEX ix_documents_document_type ON documents (document_type)")
    op.execute("CREATE INDEX ix_documents_status ON documents (status)")
    op.execute("CREATE INDEX ix_documents_uploaded_at ON documents (uploaded_at)")

    op.execute("""
        INSERT INTO documents
        SELECT * FROM documents_old
    """)

    op.execute("DROP TABLE documents_old")


def _partition_documents_down() -> None:
    """Revert documents to regular table."""
    op.execute("ALTER TABLE documents RENAME TO documents_partitioned")

    op.execute("""
        CREATE TABLE documents (
            id VARCHAR(50) PRIMARY KEY,
            lead_id VARCHAR(50) NOT NULL,
            document_type VARCHAR(20) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            file_size INTEGER NOT NULL,
            mime_type VARCHAR(100) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            ocr_text TEXT,
            extracted_data JSON,
            confidence_score FLOAT,
            validation_status VARCHAR(20),
            validation_errors JSON,
            uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            processed_at TIMESTAMPTZ,
            created_by VARCHAR(50) NOT NULL,
            ip_address VARCHAR(45)
        )
    """)

    op.execute("""
        INSERT INTO documents
        SELECT * FROM documents_partitioned
    """)

    op.execute("CREATE INDEX ix_documents_lead_id ON documents (lead_id)")
    op.execute("CREATE INDEX ix_documents_document_type ON documents (document_type)")
    op.execute("CREATE INDEX ix_documents_status ON documents (status)")
    op.execute("CREATE INDEX ix_documents_uploaded_at ON documents (uploaded_at)")

    op.execute("DROP TABLE documents_partitioned")


def upgrade() -> None:
    _partition_fz152_audit_log_up()
    _partition_documents_up()


def downgrade() -> None:
    _partition_documents_down()
    _partition_fz152_audit_log_down()
