"""
Content Calendar Manager - Content Planning and Scheduling.

Manages content calendar, schedules publications, tracks deadlines,
and optimizes content distribution across channels.

Based on: Content Marketing Best Practices + Editorial Calendar Management
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import structlog
# from airflow.models.pool import Pool
# from airflow.utils.db import DBLocks


@dataclass
class ContentItem:
    """Content item in calendar."""

    content_id: str
    title: str
    content_type: str  # blog, social, email, video, infographic
    status: str  # draft, review, scheduled, published
    author: str
    target_keyword: str | None
    scheduled_date: str  # ISO format
    publish_channel: str  # blog, facebook, instagram, linkedin, email
    priority: str  # high, medium, low
    word_count: int | None
    estimated_hours: float


@dataclass
class ChannelSchedule:
    """Publishing schedule for channel."""

    channel: str
    frequency: str  # daily, weekly, biweekly, monthly
    optimal_times: list[str]  # e.g., ["09:00", "14:00", "18:00"]
    next_slot: str  # ISO format
    capacity: int  # Posts per period
    current_load: int  # Scheduled posts


@dataclass
class ContentGap:
    """Content gap identified."""

    topic: str
    keyword: str
    priority: str  # high, medium, low
    reason: str
    suggested_type: str  # blog, video, infographic
    estimated_traffic: int


@dataclass
class DeadlineAlert:
    """Deadline alert."""

    content_id: str
    title: str
    deadline: str  # ISO format
    days_remaining: int
    status: str  # draft, review
    urgency: str  # critical, high, medium


@dataclass
class CalendarMetrics:
    """Calendar performance metrics."""

    total_items: int
    published_count: int
    scheduled_count: int
    draft_count: int
    overdue_count: int
    completion_rate: float  # %
    avg_production_time: float  # hours
    channel_distribution: dict[str, int]


@dataclass
class ContentCalendarReport:
    """Complete content calendar report."""

    period: str
    generated_at: str

    # Core sections
    calendar_items: list[ContentItem]
    channel_schedules: list[ChannelSchedule]
    content_gaps: list[ContentGap]
    deadline_alerts: list[DeadlineAlert]
    metrics: CalendarMetrics

    # Recommendations
    recommendations: list[str]


class ContentCalendarManager:
    """
    Content Calendar Manager.

    Manages content planning, scheduling, and distribution.
    """

    def __init__(self):
        """Initialize Content Calendar Manager."""
        self.logger = structlog.get_logger()

    async def get_calendar(
        self,
        period: str,
        data: dict[str, Any] | None = None,
    ) -> ContentCalendarReport:
        """
        Get content calendar for period.

        Args:
            period: Period (e.g., "2026-05-01 to 2026-05-31")
            data: Calendar data (if None, will fetch)

        Returns:
            Complete content calendar report
        """
        self.logger.info("calendar_fetch_start", period=period)

        # Fetch data if not provided
        if data is None:
            data = await self._fetch_calendar_data(period)

        # Step 1: Get calendar items
        calendar_items = await self._get_calendar_items(data)

        # Step 2: Get channel schedules
        channel_schedules = await self._get_channel_schedules(data, calendar_items)

        # Step 3: Identify content gaps
        content_gaps = await self._identify_content_gaps(data, calendar_items)

        # Step 4: Generate deadline alerts
        deadline_alerts = await self._generate_deadline_alerts(calendar_items)

        # Step 5: Calculate metrics
        metrics = await self._calculate_metrics(calendar_items)

        # Step 6: Generate recommendations
        recommendations = await self._generate_recommendations(
            calendar_items, channel_schedules, content_gaps, deadline_alerts
        )

        report = ContentCalendarReport(
            period=period,
            generated_at=datetime.now().isoformat(),
            calendar_items=calendar_items,
            channel_schedules=channel_schedules,
            content_gaps=content_gaps,
            deadline_alerts=deadline_alerts,
            metrics=metrics,
            recommendations=recommendations,
        )

        self.logger.info(
            "calendar_fetch_complete",
            items_count=len(calendar_items),
            gaps_count=len(content_gaps),
        )

        return report

    async def schedule_content(
        self,
        title: str,
        content_type: str,
        author: str,
        target_date: str,
        channel: str,
        priority: str = "medium",
        target_keyword: str | None = None,
    ) -> ContentItem:
        """
        Schedule new content item.

        Args:
            title: Content title
            content_type: Content type (blog, social, email, video)
            author: Author name
            target_date: Target publish date (ISO format)
            channel: Publish channel
            priority: Priority (high, medium, low)
            target_keyword: Target keyword (optional)

        Returns:
            Created content item
        """
        self.logger.info("content_schedule", title=title, date=target_date)

        # Estimate production time based on content type
        estimated_hours = self._estimate_production_time(content_type)

        content_item = ContentItem(
            content_id=f"content_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=title,
            content_type=content_type,
            status="draft",
            author=author,
            target_keyword=target_keyword,
            scheduled_date=target_date,
            publish_channel=channel,
            priority=priority,
            word_count=None,
            estimated_hours=estimated_hours,
        )

        return content_item

    async def _fetch_calendar_data(self, period: str) -> dict[str, Any]:
        """Fetch calendar data from content management system."""
        # Mock data for now (will integrate with real CMS)
        return {
            "items": [
                {
                    "content_id": "content_001",
                    "title": "Dental Implants Guide 2026",
                    "content_type": "blog",
                    "status": "scheduled",
                    "author": "Dr. Smith",
                    "target_keyword": "dental implants",
                    "scheduled_date": "2026-05-15T09:00:00",
                    "publish_channel": "blog",
                    "priority": "high",
                    "word_count": 2000,
                    "estimated_hours": 8.0,
                },
                {
                    "content_id": "content_002",
                    "title": "Patient Success Story",
                    "content_type": "social",
                    "status": "draft",
                    "author": "Marketing Team",
                    "target_keyword": None,
                    "scheduled_date": "2026-05-16T14:00:00",
                    "publish_channel": "instagram",
                    "priority": "medium",
                    "word_count": 150,
                    "estimated_hours": 2.0,
                },
                {
                    "content_id": "content_003",
                    "title": "Monthly Newsletter",
                    "content_type": "email",
                    "status": "review",
                    "author": "Content Team",
                    "target_keyword": None,
                    "scheduled_date": "2026-05-20T10:00:00",
                    "publish_channel": "email",
                    "priority": "high",
                    "word_count": 800,
                    "estimated_hours": 4.0,
                },
            ],
            "channels": {
                "blog": {"frequency": "weekly", "optimal_times": ["09:00", "14:00"]},
                "instagram": {"frequency": "daily", "optimal_times": ["12:00", "18:00"]},
                "email": {"frequency": "monthly", "optimal_times": ["10:00"]},
            },
            "target_keywords": ["dental implants", "teeth whitening", "orthodontics"],
        }

    async def _get_calendar_items(self, data: dict[str, Any]) -> list[ContentItem]:
        """Get calendar items from data."""
        items_data = data.get("items", [])
        items = []

        for item_data in items_data:
            items.append(
                ContentItem(
                    content_id=item_data["content_id"],
                    title=item_data["title"],
                    content_type=item_data["content_type"],
                    status=item_data["status"],
                    author=item_data["author"],
                    target_keyword=item_data.get("target_keyword"),
                    scheduled_date=item_data["scheduled_date"],
                    publish_channel=item_data["publish_channel"],
                    priority=item_data["priority"],
                    word_count=item_data.get("word_count"),
                    estimated_hours=item_data["estimated_hours"],
                )
            )

        # Sort by scheduled date
        items.sort(key=lambda x: x.scheduled_date)

        return items

    async def _get_channel_schedules(
        self, data: dict[str, Any], items: list[ContentItem]
    ) -> list[ChannelSchedule]:
        """Get channel schedules."""
        channels_data = data.get("channels", {})
        schedules = []

        for channel, config in channels_data.items():
            # Count scheduled items for this channel
            scheduled_count = sum(
                1 for item in items if item.publish_channel == channel and item.status == "scheduled"
            )

            # Calculate capacity based on frequency
            frequency = config.get("frequency", "weekly")
            if frequency == "daily":
                capacity = 30
            elif frequency == "weekly":
                capacity = 4
            elif frequency == "biweekly":
                capacity = 2
            else:  # monthly
                capacity = 1

            # Find next available slot
            optimal_times = config.get("optimal_times", ["09:00"])
            next_slot = datetime.now() + timedelta(days=1)
            next_slot = next_slot.replace(
                hour=int(optimal_times[0].split(":")[0]),
                minute=int(optimal_times[0].split(":")[1]),
            )

            schedules.append(
                ChannelSchedule(
                    channel=channel,
                    frequency=frequency,
                    optimal_times=optimal_times,
                    next_slot=next_slot.isoformat(),
                    capacity=capacity,
                    current_load=scheduled_count,
                )
            )

        return schedules

    async def _identify_content_gaps(
        self, data: dict[str, Any], items: list[ContentItem]
    ) -> list[ContentGap]:
        """Identify content gaps."""
        target_keywords = data.get("target_keywords", [])
        gaps = []

        # Check which keywords don't have content
        covered_keywords = {item.target_keyword for item in items if item.target_keyword}

        for keyword in target_keywords:
            if keyword not in covered_keywords:
                gaps.append(
                    ContentGap(
                        topic=keyword.title(),
                        keyword=keyword,
                        priority="high",
                        reason="No content targeting this keyword",
                        suggested_type="blog",
                        estimated_traffic=1000,
                    )
                )

        return gaps

    async def _generate_deadline_alerts(
        self, items: list[ContentItem]
    ) -> list[DeadlineAlert]:
        """Generate deadline alerts."""
        alerts = []
        now = datetime.now()

        for item in items:
            if item.status in ["draft", "review"]:
                scheduled = datetime.fromisoformat(item.scheduled_date)
                days_remaining = (scheduled - now).days

                # Alert if deadline is within 7 days
                if days_remaining <= 7:
                    if days_remaining <= 1:
                        urgency = "critical"
                    elif days_remaining <= 3:
                        urgency = "high"
                    else:
                        urgency = "medium"

                    alerts.append(
                        DeadlineAlert(
                            content_id=item.content_id,
                            title=item.title,
                            deadline=item.scheduled_date,
                            days_remaining=days_remaining,
                            status=item.status,
                            urgency=urgency,
                        )
                    )

        # Sort by urgency and days remaining
        urgency_order = {"critical": 0, "high": 1, "medium": 2}
        alerts.sort(key=lambda x: (urgency_order[x.urgency], x.days_remaining))

        return alerts

    async def _calculate_metrics(self, items: list[ContentItem]) -> CalendarMetrics:
        """Calculate calendar metrics."""
        total_items = len(items)
        published_count = sum(1 for item in items if item.status == "published")
        scheduled_count = sum(1 for item in items if item.status == "scheduled")
        draft_count = sum(1 for item in items if item.status == "draft")

        # Count overdue items
        now = datetime.now()
        overdue_count = sum(
            1
            for item in items
            if item.status in ["draft", "review"]
            and datetime.fromisoformat(item.scheduled_date) < now
        )

        # Completion rate
        completion_rate = (
            (published_count / total_items * 100) if total_items > 0 else 0.0
        )

        # Average production time
        items_with_time = [item for item in items if item.estimated_hours]
        avg_production_time = (
            sum(item.estimated_hours for item in items_with_time) / len(items_with_time)
            if items_with_time
            else 0.0
        )

        # Channel distribution
        channel_distribution = {}
        for item in items:
            channel = item.publish_channel
            channel_distribution[channel] = channel_distribution.get(channel, 0) + 1

        return CalendarMetrics(
            total_items=total_items,
            published_count=published_count,
            scheduled_count=scheduled_count,
            draft_count=draft_count,
            overdue_count=overdue_count,
            completion_rate=round(completion_rate, 2),
            avg_production_time=round(avg_production_time, 2),
            channel_distribution=channel_distribution,
        )

    async def _generate_recommendations(
        self,
        items: list[ContentItem],
        schedules: list[ChannelSchedule],
        gaps: list[ContentGap],
        alerts: list[DeadlineAlert],
    ) -> list[str]:
        """Generate recommendations."""
        recommendations = []

        # Deadline alerts
        critical_alerts = [a for a in alerts if a.urgency == "critical"]
        if critical_alerts:
            recommendations.append(
                f"URGENT: {len(critical_alerts)} content item(s) due within 24 hours"
            )

        # Content gaps
        high_priority_gaps = [g for g in gaps if g.priority == "high"]
        if high_priority_gaps:
            recommendations.append(
                f"Fill {len(high_priority_gaps)} high-priority content gap(s)"
            )

        # Channel capacity
        overloaded_channels = [s for s in schedules if s.current_load > s.capacity * 0.8]
        if overloaded_channels:
            channel_names = ", ".join([s.channel for s in overloaded_channels])
            recommendations.append(
                f"Reduce load on {channel_names} (near capacity)"
            )

        # Underutilized channels
        underutilized = [s for s in schedules if s.current_load < s.capacity * 0.5]
        if underutilized:
            channel_names = ", ".join([s.channel for s in underutilized])
            recommendations.append(
                f"Increase content for {channel_names} (underutilized)"
            )

        return recommendations

    def _estimate_production_time(self, content_type: str) -> float:
        """Estimate production time based on content type."""
        estimates = {
            "blog": 8.0,  # hours
            "social": 2.0,
            "email": 4.0,
            "video": 16.0,
            "infographic": 12.0,
        }
        return estimates.get(content_type, 4.0)


# ==============================================================================
# Added by Teacher Agent: calendar-manager
# ==============================================================================

async def _executable_task_instances_to_queued(self, max_tis: int, session: Any) -> list[Any]:
        """
        Find TIs that are ready for execution based on conditions.

        Conditions include:
        - pool limits
        - DAG max_active_tasks
        - executor state
        - priority
        - max active tis per DAG
        - max active tis per DAG run

        :param max_tis: Maximum number of TIs to queue in this loop.
        :return: list[airflow.models.TaskInstance]
        """
        from airflow.models.pool import Pool
        from airflow.utils.db import DBLocks

        executable_tis: list[Any] = []

        if get_dialect_name(session) == "postgresql":
            # Optimization: to avoid littering the DB errors of "ERROR: canceling statement due to lock
            # timeout", try to take out a transactional advisory lock (unlocks automatically on
            # COMMIT/ROLLBACK)
            lock_acquired = session.execute(
                text("SELECT pg_try_advisory_xact_lock(:id)").bindparams(
                    id=DBLocks.SCHEDULER_CRITICAL_SECTION.value
                )
            ).scalar()
            if lock_acquired is None:
                lock_acquired = False
            if not lock_acquired:
                # Throw an error like the one that would happen with NOWAIT
                raise OperationalError(
                    "Failed to acquire advisory lock", params=None, orig=RuntimeError("55P03")
                )

        # Get the pool settings. We get a lock on the pool rows, treating this as a "critical section"
        # Throws an exception if lock cannot be obtained, rather than blocking
        pools = Pool.slots_stats(lock_rows=True, session=session)

        # If the pools are full, there is no point doing anything!
        # If _somehow_ the pool is overfull, don't let the limit go negative - it breaks SQL
        pool_slots_free = sum(max(0, pool["open"]) for pool in pools.values())

        if pool_slots_free == 0:
            self.log.debug("All pools are full!")
            return []

        max_tis = int(min(max_tis, pool_slots_free))

        starved_pools = {pool_name for pool_name, stats in pools.items() if stats["open"] <= 0}

        # dag_id to # of running tasks and (dag_id, task_id) to # of running tasks.
        concurrency_map = ConcurrencyMap()
        concurrency_map.load(session=session)

        # Number of tasks that cannot be scheduled because of no open slot in pool
        num_starving_tasks_total = 0

        # dag and task ids that can't be queued because of concurrency limits
        starved_dags: set[str] = set()
        starved_tasks: set[tuple[str, str]] = set()
        starved_tasks_task_dagrun_concurrency: set[tuple[str, str, str]] = set()

        pool_num_starving_tasks: dict[str, int] = Counter()

        for loop_count in itertools.count(start=1):
            num_starved_pools = len(starved_pools)
            num_starved_dags = len(starved_dags)
            num_starved_tasks = len(starved_tasks)
            num_starved_tasks_task_dagrun_concurrency = len(starved_tasks_task_dagrun_concurrency)

            # This behaves the same as 'concurrency_map.load()' with the difference that
            # 'load()' executes immediately while '_get_current_dr_task_concurrency' creates a
            # subquery object that is then executed along with main query.
            # The results of 'load()' aren't used again here because by the time the main query
            # executes, there could be a change that will be ignored.
            dr_task_concurrency_subquery = _get_current_dr_task_concurrency(states=EXECUTION_STATES)

            query = (
                select(TI)
                .with_hint(TI, "USE INDEX (ti_state)", dialect_name="mysql")
                .join(TI.dag_run)
                .where(DR.state == DagRunState.RUNNING)
                .join(TI.dag_model)
                .where(~DM.is_paused)
                .where(TI.state == TaskInstanceState.SCHEDULED)
                .where(DM.bundle_name.is_not(None))
                .join(
                    dr_task_concurrency_subquery,
                    and_(
                        TI.dag_id == dr_task_concurrency_subquery.c.dag_id,
                        TI.run_id == dr_task_concurrency_subquery.c.run_id,
                    ),
                    isouter=True,
                )
                .where(
                    func.coalesce(dr_task_concurrency_subquery.c.task_per_dr_count, 0) < DM.max_active_tasks
                )
                .order_by(-TI.priority_weight, DR.logical_date, TI.map_index)
            )

            # Starvation filters should be applied before computing the row_num based on the
            # max_active_tasks limit. That way, starved dags and tasks that shouldn't run,
            # won't occupy a slot.
            if starved_pools:
                query = query.where(TI.pool.not_in(starved_pools))

            if starved_dags:
                query = query.where(TI.dag_id.not_in(starved_dags))

            if starved_tasks:
                query = query.where(tuple_(TI.dag_id, TI.task_id).not_in(starved_tasks))

            if starved_tasks_task_dagrun_concurrency:
                query = query.where(
                    tuple_(TI.dag_id, TI.run_id, TI.task_id).not_in(starved_tasks_task_dagrun_concurrency)
                )

            # Create a subquery with row numbers partitioned by dag_id and run_id.
            # Different dags can have the same run_id but
            # the dag_id combined with the run_id uniquely identify a run.
            ranked_query = (
                query.add_columns(
                    func.row_number()
                    .over(
                        partition_by=[TI.dag_id, TI.run_id],
                        order_by=[-TI.priority_weight, DR.logical_date, TI.map_index],
                    )
                    .label("row_num"),
                    DM.max_active_tasks.label("dr_max_active_tasks"),
                    # Create columns for the order_by checks here for sqlite.
                    TI.priority_weight.label("priority_weight_for_ordering"),
                    DR.logical_date.label("logical_date_for_ordering"),
                    TI.map_index.label("map_index_for_ordering"),
                )
            ).subquery()

            # Select only rows where row_number <= max_active_tasks.
            query = (
                select(TI)
                .with_hint(TI, "USE INDEX (ti_state)", dialect_name="mysql")
                .select_from(ranked_query)
                .join(
                    TI,
                    (TI.dag_id == ranked_query.c.dag_id)
                    & (TI.task_id == ranked_query.c.task_id)
                    & (TI.run_id == ranked_query.c.run_id)
                    & (TI.map_index == ranked_query.c.map_index),
                )
                .where(ranked_query.c.row_num <= ranked_query.c.dr_max_active_tasks)
                # Add the order_by columns from the ranked query for sqlite.
                .order_by(
                    -ranked_query.c.priority_weight_for_ordering,
                    ranked_query.c.logical_date_for_ordering,
                    ranked_query.c.map_index_for_ordering,
                )
                .options(selectinload(TI.dag_model))
            )

            query = query.limit(max_tis)

            timer = stats.timer("scheduler.critical_section_query_duration")
            timer.start()

            try:
                locked_query = with_row_locks(query, of=TI, session=session, skip_locked=True)
                task_instances_to_examine = session.scalars(locked_query).all()

                if self.log.isEnabledFor(logging.DEBUG):
                    self.log.debug("Length of the tis to examine is %d", len(task_instances_to_examine))
                    self.log.debug(
                        "TaskInstance selection is: %s",
                        dict(Counter(ti.dag_id for ti in task_instances_to_examine)),
                    )

                timer.stop(send=True)
            except OperationalError as e:
                timer.stop(send=False)
                raise e

            # TODO[HA]: This was wrong before anyway, as it only looked at a sub-set of dags, not everything.
            # stats.gauge('scheduler.tasks.pending', len(task_instances_to_examine))

            if not task_instances_to_examine:
                self.log.debug("No tasks to consider for execution.")
                break

            # Put one task instance on each line
            task_instance_str = "\n".join(f"\t{x!r}" for x in task_instances_to_examine)
            self.log.info("%s tasks up for execution:\n%s", len(task_instances_to_examine), task_instance_str)

            dag_id_to_team_name: dict[str, str | None] = {}
            if self._multi_team:
                # Batch query to resolve team names for all DAG IDs to optimize performance
                # Instead of individual queries in _try_to_load_executor(), resolve all team names upfront
                unique_dag_ids = {ti.dag_id for ti in task_instances_to_examine}
                dag_id_to_team_name = self._get_team_names_for_dag_ids(unique_dag_ids, session)
                self.log.debug(
                    "Batch resolved team names for %d unique DAG IDs in scheduling loop: %s",
                    len(unique_dag_ids),
                    list(unique_dag_ids),
                )

            executor_slots_available: dict[ExecutorName, int] = {}
            # First get a mapping of executor names to slots they have available
            for executor in self.executors:
                if TYPE_CHECKING:
                    # All executors should have a name if they are initted from the executor_loader.
                    # But we need to check for None to make mypy happy.
                    assert executor.name
                executor_slots_available[executor.name] = executor.slots_available

            for task_instance in task_instances_to_examine:
                pool_name = task_instance.pool

                pool_stats = await pools.get(pool_name)
                if not pool_stats:
                    self.log.warning("Tasks using non-existent pool '%s' will not be scheduled", pool_name)
                    starved_pools.add(pool_name)
                    continue

                # Make sure to emit metrics if pool has no starving tasks
                pool_num_starving_tasks.setdefault(pool_name, 0)

                pool_total = pool_stats["total"]
                open_slots = pool_stats["open"]

                if open_slots <= 0:
                    self.log.info(
                        "Not scheduling since there are %s open slots in pool %s", open_slots, pool_name
                    )
                    # Can't schedule any more since there are no more open slots.
                    pool_num_starving_tasks[pool_name] += 1
                    num_starving_tasks_total += 1
                    starved_pools.add(pool_name)
                    continue

                if task_instance.pool_slots > pool_total:
                    self.log.warning(
                        "Not executing %s. Requested pool slots (%s) are greater than "
                        "total pool slots: '%s' for pool: %s.",
                        task_instance,
                        task_instance.pool_slots,
                        pool_total,
                        pool_name,
                    )

                    pool_num_starving_tasks[pool_name] += 1
                    num_starving_tasks_total += 1
                    starved_tasks.add((task_instance.dag_id, task_instance.task_id))
                    continue

                if task_instance.pool_slots > open_slots:
                    self.log.info(
                        "Not executing %s since it requires %s slots "
                        "but there are %s open slots in the pool %s.",
                        task_instance,
                        task_instance.pool_slots,
                        open_slots,
                        pool_name,
                    )
                    pool_num_starving_tasks[pool_name] += 1
                    num_starving_tasks_total += 1
                    starved_tasks.add((task_instance.dag_id, task_instance.task_id))
                    # Though we can execute tasks with lower priority if there's enough room
                    continue

                # Check to make sure that the task max_active_tasks of the DAG hasn't been
                # reached.
                dag_id = task_instance.dag_id
                dag_run_key = (dag_id, task_instance.run_id)
                current_active_tasks_per_dag_run = concurrency_map.dag_run_active_tasks_map[dag_run_key]
                dag_max_active_tasks = task_instance.dag_model.max_active_tasks
                self.log.info(
                    "DAG %s has %s/%s running and queued tasks",
                    dag_id,
                    current_active_tasks_per_dag_run,
                    dag_max_active_tasks,
                )
                if current_active_tasks_per_dag_run >= dag_max_active_tasks:
                    self.log.info(
                        "Not executing %s since the number of tasks running or queued "
                        "from DAG %s is >= to the DAG's max_active_tasks limit of %s",
                        task_instance,
                        dag_id,
                        dag_max_active_tasks,
                    )
                    starved_dags.add(dag_id)
                    continue

                if task_instance.dag_model.has_task_concurrency_limits:
                    # Many dags don't have a task_concurrency, so where we can avoid loading the full
                    # serialized DAG the better.
                    serialized_dag = self.scheduler_dag_bag.get_dag_for_run(
                        dag_run=task_instance.dag_run, session=session
                    )
                    # If the dag is missing, fail the task and continue to the next task.
                    if not serialized_dag:
                        self.log.error(
                            "DAG '%s' for task instance %s not found in serialized_dag table",
                            dag_id,
                            task_instance,
                        )
                        session.execute(
                            update(TI)
                            .where(TI.dag_id == dag_id, TI.state == TaskInstanceState.SCHEDULED)
                            .values(state=TaskInstanceState.FAILED)
                            .execution_options(synchronize_session="fetch")
                        )
                        continue

                    task_concurrency_limit: int | None = None
                    if serialized_dag.has_task(task_instance.task_id):
                        task_concurrency_limit = serialized_dag.get_task(
                            task_instance.task_id
                        ).max_active_tis_per_dag

                    if task_concurrency_limit is not None:
                        current_task_concurrency = concurrency_map.task_concurrency_map[
                            (task_instance.dag_id, task_instance.task_id)
                        ]

                        if current_task_concurrency >= task_concurrency_limit:
                            self.log.info(
                                "Not executing %s since the task concurrency for this task has been reached.",
                                task_instance,
                            )
                            starved_tasks.add((task_instance.dag_id, task_instance.task_id))
                            continue

                    task_dagrun_concurrency_limit: int | None = None
                    if serialized_dag.has_task(task_instance.task_id):
                        task_dagrun_concurrency_limit = serialized_dag.get_task(
                            task_instance.task_id
                        ).max_active_tis_per_dagrun

                    if task_dagrun_concurrency_limit is not None:
                        current_task_dagrun_concurrency = concurrency_map.task_dagrun_concurrency_map[
                            (task_instance.dag_id, task_instance.run_id, task_instance.task_id)
                        ]

                        if current_task_dagrun_concurrency >= task_dagrun_concurrency_limit:
                            self.log.info(
                                "Not executing %s since the task concurrency per DAG run for"
                                " this task has been reached.",
                                task_instance,
                            )
                            starved_tasks_task_dagrun_concurrency.add(
                                (
                                    task_instance.dag_id,
                                    task_instance.run_id,
                                    task_instance.task_id,
                                )
                            )
                            continue

                if executor_obj := self._try_to_load_executor(
                    task_instance, session, team_name=await dag_id_to_team_name.get(task_instance.dag_id, NOTSET)
                ):
                    if TYPE_CHECKING:
                        # All executors should have a name if they are initted from the executor_loader.
                        # But we need to check for None to make mypy happy.
                        assert executor_obj.name

                    if executor_slots_available[executor_obj.name] <= 0:
                        self.log.debug(
                            "Not scheduling %s since its executor %s does not currently have any more "
                            "available slots",
                            task_instance.task_id,
                            executor_obj.name,
                        )
                        starved_tasks.add((task_instance.dag_id, task_instance.task_id))
                        continue
                    executor_slots_available[executor_obj.name] -= 1
                else:
                    # This is a defensive guard for if we happen to have a task who's executor cannot be
                    # found. The check in the dag parser should make this not realistically possible but the
                    # loader can fail if some direct DB modification has happened or another as yet unknown
                    # edge case. _try_to_load_executor will log an error message explaining the executor
                    # cannot be found.
                    starved_tasks.add((task_instance.dag_id, task_instance.task_id))
                    continue

                executable_tis.append(task_instance)
                open_slots -= task_instance.pool_slots
                concurrency_map.dag_run_active_tasks_map[dag_run_key] += 1
                concurrency_map.task_concurrency_map[(task_instance.dag_id, task_instance.task_id)] += 1
                concurrency_map.task_dagrun_concurrency_map[
                    (task_instance.dag_id, task_instance.run_id, task_instance.task_id)
                ] += 1

                pool_stats["open"] = open_slots

            is_done = executable_tis or len(task_instances_to_examine) < max_tis
            # Check this to avoid accidental infinite loops
            found_new_filters = (
                len(starved_pools) > num_starved_pools
                or len(starved_dags) > num_starved_dags
                or len(starved_tasks) > num_starved_tasks
                or len(starved_tasks_task_dagrun_concurrency) > num_starved_tasks_task_dagrun_concurrency
            )

            if is_done or not found_new_filters:
                break

            self.log.info(
                "Found no task instances to queue on query iteration %s "
                "but there could be more candidate task instances to check.",
                loop_count,
            )

        for pool_name, num_starving_tasks in pool_num_starving_tasks.items():
            stats.gauge(
                "pool.starving_tasks",
                num_starving_tasks,
                tags={"pool_name": pool_name},
            )

        stats.gauge("scheduler.tasks.starving", num_starving_tasks_total)
        stats.gauge("scheduler.tasks.executable", len(executable_tis))

        if executable_tis:
            task_instance_str = "\n".join(
                f"\t{x!r} (id={x.id}, try_number={x.try_number})" for x in executable_tis
            )
            self.log.info(
                "Setting the following tasks to queued state (scheduler job_id=%s):\n%s",
                self.job.id,
                task_instance_str,
            )

            # set TIs to queued state
            filter_for_tis = TI.filter_for_tis(executable_tis)
            if filter_for_tis is None:
                return []

            queued_values: dict[str, Any] = {
                "state": TaskInstanceState.QUEUED,
                "queued_dttm": timezone.utcnow(),
                "queued_by_job_id": self.job.id,
            }

            # Pre-assign external_executor_id atomically with the QUEUED state so it
            # survives a scheduler crash. Only done when an executor opts in via
            # pre_assigns_external_executor_id (e.g. CeleryExecutor uses it as the
            # Celery task_id passed to apply_async). In mixed-executor deployments,
            # a CASE expression limits the UUID to TIs targeting an opt-in executor.
            pre_assign_executors = {e for e in self.executors if e.pre_assigns_external_executor_id}
            if pre_assign_executors == set(self.executors):
                # All executors opt in — unconditional UUID for every TI.
                queued_values["external_executor_id"] = random_db_uuid()
            elif pre_assign_executors:
                # Mixed — only TIs routed to an opt-in executor get a UUID.
                opt_in_names: set[str] = set()
                default_opts_in = self.executor in pre_assign_executors
                for exc in pre_assign_executors:
                    if exc.name:
                        if exc.name.alias:
                            opt_in_names.add(exc.name.alias)
                        opt_in_names.add(exc.name.module_path)
                whens = []
                if opt_in_names:
                    whens.append((TI.executor.in_(opt_in_names), random_db_uuid()))
                if default_opts_in:
                    whens.append((TI.executor.is_(None), random_db_uuid()))
                if whens:
                    queued_values["external_executor_id"] = case(*whens, else_=TI.external_executor_id)

            queued_update = (
                update(TI)
                .where(filter_for_tis)
                .values(**queued_values)
                .execution_options(synchronize_session=False)
            )

            if pre_assign_executors:
                # Read the DB-generated UUIDs back onto the in-memory objects so the
                # workload DTO carries them through to send_workload_to_executor (the
                # objects are about to be detached by make_transient). Use RETURNING
                # where supported (PostgreSQL); fall back to a SELECT for MySQL and
                # SQLite (RETURNING requires SQLite 3.35+ which isn't guaranteed).
                if get_dialect_name(session) == "postgresql":
                    result = session.execute(queued_update.returning(TI.id, TI.external_executor_id))
                    id_map = {row[0]: row[1] for row in result}
                else:
                    session.execute(queued_update)
                    id_rows = session.execute(
                        select(TI.id, TI.external_executor_id).where(filter_for_tis)
                    ).all()
                    id_map = {row[0]: row[1] for row in id_rows}
                for ti in executable_tis:
                    ti.external_executor_id = await id_map.get(ti.id)
            else:
                session.execute(queued_update)

            for ti in executable_tis:
                ti.emit_state_change_metric(TaskInstanceState.QUEUED)

        for ti in executable_tis:
            make_transient(ti)
        return executable_tis

# ==============================================================================
# Added by Teacher Agent: calendar-manager
# ==============================================================================

async def _executable_task_instances_to_queued(self, max_tis: int, session: Any) -> list[Any]:
        """
        Find TIs that are ready for execution based on conditions.

        Conditions include:
        - pool limits
        - DAG max_active_tasks
        - executor state
        - priority
        - max active tis per DAG
        - max active tis per DAG run

        :param max_tis: Maximum number of TIs to queue in this loop.
        :return: list[airflow.models.TaskInstance]
        """
        from airflow.models.pool import Pool
        from airflow.utils.db import DBLocks

        executable_tis: list[Any] = []

        if get_dialect_name(session) == "postgresql":
            # Optimization: to avoid littering the DB errors of "ERROR: canceling statement due to lock
            # timeout", try to take out a transactional advisory lock (unlocks automatically on
            # COMMIT/ROLLBACK)
            lock_acquired = session.execute(
                text("SELECT pg_try_advisory_xact_lock(:id)").bindparams(
                    id=DBLocks.SCHEDULER_CRITICAL_SECTION.value
                )
            ).scalar()
            if lock_acquired is None:
                lock_acquired = False
            if not lock_acquired:
                # Throw an error like the one that would happen with NOWAIT
                raise OperationalError(
                    "Failed to acquire advisory lock", params=None, orig=RuntimeError("55P03")
                )

        # Get the pool settings. We get a lock on the pool rows, treating this as a "critical section"
        # Throws an exception if lock cannot be obtained, rather than blocking
        pools = Pool.slots_stats(lock_rows=True, session=session)

        # If the pools are full, there is no point doing anything!
        # If _somehow_ the pool is overfull, don't let the limit go negative - it breaks SQL
        pool_slots_free = sum(max(0, pool["open"]) for pool in pools.values())

        if pool_slots_free == 0:
            self.log.debug("All pools are full!")
            return []

        max_tis = int(min(max_tis, pool_slots_free))

        starved_pools = {pool_name for pool_name, stats in pools.items() if stats["open"] <= 0}

        # dag_id to # of running tasks and (dag_id, task_id) to # of running tasks.
        concurrency_map = ConcurrencyMap()
        concurrency_map.load(session=session)

        # Number of tasks that cannot be scheduled because of no open slot in pool
        num_starving_tasks_total = 0

        # dag and task ids that can't be queued because of concurrency limits
        starved_dags: set[str] = set()
        starved_tasks: set[tuple[str, str]] = set()
        starved_tasks_task_dagrun_concurrency: set[tuple[str, str, str]] = set()

        pool_num_starving_tasks: dict[str, int] = Counter()

        for loop_count in itertools.count(start=1):
            num_starved_pools = len(starved_pools)
            num_starved_dags = len(starved_dags)
            num_starved_tasks = len(starved_tasks)
            num_starved_tasks_task_dagrun_concurrency = len(starved_tasks_task_dagrun_concurrency)

            # This behaves the same as 'concurrency_map.load()' with the difference that
            # 'load()' executes immediately while '_get_current_dr_task_concurrency' creates a
            # subquery object that is then executed along with main query.
            # The results of 'load()' aren't used again here because by the time the main query
            # executes, there could be a change that will be ignored.
            dr_task_concurrency_subquery = _get_current_dr_task_concurrency(states=EXECUTION_STATES)

            query = (
                select(TI)
                .with_hint(TI, "USE INDEX (ti_state)", dialect_name="mysql")
                .join(TI.dag_run)
                .where(DR.state == DagRunState.RUNNING)
                .join(TI.dag_model)
                .where(~DM.is_paused)
                .where(TI.state == TaskInstanceState.SCHEDULED)
                .where(DM.bundle_name.is_not(None))
                .join(
                    dr_task_concurrency_subquery,
                    and_(
                        TI.dag_id == dr_task_concurrency_subquery.c.dag_id,
                        TI.run_id == dr_task_concurrency_subquery.c.run_id,
                    ),
                    isouter=True,
                )
                .where(
                    func.coalesce(dr_task_concurrency_subquery.c.task_per_dr_count, 0) < DM.max_active_tasks
                )
                .order_by(-TI.priority_weight, DR.logical_date, TI.map_index)
            )

            # Starvation filters should be applied before computing the row_num based on the
            # max_active_tasks limit. That way, starved dags and tasks that shouldn't run,
            # won't occupy a slot.
            if starved_pools:
                query = query.where(TI.pool.not_in(starved_pools))

            if starved_dags:
                query = query.where(TI.dag_id.not_in(starved_dags))

            if starved_tasks:
                query = query.where(tuple_(TI.dag_id, TI.task_id).not_in(starved_tasks))

            if starved_tasks_task_dagrun_concurrency:
                query = query.where(
                    tuple_(TI.dag_id, TI.run_id, TI.task_id).not_in(starved_tasks_task_dagrun_concurrency)
                )

            # Create a subquery with row numbers partitioned by dag_id and run_id.
            # Different dags can have the same run_id but
            # the dag_id combined with the run_id uniquely identify a run.
            ranked_query = (
                query.add_columns(
                    func.row_number()
                    .over(
                        partition_by=[TI.dag_id, TI.run_id],
                        order_by=[-TI.priority_weight, DR.logical_date, TI.map_index],
                    )
                    .label("row_num"),
                    DM.max_active_tasks.label("dr_max_active_tasks"),
                    # Create columns for the order_by checks here for sqlite.
                    TI.priority_weight.label("priority_weight_for_ordering"),
                    DR.logical_date.label("logical_date_for_ordering"),
                    TI.map_index.label("map_index_for_ordering"),
                )
            ).subquery()

            # Select only rows where row_number <= max_active_tasks.
            query = (
                select(TI)
                .with_hint(TI, "USE INDEX (ti_state)", dialect_name="mysql")
                .select_from(ranked_query)
                .join(
                    TI,
                    (TI.dag_id == ranked_query.c.dag_id)
                    & (TI.task_id == ranked_query.c.task_id)
                    & (TI.run_id == ranked_query.c.run_id)
                    & (TI.map_index == ranked_query.c.map_index),
                )
                .where(ranked_query.c.row_num <= ranked_query.c.dr_max_active_tasks)
                # Add the order_by columns from the ranked query for sqlite.
                .order_by(
                    -ranked_query.c.priority_weight_for_ordering,
                    ranked_query.c.logical_date_for_ordering,
                    ranked_query.c.map_index_for_ordering,
                )
                .options(selectinload(TI.dag_model))
            )

            query = query.limit(max_tis)

            timer = stats.timer("scheduler.critical_section_query_duration")
            timer.start()

            try:
                locked_query = with_row_locks(query, of=TI, session=session, skip_locked=True)
                task_instances_to_examine = session.scalars(locked_query).all()

                if self.log.isEnabledFor(logging.DEBUG):
                    self.log.debug("Length of the tis to examine is %d", len(task_instances_to_examine))
                    self.log.debug(
                        "TaskInstance selection is: %s",
                        dict(Counter(ti.dag_id for ti in task_instances_to_examine)),
                    )

                timer.stop(send=True)
            except OperationalError as e:
                timer.stop(send=False)
                raise e

            # TODO[HA]: This was wrong before anyway, as it only looked at a sub-set of dags, not everything.
            # stats.gauge('scheduler.tasks.pending', len(task_instances_to_examine))

            if not task_instances_to_examine:
                self.log.debug("No tasks to consider for execution.")
                break

            # Put one task instance on each line
            task_instance_str = "\n".join(f"\t{x!r}" for x in task_instances_to_examine)
            self.log.info("%s tasks up for execution:\n%s", len(task_instances_to_examine), task_instance_str)

            dag_id_to_team_name: dict[str, str | None] = {}
            if self._multi_team:
                # Batch query to resolve team names for all DAG IDs to optimize performance
                # Instead of individual queries in _try_to_load_executor(), resolve all team names upfront
                unique_dag_ids = {ti.dag_id for ti in task_instances_to_examine}
                dag_id_to_team_name = self._get_team_names_for_dag_ids(unique_dag_ids, session)
                self.log.debug(
                    "Batch resolved team names for %d unique DAG IDs in scheduling loop: %s",
                    len(unique_dag_ids),
                    list(unique_dag_ids),
                )

            executor_slots_available: dict[ExecutorName, int] = {}
            # First get a mapping of executor names to slots they have available
            for executor in self.executors:
                if TYPE_CHECKING:
                    # All executors should have a name if they are initted from the executor_loader.
                    # But we need to check for None to make mypy happy.
                    assert executor.name
                executor_slots_available[executor.name] = executor.slots_available

            for task_instance in task_instances_to_examine:
                pool_name = task_instance.pool

                pool_stats = await pools.get(pool_name)
                if not pool_stats:
                    self.log.warning("Tasks using non-existent pool '%s' will not be scheduled", pool_name)
                    starved_pools.add(pool_name)
                    continue

                # Make sure to emit metrics if pool has no starving tasks
                pool_num_starving_tasks.setdefault(pool_name, 0)

                pool_total = pool_stats["total"]
                open_slots = pool_stats["open"]

                if open_slots <= 0:
                    self.log.info(
                        "Not scheduling since there are %s open slots in pool %s", open_slots, pool_name
                    )
                    # Can't schedule any more since there are no more open slots.
                    pool_num_starving_tasks[pool_name] += 1
                    num_starving_tasks_total += 1
                    starved_pools.add(pool_name)
                    continue

                if task_instance.pool_slots > pool_total:
                    self.log.warning(
                        "Not executing %s. Requested pool slots (%s) are greater than "
                        "total pool slots: '%s' for pool: %s.",
                        task_instance,
                        task_instance.pool_slots,
                        pool_total,
                        pool_name,
                    )

                    pool_num_starving_tasks[pool_name] += 1
                    num_starving_tasks_total += 1
                    starved_tasks.add((task_instance.dag_id, task_instance.task_id))
                    continue

                if task_instance.pool_slots > open_slots:
                    self.log.info(
                        "Not executing %s since it requires %s slots "
                        "but there are %s open slots in the pool %s.",
                        task_instance,
                        task_instance.pool_slots,
                        open_slots,
                        pool_name,
                    )
                    pool_num_starving_tasks[pool_name] += 1
                    num_starving_tasks_total += 1
                    starved_tasks.add((task_instance.dag_id, task_instance.task_id))
                    # Though we can execute tasks with lower priority if there's enough room
                    continue

                # Check to make sure that the task max_active_tasks of the DAG hasn't been
                # reached.
                dag_id = task_instance.dag_id
                dag_run_key = (dag_id, task_instance.run_id)
                current_active_tasks_per_dag_run = concurrency_map.dag_run_active_tasks_map[dag_run_key]
                dag_max_active_tasks = task_instance.dag_model.max_active_tasks
                self.log.info(
                    "DAG %s has %s/%s running and queued tasks",
                    dag_id,
                    current_active_tasks_per_dag_run,
                    dag_max_active_tasks,
                )
                if current_active_tasks_per_dag_run >= dag_max_active_tasks:
                    self.log.info(
                        "Not executing %s since the number of tasks running or queued "
                        "from DAG %s is >= to the DAG's max_active_tasks limit of %s",
                        task_instance,
                        dag_id,
                        dag_max_active_tasks,
                    )
                    starved_dags.add(dag_id)
                    continue

                if task_instance.dag_model.has_task_concurrency_limits:
                    # Many dags don't have a task_concurrency, so where we can avoid loading the full
                    # serialized DAG the better.
                    serialized_dag = self.scheduler_dag_bag.get_dag_for_run(
                        dag_run=task_instance.dag_run, session=session
                    )
                    # If the dag is missing, fail the task and continue to the next task.
                    if not serialized_dag:
                        self.log.error(
                            "DAG '%s' for task instance %s not found in serialized_dag table",
                            dag_id,
                            task_instance,
                        )
                        session.execute(
                            update(TI)
                            .where(TI.dag_id == dag_id, TI.state == TaskInstanceState.SCHEDULED)
                            .values(state=TaskInstanceState.FAILED)
                            .execution_options(synchronize_session="fetch")
                        )
                        continue

                    task_concurrency_limit: int | None = None
                    if serialized_dag.has_task(task_instance.task_id):
                        task_concurrency_limit = serialized_dag.get_task(
                            task_instance.task_id
                        ).max_active_tis_per_dag

                    if task_concurrency_limit is not None:
                        current_task_concurrency = concurrency_map.task_concurrency_map[
                            (task_instance.dag_id, task_instance.task_id)
                        ]

                        if current_task_concurrency >= task_concurrency_limit:
                            self.log.info(
                                "Not executing %s since the task concurrency for this task has been reached.",
                                task_instance,
                            )
                            starved_tasks.add((task_instance.dag_id, task_instance.task_id))
                            continue

                    task_dagrun_concurrency_limit: int | None = None
                    if serialized_dag.has_task(task_instance.task_id):
                        task_dagrun_concurrency_limit = serialized_dag.get_task(
                            task_instance.task_id
                        ).max_active_tis_per_dagrun

                    if task_dagrun_concurrency_limit is not None:
                        current_task_dagrun_concurrency = concurrency_map.task_dagrun_concurrency_map[
                            (task_instance.dag_id, task_instance.run_id, task_instance.task_id)
                        ]

                        if current_task_dagrun_concurrency >= task_dagrun_concurrency_limit:
                            self.log.info(
                                "Not executing %s since the task concurrency per DAG run for"
                                " this task has been reached.",
                                task_instance,
                            )
                            starved_tasks_task_dagrun_concurrency.add(
                                (
                                    task_instance.dag_id,
                                    task_instance.run_id,
                                    task_instance.task_id,
                                )
                            )
                            continue

                if executor_obj := self._try_to_load_executor(
                    task_instance, session, team_name=await dag_id_to_team_name.get(task_instance.dag_id, NOTSET)
                ):
                    if TYPE_CHECKING:
                        # All executors should have a name if they are initted from the executor_loader.
                        # But we need to check for None to make mypy happy.
                        assert executor_obj.name

                    if executor_slots_available[executor_obj.name] <= 0:
                        self.log.debug(
                            "Not scheduling %s since its executor %s does not currently have any more "
                            "available slots",
                            task_instance.task_id,
                            executor_obj.name,
                        )
                        starved_tasks.add((task_instance.dag_id, task_instance.task_id))
                        continue
                    executor_slots_available[executor_obj.name] -= 1
                else:
                    # This is a defensive guard for if we happen to have a task who's executor cannot be
                    # found. The check in the dag parser should make this not realistically possible but the
                    # loader can fail if some direct DB modification has happened or another as yet unknown
                    # edge case. _try_to_load_executor will log an error message explaining the executor
                    # cannot be found.
                    starved_tasks.add((task_instance.dag_id, task_instance.task_id))
                    continue

                executable_tis.append(task_instance)
                open_slots -= task_instance.pool_slots
                concurrency_map.dag_run_active_tasks_map[dag_run_key] += 1
                concurrency_map.task_concurrency_map[(task_instance.dag_id, task_instance.task_id)] += 1
                concurrency_map.task_dagrun_concurrency_map[
                    (task_instance.dag_id, task_instance.run_id, task_instance.task_id)
                ] += 1

                pool_stats["open"] = open_slots

            is_done = executable_tis or len(task_instances_to_examine) < max_tis
            # Check this to avoid accidental infinite loops
            found_new_filters = (
                len(starved_pools) > num_starved_pools
                or len(starved_dags) > num_starved_dags
                or len(starved_tasks) > num_starved_tasks
                or len(starved_tasks_task_dagrun_concurrency) > num_starved_tasks_task_dagrun_concurrency
            )

            if is_done or not found_new_filters:
                break

            self.log.info(
                "Found no task instances to queue on query iteration %s "
                "but there could be more candidate task instances to check.",
                loop_count,
            )

        for pool_name, num_starving_tasks in pool_num_starving_tasks.items():
            stats.gauge(
                "pool.starving_tasks",
                num_starving_tasks,
                tags={"pool_name": pool_name},
            )

        stats.gauge("scheduler.tasks.starving", num_starving_tasks_total)
        stats.gauge("scheduler.tasks.executable", len(executable_tis))

        if executable_tis:
            task_instance_str = "\n".join(
                f"\t{x!r} (id={x.id}, try_number={x.try_number})" for x in executable_tis
            )
            self.log.info(
                "Setting the following tasks to queued state (scheduler job_id=%s):\n%s",
                self.job.id,
                task_instance_str,
            )

            # set TIs to queued state
            filter_for_tis = TI.filter_for_tis(executable_tis)
            if filter_for_tis is None:
                return []

            queued_values: dict[str, Any] = {
                "state": TaskInstanceState.QUEUED,
                "queued_dttm": timezone.utcnow(),
                "queued_by_job_id": self.job.id,
            }

            # Pre-assign external_executor_id atomically with the QUEUED state so it
            # survives a scheduler crash. Only done when an executor opts in via
            # pre_assigns_external_executor_id (e.g. CeleryExecutor uses it as the
            # Celery task_id passed to apply_async). In mixed-executor deployments,
            # a CASE expression limits the UUID to TIs targeting an opt-in executor.
            pre_assign_executors = {e for e in self.executors if e.pre_assigns_external_executor_id}
            if pre_assign_executors == set(self.executors):
                # All executors opt in — unconditional UUID for every TI.
                queued_values["external_executor_id"] = random_db_uuid()
            elif pre_assign_executors:
                # Mixed — only TIs routed to an opt-in executor get a UUID.
                opt_in_names: set[str] = set()
                default_opts_in = self.executor in pre_assign_executors
                for exc in pre_assign_executors:
                    if exc.name:
                        if exc.name.alias:
                            opt_in_names.add(exc.name.alias)
                        opt_in_names.add(exc.name.module_path)
                whens = []
                if opt_in_names:
                    whens.append((TI.executor.in_(opt_in_names), random_db_uuid()))
                if default_opts_in:
                    whens.append((TI.executor.is_(None), random_db_uuid()))
                if whens:
                    queued_values["external_executor_id"] = case(*whens, else_=TI.external_executor_id)

            queued_update = (
                update(TI)
                .where(filter_for_tis)
                .values(**queued_values)
                .execution_options(synchronize_session=False)
            )

            if pre_assign_executors:
                # Read the DB-generated UUIDs back onto the in-memory objects so the
                # workload DTO carries them through to send_workload_to_executor (the
                # objects are about to be detached by make_transient). Use RETURNING
                # where supported (PostgreSQL); fall back to a SELECT for MySQL and
                # SQLite (RETURNING requires SQLite 3.35+ which isn't guaranteed).
                if get_dialect_name(session) == "postgresql":
                    result = session.execute(queued_update.returning(TI.id, TI.external_executor_id))
                    id_map = {row[0]: row[1] for row in result}
                else:
                    session.execute(queued_update)
                    id_rows = session.execute(
                        select(TI.id, TI.external_executor_id).where(filter_for_tis)
                    ).all()
                    id_map = {row[0]: row[1] for row in id_rows}
                for ti in executable_tis:
                    ti.external_executor_id = await id_map.get(ti.id)
            else:
                session.execute(queued_update)

            for ti in executable_tis:
                ti.emit_state_change_metric(TaskInstanceState.QUEUED)

        for ti in executable_tis:
            make_transient(ti)
        return executable_tis