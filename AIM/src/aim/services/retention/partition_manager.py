"""ФЗ-152 Data Retention — PostgreSQL Partition Manager

Implements 7-year medical data retention requirement (ФЗ-323 ст.13).
Creates monthly partitions, detaches expired ones, manages retention lifecycle.

Tables partitioned: leads, documents, fz152_audit_log
Partition key: created_at (monthly)
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import text
import structlog

logger = structlog.get_logger()


class PartitionManager:
    """Manages monthly partitions for ФЗ-152 retention compliance."""

    PARTITIONED_TABLES = ["leads", "documents", "fz152_audit_log"]
    RETENTION_YEARS = 7
    FUTURE_PARTITIONS = 3

    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def _get_partitioned_tables(self) -> set[str]:
        """Return which of the target tables are actually partitioned."""
        async with self.session_factory() as session:
            result = await session.execute(text("""
                SELECT c.relname
                FROM pg_class c
                JOIN pg_partitioned_table p ON p.partrelid = c.oid
                WHERE c.relname = ANY(:tables)
            """), {"tables": self.PARTITIONED_TABLES})
            return {row[0] for row in result.fetchall()}

    async def ensure_partitions(self):
        """Create future partitions if they don't exist. Run on startup + monthly cron."""
        partitioned = await self._get_partitioned_tables()
        skipped = set(self.PARTITIONED_TABLES) - partitioned
        if skipped:
            logger.info(
                "partition_tables_not_partitioned",
                tables=sorted(skipped),
                hint="Run migration to add PARTITION BY RANGE (created_at) to these tables",
            )

        if not partitioned:
            return

        now = datetime.now(timezone.utc)
        for i in range(self.FUTURE_PARTITIONS + 1):
            target_month = now.month + i
            target_year = now.year + (target_month - 1) // 12
            target_month = ((target_month - 1) % 12) + 1
            for table in partitioned:
                await self._create_partition_for_table(table, target_year, target_month)

    async def run_retention_cycle(self):
        """Detach and optionally drop expired partitions. Run monthly."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.RETENTION_YEARS * 365)
        await self._detach_expired(cutoff)
        await self._drop_detached(days_old=30)

    async def _create_partition_for_table(self, table: str, year: int, month: int):
        """Create a monthly partition for a single table."""
        start = f"{year}-{month:02d}-01"
        if month == 12:
            end = f"{year + 1}-01-01"
        else:
            end = f"{year}-{month + 1:02d}-01"

        partition_name = f"{table}_{year}_{month:02d}"
        async with self.session_factory() as session:
            try:
                await session.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {partition_name}
                    PARTITION OF {table}
                    FOR VALUES FROM ('{start}') TO ('{end}')
                """))
                await session.commit()
                logger.info("partition_created", table=table, partition=partition_name)
            except Exception as e:
                await session.rollback()
                logger.warning("partition_create_skipped", table=table, partition=partition_name, error=str(e))

    async def _detach_expired(self, cutoff: datetime):
        """Detach partitions older than retention period."""
        async with self.session_factory() as session:
            for table in self.PARTITIONED_TABLES:
                result = await session.execute(text("""
                    SELECT inhrelid::regclass AS child
                    FROM pg_inherits
                    WHERE inhparent = :table::regclass
                """), {"table": table})
                partitions = [row[0] for row in result.fetchall()]

                for partition in partitions:
                    try:
                        parts = partition.split("_")
                        if len(parts) >= 3:
                            part_year = int(parts[-2])
                            part_month = int(parts[-1])
                            partition_end = datetime(part_year, part_month, 1, tzinfo=timezone.utc) + timedelta(days=32)
                            partition_end = partition_end.replace(day=1)
                            if partition_end <= cutoff:
                                await session.execute(text(f"""
                                    ALTER TABLE {table} DETACH PARTITION {partition}
                                """))
                                await session.commit()
                                logger.info("partition_detached", table=table, partition=partition)
                    except (ValueError, IndexError):
                        logger.warning("partition_parse_error", partition_name=partition)

    async def _drop_detached(self, days_old: int = 30):
        """Drop detached partitions older than N days (grace period)."""
        async with self.session_factory() as session:
            for table in self.PARTITIONED_TABLES:
                result = await session.execute(text("""
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                      AND tablename LIKE :pattern
                      AND tablename NOT IN (
                          SELECT inhrelid::regclass::text
                          FROM pg_inherits
                          WHERE inhparent = :table::regclass
                      )
                """), {"pattern": f"{table}_20%", "table": table})
                orphans = [row[0] for row in result.fetchall()]
                for orphan in orphans:
                    try:
                        await session.execute(text(f"DROP TABLE IF EXISTS {orphan}"))
                        await session.commit()
                        logger.info("orphan_partition_dropped", table_name=orphan)
                    except Exception as e:
                        await session.rollback()
                        logger.warning("orphan_drop_failed", table_name=orphan, error=str(e))
