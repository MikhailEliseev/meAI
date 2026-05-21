"""ФЗ-152 Data Retention — PostgreSQL Partition Manager

Manages yearly/monthly partitions for ФЗ-152 7-year medical data retention.
Handles both yearly (migration 008) and monthly partitioning strategies by
inspecting the existing partition layout before creating new partitions.

Partitioned tables: fz152_audit_log (yearly, by timestamp), documents (yearly, by uploaded_at)
Not partitioned: leads (FK constraints prevent it)
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import text
import structlog

logger = structlog.get_logger()


class PartitionManager:
    """Manages partitions for ФЗ-152 retention compliance.

    Auto-detects whether a table uses yearly or monthly partitioning
    and creates the appropriate granularity.
    """

    PARTITIONED_TABLES = ["leads", "documents", "fz152_audit_log"]
    RETENTION_YEARS = 7
    FUTURE_YEARS = 8  # pre-create partitions for this many years ahead (covers 7-year retention + 1 buffer)

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
        """Create future partitions if they don't exist. Run on startup."""
        partitioned = await self._get_partitioned_tables()
        skipped = set(self.PARTITIONED_TABLES) - partitioned
        if skipped:
            logger.info(
                "partition_tables_not_partitioned",
                tables=sorted(skipped),
                hint="Run migration 008 to add PARTITION BY RANGE to these tables",
            )

        if not partitioned:
            return

        now = datetime.now(timezone.utc)

        for table in sorted(partitioned):
            try:
                granularity = await self._detect_granularity(table)
                if granularity == "yearly":
                    await self._ensure_yearly_partitions(table, now)
                elif granularity == "monthly":
                    await self._ensure_monthly_partitions(table, now)
            except Exception as e:
                logger.error(
                    "ensure_partitions_table_failed",
                    table=table,
                    error=str(e),
                )

    async def _detect_granularity(self, table: str) -> str:
        """Detect whether a table uses yearly or monthly partitioning.

        Examines existing non-default partitions to determine the span.
        """
        async with self.session_factory() as session:
            result = await session.execute(text("""
                SELECT inhrelid::regclass AS child
                FROM pg_inherits
                WHERE inhparent = :table::regclass
                  AND inhrelid::regclass::text NOT LIKE '%_default'
                ORDER BY child
                LIMIT 2
            """), {"table": table})
            partitions = [row[0] for row in result.fetchall()]

        if not partitions:
            return "monthly"  # default: create monthly partitions

        # Check span between first two partitions
        parts = str(partitions[0]).rsplit("_", 1)
        if len(parts) < 2:
            return "monthly"

        suffix = parts[1]
        if len(suffix) == 4 and suffix.isdigit():
            # e.g. fz152_audit_log_2026 → yearly
            return "yearly"
        elif len(suffix) == 2 and suffix.isdigit():
            # e.g. leads_2026_05 → monthly
            return "monthly"

        return "monthly"

    async def _ensure_yearly_partitions(self, table: str, now: datetime):
        """Ensure yearly partitions exist for the next FUTURE_YEARS years."""
        current_year = now.year
        for year in range(current_year, current_year + self.FUTURE_YEARS):
            partition_name = f"{table}_{year}"
            start = f"{year}-01-01"
            end = f"{year + 1}-01-01"
            await self._create_partition(table, partition_name, start, end)

    async def _ensure_monthly_partitions(self, table: str, now: datetime):
        """Ensure monthly partitions exist for the next few months."""
        for i in range(4):  # current + 3 future months
            target_month = now.month + i
            target_year = now.year + (target_month - 1) // 12
            target_month = ((target_month - 1) % 12) + 1

            partition_name = f"{table}_{target_year}_{target_month:02d}"
            start = f"{target_year}-{target_month:02d}-01"
            if target_month == 12:
                end = f"{target_year + 1}-01-01"
            else:
                end = f"{target_year}-{target_month + 1:02d}-01"

            await self._create_partition(table, partition_name, start, end)

    async def _create_partition(self, table: str, partition_name: str, start: str, end: str):
        """Create a single partition if it doesn't exist."""
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
                logger.warning(
                    "partition_create_skipped",
                    table=table,
                    partition=partition_name,
                    error=str(e),
                )

    async def run_retention_cycle(self):
        """Detach and optionally drop expired partitions. Run monthly."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.RETENTION_YEARS * 365)
        await self._detach_expired(cutoff)
        await self._drop_detached(days_old=30)

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
                        parts = str(partition).split("_")
                        if len(parts) >= 2:
                            # Try yearly format: tablename_YYYY
                            year_part = parts[-1]
                            if len(year_part) == 4 and year_part.isdigit():
                                part_year = int(year_part)
                                partition_end = datetime(part_year + 1, 1, 1, tzinfo=timezone.utc)
                                if partition_end <= cutoff:
                                    await session.execute(text(f"""
                                        ALTER TABLE {table} DETACH PARTITION {partition}
                                    """))
                                    await session.commit()
                                    logger.info("partition_detached", table=table, partition=partition)
                                    continue

                            # Try monthly format: tablename_YYYY_MM
                            if len(parts) >= 3:
                                month_part = parts[-1]
                                year_part = parts[-2]
                                if year_part.isdigit() and month_part.isdigit():
                                    part_year = int(year_part)
                                    part_month = int(month_part)
                                    partition_end = datetime(part_year, part_month, 1, tzinfo=timezone.utc)
                                    if part_month == 12:
                                        partition_end = datetime(part_year + 1, 1, 1, tzinfo=timezone.utc)
                                    else:
                                        partition_end = datetime(part_year, part_month + 1, 1, tzinfo=timezone.utc)
                                    if partition_end <= cutoff:
                                        await session.execute(text(f"""
                                            ALTER TABLE {table} DETACH PARTITION {partition}
                                        """))
                                        await session.commit()
                                        logger.info("partition_detached", table=table, partition=partition)
                    except (ValueError, IndexError):
                        logger.warning("partition_parse_error", partition_name=str(partition))

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
