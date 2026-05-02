"""Base Magister class - domain specialist with hybrid search"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import text

from meai.agents.base_agent import Agent, Task, TaskResult, Feedback
from meai.events.event_bus import EventBus, Event
from meai.storage.database import Database


class BaseMagister(Agent):
    """Base Magister - domain specialist with hybrid search

    Hybrid Search Strategy:
    1. Search local Obsidian vault first (fastest)
    2. If not found → query Teacher (Qdrant)
    3. If Teacher doesn't have → request Researcher
    4. Cache results locally for future queries

    Each Magister specializes in a domain (SEO, Content, Ads, etc.)
    and maintains local knowledge in Obsidian vault.
    """

    def __init__(
        self,
        agent_id: str,
        magister_type: str,
        domain: str,
        event_bus: EventBus,
        vault_path: Path,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
    ):
        """Initialize Base Magister

        Args:
            agent_id: Unique agent identifier
            magister_type: Type of magister (seo, content, ads, etc.)
            domain: Knowledge domain (seo, content, ads, etc.)
            event_bus: Event bus for communication
            vault_path: Path to Obsidian vault
            database_url: Database URL for agent state
        """
        super().__init__(
            agent_id=agent_id,
            agent_type=f"{magister_type}-magister",
            database_url=database_url,
            vault_path=str(vault_path),
        )

        self.magister_type = magister_type
        self.domain = domain
        self.vault_path = Path(vault_path)

        # Replace Agent's event_bus with shared one
        self.event_bus = event_bus

        # Cache settings
        self.cache_ttl_hours = 24  # Cache for 24 hours

        # Teacher agent ID
        self.teacher_id = "teacher-1"

    async def initialize(self) -> None:
        """Initialize Magister"""
        # Initialize database and vault
        await self.db.connect()
        await self.vault.initialize()

        # Initialize shared event_bus (already set in __init__)
        if not self.event_bus._initialized:
            await self.event_bus.initialize()

        # Create base Agent tables
        await self._create_tables()

        # Create Magister-specific tables
        await self._create_magister_tables()

        # Create vault structure
        await self._create_vault_structure()

        # Subscribe to events
        await self._subscribe_to_events()

    async def _create_magister_tables(self) -> None:
        """Create Magister-specific database tables"""
        async with self.db.session() as session:
            # Tasks table
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS magister_tasks (
                    id TEXT PRIMARY KEY,
                    magister_id TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP
                )
                """)
            )

            # Knowledge cache table
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS magister_knowledge_cache (
                    id TEXT PRIMARY KEY,
                    magister_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    quality_score REAL,
                    metadata TEXT,
                    cached_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP NOT NULL
                )
                """)
            )

            # Queries table
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS magister_queries (
                    id TEXT PRIMARY KEY,
                    magister_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    result_source TEXT NOT NULL,
                    results_count INTEGER NOT NULL,
                    queried_at TIMESTAMP NOT NULL
                )
                """)
            )

            # Decisions table
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS magister_decisions (
                    id TEXT PRIMARY KEY,
                    magister_id TEXT NOT NULL,
                    decision_type TEXT NOT NULL,
                    context TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    rationale TEXT,
                    decided_at TIMESTAMP NOT NULL
                )
                """)
            )

            # Errors table (NEW)
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS magister_errors (
                    id TEXT PRIMARY KEY,
                    magister_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    stack_trace TEXT,
                    occurred_at TIMESTAMP NOT NULL
                )
                """)
            )

            await session.commit()

    async def _create_vault_structure(self) -> None:
        """Create Obsidian vault structure"""
        # Create vault directories
        (self.vault_path / "knowledge").mkdir(parents=True, exist_ok=True)
        (self.vault_path / "tasks").mkdir(parents=True, exist_ok=True)
        (self.vault_path / "decisions").mkdir(parents=True, exist_ok=True)

        # Create .obsidian folder for Obsidian recognition
        obsidian_path = self.vault_path / ".obsidian"
        obsidian_path.mkdir(parents=True, exist_ok=True)

        # Create app.json
        app_json = obsidian_path / "app.json"
        if not app_json.exists():
            app_json.write_text(json.dumps({
                "name": f"{self.magister_type.upper()} Magister Vault"
            }, indent=2))

        # Create appearance.json
        appearance_json = obsidian_path / "appearance.json"
        if not appearance_json.exists():
            appearance_json.write_text(json.dumps({
                "attachmentFolderPath": "assets"
            }, indent=2))

        # Create index file
        index_path = self.vault_path / "INDEX.md"
        if not index_path.exists():
            index_content = f"""# {self.magister_type.upper()} Magister

**Domain:** {self.domain}
**Agent ID:** {self.agent_id}
**Created:** {datetime.now(timezone.utc).isoformat()}

## Structure

- [[knowledge/]] — Cached knowledge from Teacher and Researcher
- [[tasks/]] — Task execution logs
- [[decisions/]] — Decision records

## Capabilities

{chr(10).join(f"- {cap}" for cap in self.get_capabilities())}
"""
            index_path.write_text(index_content)

    async def _subscribe_to_events(self) -> None:
        """Subscribe to relevant events"""
        # Subscribe to knowledge distribution for this domain
        self.event_bus.subscribe(
            "knowledge.distributed",
            self._handle_knowledge_distribution,
        )

        # Start polling for task assignments from Operator
        # Note: Messages use queue pattern, not pub/sub
        # Magisters will poll messages in their main loop

    async def _handle_knowledge_distribution(self, event: Event) -> None:
        """Handle knowledge distribution from Teacher

        Args:
            event: Knowledge distribution event
        """
        # Check if this knowledge is for our domain
        collection = event.payload.get("collection", "")

        if self.domain in collection or event.payload.get("target_agent_id") == self.agent_id:
            knowledge_id = event.payload.get("knowledge_id")

            # Log receipt
            async with self.db.session() as session:
                await session.execute(
                    text("""
                    INSERT INTO magister_decisions
                    (id, magister_id, decision_type, context, decision, decided_at)
                    VALUES (:id, :magister_id, :decision_type, :context, :decision, :decided_at)
                    """),
                    {
                        "id": f"decision-{uuid4().hex[:8]}",
                        "magister_id": self.agent_id,
                        "decision_type": "knowledge_received",
                        "context": json.dumps({"knowledge_id": knowledge_id}),
                        "decision": "acknowledged",
                        "decided_at": datetime.now(timezone.utc),
                    },
                )
                await session.commit()

    def get_capabilities(self) -> list[str]:
        """Get Magister capabilities

        Base capabilities that all Magisters have.
        Subclasses should extend this with domain-specific capabilities.
        """
        return [
            "search_knowledge",
            "cache_knowledge",
            "query_teacher",
            "request_research",
        ]

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute a task based on capability with error handling

        Args:
            task: Task to execute

        Returns:
            Task result
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Execute task implementation
            result = await self._execute_task_impl(task)
            return result
        except Exception as e:
            # Log error
            await self._log_error(task, e)

            # Return failed result
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                action=task.metadata.get("action", "unknown"),
                status="failed",
                result={},
                error=str(e),
                duration_seconds=duration,
                completed_at=datetime.now(timezone.utc),
            )

    async def _execute_task_impl(self, task: Task) -> TaskResult:
        """Execute task implementation (internal)

        Args:
            task: Task to execute

        Returns:
            Task result
        """
        start_time = datetime.now(timezone.utc)
        capability = task.metadata.get("capability")

        if capability == "search_knowledge":
            result = await self._handle_search_knowledge(task)
        elif capability == "cache_knowledge":
            result = await self._handle_cache_knowledge(task)
        elif capability == "query_teacher":
            result = await self._handle_query_teacher(task)
        elif capability == "request_research":
            result = await self._handle_request_research(task)
        else:
            result = TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                action=task.metadata.get("action", "unknown"),
                status="failed",
                result={},
                error=f"Unknown capability: {capability}",
                duration_seconds=0.0,
                completed_at=datetime.now(timezone.utc),
            )

        # Add duration
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        result.duration_seconds = duration
        result.agent_id = self.agent_id
        result.action = task.metadata.get("action", capability or "unknown")
        result.completed_at = datetime.now(timezone.utc)

        return result

    async def _handle_search_knowledge(self, task: Task) -> TaskResult:
        """Handle knowledge search task"""
        query = task.metadata.get("query")
        search_local = task.metadata.get("search_local", True)
        search_teacher = task.metadata.get("search_teacher", True)

        results = await self.search_knowledge(
            query=query,
            search_local=search_local,
            search_teacher=search_teacher,
        )

        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            action="search_knowledge",
            status="completed",
            result={"results": results, "count": len(results)},
            error=None,
            duration_seconds=0.0,
            completed_at=datetime.now(timezone.utc),
        )

    async def _handle_cache_knowledge(self, task: Task) -> TaskResult:
        """Handle knowledge caching task"""
        knowledge = task.metadata.get("knowledge")
        cache_key = task.metadata.get("cache_key")

        await self.cache_knowledge(knowledge, cache_key)

        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            action="cache_knowledge",
            status="completed",
            result={"cached": True},
            error=None,
            duration_seconds=0.0,
            completed_at=datetime.now(timezone.utc),
        )

    async def _handle_query_teacher(self, task: Task) -> TaskResult:
        """Handle Teacher query task"""
        query = task.metadata.get("query")

        results = await self.query_teacher(query)

        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            action="query_teacher",
            status="completed",
            result={"results": results},
            error=None,
            duration_seconds=0.0,
            completed_at=datetime.now(timezone.utc),
        )

    async def _handle_request_research(self, task: Task) -> TaskResult:
        """Handle research request task"""
        topic = task.metadata.get("topic")

        await self.request_research(topic)

        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            action="request_research",
            status="completed",
            result={"requested": True},
            error=None,
            duration_seconds=0.0,
            completed_at=datetime.now(timezone.utc),
        )

    async def search_knowledge(
        self,
        query: str,
        search_local: bool = True,
        search_teacher: bool = True,
        search_researcher: bool = False,
    ) -> list[dict[str, Any]]:
        """Hybrid search for knowledge

        Search strategy:
        1. Search local cache first (if search_local=True)
        2. If not found → query Teacher (if search_teacher=True)
        3. If Teacher doesn't have → request Researcher (if search_researcher=True)

        Args:
            query: Search query
            search_local: Search local cache
            search_teacher: Query Teacher if not found locally
            search_researcher: Request Researcher if Teacher doesn't have

        Returns:
            List of search results
        """
        results = []
        result_source = "none"

        # Step 1: Search local cache
        if search_local:
            local_results = await self._search_local_cache(query)
            if local_results:
                results = local_results
                result_source = "local"

        # Step 2: Query Teacher if not found locally
        if not results and search_teacher:
            teacher_results = await self.query_teacher(query)
            if teacher_results:
                results = teacher_results
                result_source = "teacher"

                # Cache Teacher results locally
                for result in results:
                    await self.cache_knowledge(result, query)

        # Step 3: Request Researcher if Teacher doesn't have
        if not results and search_researcher:
            await self.request_research(query)
            result_source = "researcher_requested"

        # Log query
        await self._log_query(query, result_source, len(results))

        return results

    async def _search_local_cache(self, query: str) -> list[dict[str, Any]]:
        """Search local knowledge cache

        Args:
            query: Search query

        Returns:
            List of cached knowledge items
        """
        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT id, content, source, quality_score, metadata, cached_at
                FROM magister_knowledge_cache
                WHERE magister_id = :magister_id
                  AND query LIKE :query
                  AND expires_at > :now
                ORDER BY cached_at DESC
                LIMIT 10
                """),
                {
                    "magister_id": self.agent_id,
                    "query": f"%{query}%",
                    "now": datetime.now(timezone.utc),
                },
            )
            rows = result.fetchall()

        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "content": row[1],
                "source": row[2],
                "quality_score": row[3],
                "metadata": json.loads(row[4]) if row[4] else {},
                "cached_at": row[5],
            })

        return results

    async def cache_knowledge(
        self,
        knowledge: dict[str, Any],
        cache_key: str,
    ) -> None:
        """Cache knowledge locally

        Args:
            knowledge: Knowledge to cache
            cache_key: Cache key (usually the query)
        """
        from datetime import timedelta

        cache_id = f"cache-{uuid4().hex[:8]}"
        cached_at = datetime.now(timezone.utc)
        expires_at = cached_at + timedelta(hours=self.cache_ttl_hours)

        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO magister_knowledge_cache
                (id, magister_id, query, content, source, quality_score,
                 metadata, cached_at, expires_at)
                VALUES (:id, :magister_id, :query, :content, :source,
                        :quality_score, :metadata, :cached_at, :expires_at)
                """),
                {
                    "id": cache_id,
                    "magister_id": self.agent_id,
                    "query": cache_key,
                    "content": knowledge.get("content", ""),
                    "source": knowledge.get("source", "unknown"),
                    "quality_score": knowledge.get("quality_score", 0.0),
                    "metadata": json.dumps(knowledge.get("metadata", {})),
                    "cached_at": cached_at,
                    "expires_at": expires_at,
                },
            )
            await session.commit()

        # Also save to Obsidian vault
        await self._save_to_vault(knowledge, cache_key)

    async def _save_to_vault(
        self,
        knowledge: dict[str, Any],
        cache_key: str,
    ) -> None:
        """Save knowledge to Obsidian vault

        Args:
            knowledge: Knowledge to save
            cache_key: Cache key for filename
        """
        # Create filename from cache key
        filename = cache_key.lower().replace(" ", "-")[:50] + ".md"
        filepath = self.vault_path / "knowledge" / filename

        # Create markdown content
        content = f"""---
query: {cache_key}
source: {knowledge.get('source', 'unknown')}
quality_score: {knowledge.get('quality_score', 0.0)}
cached_at: {datetime.now(timezone.utc).isoformat()}
---

# {cache_key}

{knowledge.get('content', '')}

## Metadata

{json.dumps(knowledge.get('metadata', {}), indent=2)}
"""

        filepath.write_text(content)

    async def query_teacher(self, query: str) -> list[dict[str, Any]]:
        """Query Teacher for knowledge

        Args:
            query: Search query

        Returns:
            List of results from Teacher
        """
        # Create query event
        event = Event(
            event_type="magister.query",
            source_agent_id=self.agent_id,
            target_agent_id=self.teacher_id,
            priority=2,
            payload={
                "query": query,
                "collection": f"{self.domain}_knowledge",
                "magister_id": self.agent_id,
            },
        )

        await self.event_bus.publish(event)

        # In real implementation, would wait for Teacher response
        # For now, return empty (Teacher integration in next tasks)
        return []

    async def request_research(self, topic: str) -> None:
        """Request Researcher to investigate a topic

        Args:
            topic: Topic to research
        """
        # Create research request event
        event = Event(
            event_type="research.requested",
            source_agent_id=self.agent_id,
            target_agent_id="researcher",
            priority=2,
            payload={
                "topic": topic,
                "collection": f"{self.domain}_knowledge",
                "requesting_magister": self.agent_id,
                "requested_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        await self.event_bus.publish(event)

    async def _log_query(
        self,
        query: str,
        result_source: str,
        results_count: int,
    ) -> None:
        """Log a query for analytics

        Args:
            query: Search query
            result_source: Where results came from (local, teacher, researcher_requested)
            results_count: Number of results found
        """
        query_id = f"query-{uuid4().hex[:8]}"

        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO magister_queries
                (id, magister_id, query, result_source, results_count, queried_at)
                VALUES (:id, :magister_id, :query, :result_source,
                        :results_count, :queried_at)
                """),
                {
                    "id": query_id,
                    "magister_id": self.agent_id,
                    "query": query,
                    "result_source": result_source,
                    "results_count": results_count,
                    "queried_at": datetime.now(timezone.utc),
                },
            )
            await session.commit()

    async def poll_and_process_tasks(self) -> None:
        """Poll for task assignments from Operator and process them

        This method should be called periodically by the Magister's main loop.
        It checks for pending messages from Operator and processes them.
        """
        # Get pending messages for this agent
        messages = await self.event_bus.get_messages(
            agent_id=self.agent_id,
            status="pending",
            limit=10,
        )

        for message in messages:
            if message.message_type == "task_assignment":
                try:
                    await self._handle_task_assignment(message)
                    await self.event_bus.mark_processed(message.message_id)
                except Exception as e:
                    await self.event_bus.mark_failed(
                        message.message_id,
                        str(e),
                    )

    async def _handle_task_assignment(self, message) -> None:
        """Handle task assignment from Operator

        Args:
            message: Message from Operator with task details

        Steps:
        1. Extract task details from message
        2. Create Task object
        3. Execute task
        4. Report result back to Operator
        """
        from meai.events.event_bus import Message

        # Extract payload
        payload = message.payload

        # Create Task
        task = Task(
            task_id=payload["subtask_id"],
            description=payload["description"],
            metadata={
                "action": payload["action"],
                "parent_task_id": payload["parent_task_id"],
            },
        )

        # Execute task
        result = await self.execute_task(task)

        # Report result back to Operator
        await self._report_result_to_operator(
            result=result,
            parent_task_id=payload["parent_task_id"],
        )

    async def _report_result_to_operator(
        self,
        result: TaskResult,
        parent_task_id: str,
    ) -> None:
        """Report task result back to Operator

        Args:
            result: Task execution result
            parent_task_id: Parent task ID from Operator
        """
        from meai.events.event_bus import Message

        # Create result message
        message = Message(
            from_agent=self.agent_id,
            to_agent="operator",
            message_type="task_result",
            priority=1,
            payload={
                "subtask_id": result.task_id,
                "parent_task_id": parent_task_id,
                "status": result.status,
                "result": result.result,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Publish to Event Bus
        await self.event_bus.publish(message)

    async def _log_error(self, task: Task, error: Exception) -> None:
        """Log task execution error

        Args:
            task: Task that failed
            error: Exception that occurred
        """
        import traceback

        error_id = f"error-{uuid4().hex[:8]}"

        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO magister_errors
                (id, magister_id, task_id, error_type, error_message,
                 stack_trace, occurred_at)
                VALUES (:id, :magister_id, :task_id, :error_type,
                        :error_message, :stack_trace, :occurred_at)
                """),
                {
                    "id": error_id,
                    "magister_id": self.agent_id,
                    "task_id": task.task_id,
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "stack_trace": traceback.format_exc(),
                    "occurred_at": datetime.now(timezone.utc),
                },
            )
            await session.commit()

        # Also write to vault
        error_content = f"""---
error_id: {error_id}
task_id: {task.task_id}
error_type: {type(error).__name__}
occurred_at: {datetime.now(timezone.utc).isoformat()}
---

# Error: {type(error).__name__}

## Task
{task.description}

## Error Message
```
{str(error)}
```

## Stack Trace
```
{traceback.format_exc()}
```

## Task Metadata
```json
{json.dumps(task.metadata, indent=2)}
```
"""

        error_path = self.vault_path / "errors" / f"{error_id}.md"
        error_path.parent.mkdir(parents=True, exist_ok=True)
        error_path.write_text(error_content)
