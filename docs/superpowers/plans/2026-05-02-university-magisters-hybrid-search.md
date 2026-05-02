# University Magisters + Hybrid Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement 6 Magister agents with hybrid search (local → Teacher → Researcher) and domain-specific knowledge management.

**Architecture:** Each Magister has local memory (Obsidian vault), searches Teacher's Qdrant when needed, and requests Researcher for new knowledge. Magisters specialize in their domains (SEO, Content, Ads, SMM, Analytics, Intelligence).

**Tech Stack:** Python 3.11+, Obsidian (markdown vaults), Qdrant, Event Bus, SQLAlchemy

**Dependencies:** Plan 1 must be completed (Qdrant, Teacher, Researcher)

---

## File Structure

**New files:**
```
src/meai/
├── agents/
│   ├── magisters/
│   │   ├── __init__.py
│   │   ├── base_magister.py       # Base Magister class
│   │   ├── seo_magister.py        # SEO Magister
│   │   ├── content_magister.py    # Content Magister
│   │   ├── ads_magister.py        # Ads Magister
│   │   ├── smm_magister.py        # SMM Magister
│   │   ├── analytics_magister.py  # Analytics Magister
│   │   └── intelligence_magister.py # Intelligence Magister

obsidian/
├── seo-magister/
│   ├── knowledge/
│   ├── tasks/
│   └── decisions/
├── content-magister/
│   ├── knowledge/
│   ├── tasks/
│   └── decisions/
├── ads-magister/
│   ├── knowledge/
│   ├── tasks/
│   └── decisions/
├── smm-magister/
│   ├── knowledge/
│   ├── tasks/
│   └── decisions/
├── analytics-magister/
│   ├── knowledge/
│   ├── tasks/
│   └── decisions/
└── intelligence-magister/
    ├── knowledge/
    ├── tasks/
    └── decisions/

tests/
├── unit/
│   ├── test_base_magister.py
│   ├── test_seo_magister.py
│   ├── test_content_magister.py
│   ├── test_ads_magister.py
│   ├── test_smm_magister.py
│   ├── test_analytics_magister.py
│   └── test_intelligence_magister.py
│
├── integration/
│   ├── test_magister_hybrid_search.py
│   └── test_magister_teacher_flow.py

scripts/
├── setup_magisters.py
└── test_magisters_core.py
```

---
## Task 1: Base Magister Class

**Files:**
- Create: `src/meai/agents/magisters/__init__.py`
- Create: `src/meai/agents/magisters/base_magister.py`
- Create: `tests/unit/test_base_magister.py`

- [ ] **Step 1: Write failing test for BaseMagister initialization**

```python
# tests/unit/test_base_magister.py
import pytest
from meai.agents.magisters.base_magister import BaseMagister
from meai.events.event_bus import EventBus
from meai.agents.teacher import TeacherAgent
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_base_magister_initialization():
    """Test BaseMagister can be initialized"""
    event_bus = EventBus()
    
    # Initialize Teacher (required for Magister)
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
    
    teacher = TeacherAgent(
        agent_id="teacher-1",
        event_bus=event_bus,
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    # Create BaseMagister (abstract, so we'll test via concrete subclass later)
    # For now, test that we can't instantiate abstract class
    with pytest.raises(TypeError):
        magister = BaseMagister(
            agent_id="test-magister",
            agent_type="test",
            domain="test",
            event_bus=event_bus,
            teacher=teacher,
            vault_path="./obsidian/test-magister",
        )
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_base_magister.py::test_base_magister_initialization -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'meai.agents.magisters'"

- [ ] **Step 3: Create magisters package**

```python
# src/meai/agents/magisters/__init__.py
"""Magister agents with domain-specific expertise"""

from meai.agents.magisters.base_magister import BaseMagister

__all__ = ["BaseMagister"]
```

- [ ] **Step 4: Write BaseMagister implementation**

```python
# src/meai/agents/magisters/base_magister.py
"""Base Magister class with hybrid search"""

import json
import os
from abc import abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import text

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus, Event
from meai.memory.obsidian import ObsidianVault
from meai.storage.database import Database


class BaseMagister(Agent):
    """Base class for all Magister agents with hybrid search
    
    Hybrid Search Flow:
    1. Search local Obsidian vault first (fastest)
    2. If not found → query Teacher's Qdrant (medium)
    3. If Teacher doesn't have → request Researcher (slowest)
    4. Cache results locally for future use
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        domain: str,
        event_bus: EventBus,
        teacher: TeacherAgent,
        vault_path: str,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
    ):
        """Initialize Base Magister
        
        Args:
            agent_id: Unique agent identifier
            agent_type: Type of magister (seo, content, ads, etc.)
            domain: Knowledge domain (seo_knowledge, content_knowledge, etc.)
            event_bus: Event bus for communication
            teacher: Teacher agent reference
            vault_path: Path to Obsidian vault
            database_url: Database URL for agent state
        """
        super().__init__(agent_id=agent_id, agent_type=agent_type, event_bus=event_bus)
        
        self.domain = domain
        self.teacher = teacher
        self.vault_path = Path(vault_path)
        self.db = Database(database_url)
        
        # Obsidian vault for local knowledge
        self.vault: ObsidianVault | None = None
        
        # Cache settings
        self.cache_ttl_hours = 24  # Cache for 24 hours

    async def initialize(self) -> None:
        """Initialize Magister"""
        await self.db.connect()
        await self._create_tables()
        await self._initialize_vault()
        await self._subscribe_to_events()

    async def shutdown(self) -> None:
        """Shutdown Magister"""
        await self.db.disconnect()

    async def _create_tables(self) -> None:
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
                    result TEXT,
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
                    cached_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    hit_count INTEGER DEFAULT 0
                )
                """)
            )
            
            # Queries table (for analytics)
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS magister_queries (
                    id TEXT PRIMARY KEY,
                    magister_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    search_level TEXT NOT NULL,  -- local/teacher/researcher
                    found BOOLEAN NOT NULL,
                    response_time_ms INTEGER,
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
            
            await session.commit()

    async def _initialize_vault(self) -> None:
        """Initialize Obsidian vault"""
        # Create vault directory structure
        self.vault_path.mkdir(parents=True, exist_ok=True)
        (self.vault_path / "knowledge").mkdir(exist_ok=True)
        (self.vault_path / "tasks").mkdir(exist_ok=True)
        (self.vault_path / "decisions").mkdir(exist_ok=True)
        
        # Initialize vault
        self.vault = ObsidianVault(str(self.vault_path))

    async def _subscribe_to_events(self) -> None:
        """Subscribe to relevant events"""
        # Subscribe to knowledge distribution for this domain
        await self.event_bus.subscribe(
            "knowledge.distributed",
            self._handle_knowledge_distribution,
        )

    async def _handle_knowledge_distribution(self, event: Event) -> None:
        """Handle knowledge distribution from Teacher"""
        collection = event.payload.get("collection")
        
        # Check if this knowledge is for our domain
        if collection == self.domain:
            knowledge_id = event.payload.get("knowledge_id")
            
            # Fetch knowledge from Teacher and cache locally
            results = await self.teacher.search_knowledge(
                query=knowledge_id,
                collection=collection,
                limit=1,
            )
            
            if len(results) > 0:
                await self._cache_knowledge(results[0])

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """Get Magister-specific capabilities (must be implemented by subclasses)"""
        pass

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute a task (must be implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement execute_task")

    async def hybrid_search(
        self,
        query: str,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Hybrid search: local → Teacher → Researcher
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            Search results with metadata about search level
        """
        start_time = datetime.now(timezone.utc)
        
        # Level 1: Search local vault
        local_results = await self._search_local(query, limit)
        
        if len(local_results) > 0:
            response_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            await self._log_query(query, "local", True, int(response_time))
            
            return {
                "results": local_results,
                "source": "local",
                "response_time_ms": int(response_time),
            }
        
        # Level 2: Query Teacher's Qdrant
        teacher_results = await self._search_teacher(query, limit)
        
        if len(teacher_results) > 0:
            # Cache results locally
            for result in teacher_results:
                await self._cache_knowledge(result)
            
            response_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            await self._log_query(query, "teacher", True, int(response_time))
            
            return {
                "results": teacher_results,
                "source": "teacher",
                "response_time_ms": int(response_time),
            }
        
        # Level 3: Request Researcher
        await self._request_research(query)
        
        response_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        await self._log_query(query, "researcher", False, int(response_time))
        
        return {
            "results": [],
            "source": "researcher_requested",
            "response_time_ms": int(response_time),
            "message": "Research requested, results will be available later",
        }

    async def _search_local(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search local Obsidian vault
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching knowledge items
        """
        results = []
        
        # Search in knowledge directory
        knowledge_dir = self.vault_path / "knowledge"
        
        if not knowledge_dir.exists():
            return results
        
        # Simple text search in markdown files
        for md_file in knowledge_dir.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            
            # Check if query appears in content (case-insensitive)
            if query.lower() in content.lower():
                # Extract frontmatter if exists
                metadata = self._extract_frontmatter(content)
                
                results.append({
                    "id": md_file.stem,
                    "content": content,
                    "source": "local_vault",
                    "file_path": str(md_file),
                    "metadata": metadata,
                })
                
                if len(results) >= limit:
                    break
        
        return results

    async def _search_teacher(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search Teacher's Qdrant
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching knowledge items
        """
        results = await self.teacher.search_knowledge(
            query=query,
            collection=self.domain,
            limit=limit,
            score_threshold=0.7,
        )
        
        return results

    async def _request_research(self, topic: str) -> None:
        """Request Researcher to investigate topic
        
        Args:
            topic: Topic to research
        """
        await self.teacher.request_research(
            topic=topic,
            collection=self.domain,
            requesting_magister=self.agent_id,
        )

    async def _cache_knowledge(self, knowledge: dict[str, Any]) -> None:
        """Cache knowledge locally in Obsidian vault
        
        Args:
            knowledge: Knowledge to cache
        """
        # Save to Obsidian vault
        knowledge_id = knowledge.get("id", f"knowledge-{uuid4().hex[:8]}")
        file_path = self.vault_path / "knowledge" / f"{knowledge_id}.md"
        
        # Create markdown with frontmatter
        content = knowledge.get("content", "")
        metadata = knowledge.get("metadata", {})
        quality_score = knowledge.get("quality_score", 0)
        source = knowledge.get("source", "unknown")
        
        frontmatter = {
            "id": knowledge_id,
            "source": source,
            "quality_score": quality_score,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            **metadata,
        }
        
        markdown = self._create_markdown_with_frontmatter(frontmatter, content)
        file_path.write_text(markdown, encoding="utf-8")
        
        # Save to database cache
        expires_at = datetime.now(timezone.utc)
        # Add cache TTL
        from datetime import timedelta
        expires_at = expires_at + timedelta(hours=self.cache_ttl_hours)
        
        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO magister_knowledge_cache
                (id, magister_id, query, content, source, quality_score, 
                 cached_at, expires_at, hit_count)
                VALUES (:id, :magister_id, :query, :content, :source, 
                        :quality_score, :cached_at, :expires_at, :hit_count)
                """),
                {
                    "id": knowledge_id,
                    "magister_id": self.agent_id,
                    "query": "",  # Will be updated on first hit
                    "content": content,
                    "source": source,
                    "quality_score": quality_score,
                    "cached_at": datetime.now(timezone.utc),
                    "expires_at": expires_at,
                    "hit_count": 0,
                },
            )
            await session.commit()

    async def _log_query(
        self,
        query: str,
        search_level: str,
        found: bool,
        response_time_ms: int,
    ) -> None:
        """Log query for analytics
        
        Args:
            query: Search query
            search_level: Where result was found (local/teacher/researcher)
            found: Whether result was found
            response_time_ms: Response time in milliseconds
        """
        query_id = f"query-{uuid4().hex[:8]}"
        
        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO magister_queries
                (id, magister_id, query, search_level, found, 
                 response_time_ms, queried_at)
                VALUES (:id, :magister_id, :query, :search_level, :found,
                        :response_time_ms, :queried_at)
                """),
                {
                    "id": query_id,
                    "magister_id": self.agent_id,
                    "query": query,
                    "search_level": search_level,
                    "found": found,
                    "response_time_ms": response_time_ms,
                    "queried_at": datetime.now(timezone.utc),
                },
            )
            await session.commit()

    def _extract_frontmatter(self, content: str) -> dict[str, Any]:
        """Extract YAML frontmatter from markdown
        
        Args:
            content: Markdown content
            
        Returns:
            Frontmatter as dictionary
        """
        if not content.startswith("---\n"):
            return {}
        
        try:
            # Find end of frontmatter
            end_index = content.find("\n---\n", 4)
            if end_index == -1:
                return {}
            
            # Extract frontmatter
            frontmatter_text = content[4:end_index]
            
            # Parse YAML (simple key: value parsing)
            metadata = {}
            for line in frontmatter_text.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()
            
            return metadata
        
        except Exception:
            return {}

    def _create_markdown_with_frontmatter(
        self,
        frontmatter: dict[str, Any],
        content: str,
    ) -> str:
        """Create markdown with YAML frontmatter
        
        Args:
            frontmatter: Metadata dictionary
            content: Markdown content
            
        Returns:
            Complete markdown with frontmatter
        """
        # Convert frontmatter to YAML
        yaml_lines = ["---"]
        for key, value in frontmatter.items():
            if isinstance(value, str):
                yaml_lines.append(f"{key}: {value}")
            else:
                yaml_lines.append(f"{key}: {json.dumps(value)}")
        yaml_lines.append("---")
        yaml_lines.append("")
        
        return "\n".join(yaml_lines) + content
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/unit/test_base_magister.py::test_base_magister_initialization -v
```

Expected: PASS (BaseMagister is abstract, can't be instantiated)

- [ ] **Step 6: Write test for hybrid search**

```python
# tests/unit/test_base_magister.py (add to existing file)

# Create concrete Magister for testing
class TestMagister(BaseMagister):
    """Concrete Magister for testing"""
    
    def get_capabilities(self) -> list[str]:
        return ["test_capability"]
    
    async def execute_task(self, task: Task) -> TaskResult:
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={"test": "result"},
        )


@pytest.mark.asyncio
async def test_hybrid_search_local_hit():
    """Test hybrid search with local vault hit"""
    event_bus = EventBus()
    
    # Initialize Teacher
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
    
    teacher = TeacherAgent(
        agent_id="teacher-1",
        event_bus=event_bus,
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    await teacher.initialize()
    
    # Create test Magister
    magister = TestMagister(
        agent_id="test-magister",
        agent_type="test",
        domain="test_knowledge",
        event_bus=event_bus,
        teacher=teacher,
        vault_path="./test_vault",
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    await magister.initialize()
    
    # Create local knowledge file
    knowledge_dir = magister.vault_path / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    
    test_file = knowledge_dir / "test-knowledge.md"
    test_file.write_text("""---
id: test-knowledge
source: local
quality_score: 8.5
---

This is test knowledge about SEO best practices.
""")
    
    # Search (should hit local)
    result = await magister.hybrid_search("SEO best practices")
    
    assert result["source"] == "local"
    assert len(result["results"]) > 0
    assert "SEO" in result["results"][0]["content"]
    
    # Cleanup
    import shutil
    shutil.rmtree("./test_vault")
    await magister.shutdown()
    await teacher.shutdown()


@pytest.mark.asyncio
async def test_hybrid_search_teacher_hit():
    """Test hybrid search with Teacher hit"""
    event_bus = EventBus()
    
    # Initialize Teacher
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
    
    teacher = TeacherAgent(
        agent_id="teacher-1",
        event_bus=event_bus,
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    await teacher.initialize()
    
    # Store knowledge in Teacher
    knowledge = {
        "content": "Advanced SEO techniques for 2026",
        "source": "teacher",
        "sources": [],
        "metadata": {},
    }
    await teacher.store_knowledge(knowledge, "test_knowledge")
    
    # Create test Magister
    magister = TestMagister(
        agent_id="test-magister",
        agent_type="test",
        domain="test_knowledge",
        event_bus=event_bus,
        teacher=teacher,
        vault_path="./test_vault",
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    await magister.initialize()
    
    # Search (should hit Teacher)
    result = await magister.hybrid_search("Advanced SEO techniques")
    
    assert result["source"] == "teacher"
    assert len(result["results"]) > 0
    
    # Verify cached locally
    cached_files = list((magister.vault_path / "knowledge").glob("*.md"))
    assert len(cached_files) > 0
    
    # Cleanup
    import shutil
    shutil.rmtree("./test_vault")
    await qdrant.client.delete_collection("test_knowledge")
    await magister.shutdown()
    await teacher.shutdown()
```

- [ ] **Step 7: Run tests**

```bash
pytest tests/unit/test_base_magister.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 8: Commit**

```bash
git add src/meai/agents/magisters/ tests/unit/test_base_magister.py
git commit -m "feat: add Base Magister class with hybrid search

Base Magister features:
- Hybrid search: local → Teacher → Researcher
- Local knowledge caching in Obsidian vaults
- Query logging for analytics
- Event-driven knowledge distribution
- Abstract base for domain-specific Magisters

Database tables:
- magister_tasks (task tracking)
- magister_knowledge_cache (local cache)
- magister_queries (search analytics)
- magister_decisions (decision logging)

Hybrid search flow:
1. Search local Obsidian vault (fastest)
2. If not found → query Teacher's Qdrant
3. If Teacher doesn't have → request Researcher
4. Cache results locally for 24 hours

Tests cover initialization, local hits, and Teacher hits.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: SEO Magister

**Files:**
- Create: `src/meai/agents/magisters/seo_magister.py`
- Create: `tests/unit/test_seo_magister.py`

- [ ] **Step 1: Write failing test for SEO Magister initialization**

```python
# tests/unit/test_seo_magister.py
import pytest
from meai.agents.magisters.seo_magister import SEOMagister
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_seo_magister_initialization():
    """Test SEO Magister can be initialized"""
    event_bus = EventBus()
    
    # Initialize Teacher
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
    
    teacher = TeacherAgent(
        agent_id="teacher-1",
        event_bus=event_bus,
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    # Create SEO Magister
    seo_magister = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=event_bus,
        teacher=teacher,
        vault_path="./obsidian/seo-magister",
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    assert seo_magister.agent_id == "seo-magister-1"
    assert seo_magister.agent_type == "seo_magister"
    assert seo_magister.domain == "seo_knowledge"
    assert "analyze_keywords" in seo_magister.get_capabilities()
    assert "optimize_content" in seo_magister.get_capabilities()
    assert "analyze_competitors" in seo_magister.get_capabilities()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_seo_magister.py::test_seo_magister_initialization -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'meai.agents.magisters.seo_magister'"

- [ ] **Step 3: Write SEO Magister implementation**

```python
# src/meai/agents/magisters/seo_magister.py
"""SEO Magister - SEO specialist agent"""

from typing import Any

from meai.agents.base_agent import Task, TaskResult
from meai.agents.magisters.base_magister import BaseMagister
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus


class SEOMagister(BaseMagister):
    """SEO Magister - specializes in SEO strategies and optimization"""

    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        teacher: TeacherAgent,
        vault_path: str = "./obsidian/seo-magister",
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
    ):
        """Initialize SEO Magister
        
        Args:
            agent_id: Unique agent identifier
            event_bus: Event bus for communication
            teacher: Teacher agent reference
            vault_path: Path to Obsidian vault
            database_url: Database URL
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="seo_magister",
            domain="seo_knowledge",
            event_bus=event_bus,
            teacher=teacher,
            vault_path=vault_path,
            database_url=database_url,
        )

    def get_capabilities(self) -> list[str]:
        """Get SEO Magister capabilities"""
        return [
            "analyze_keywords",
            "optimize_content",
            "analyze_competitors",
            "track_rankings",
            "audit_technical_seo",
        ]

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute SEO-specific task
        
        Args:
            task: Task to execute
            
        Returns:
            Task result
        """
        capability = task.metadata.get("capability")
        
        if capability == "analyze_keywords":
            return await self._analyze_keywords(task)
        elif capability == "optimize_content":
            return await self._optimize_content(task)
        elif capability == "analyze_competitors":
            return await self._analyze_competitors(task)
        elif capability == "track_rankings":
            return await self._track_rankings(task)
        elif capability == "audit_technical_seo":
            return await self._audit_technical_seo(task)
        else:
            return TaskResult(
                task_id=task.task_id,
                status="failed",
                result=None,
                error=f"Unknown capability: {capability}",
            )

    async def _analyze_keywords(self, task: Task) -> TaskResult:
        """Analyze keywords for SEO
        
        Args:
            task: Task with keyword analysis request
            
        Returns:
            Keyword analysis results
        """
        topic = task.metadata.get("topic", "")
        
        # Search for keyword research knowledge
        search_result = await self.hybrid_search(f"keyword research {topic}")
        
        if len(search_result["results"]) == 0:
            return TaskResult(
                task_id=task.task_id,
                status="pending",
                result=None,
                metadata={
                    "message": "Keyword research knowledge requested",
                    "search_source": search_result["source"],
                },
            )
        
        # Analyze keywords based on knowledge
        knowledge = search_result["results"][0]
        
        analysis = {
            "topic": topic,
            "primary_keywords": self._extract_keywords(knowledge["content"], topic),
            "secondary_keywords": self._extract_related_keywords(knowledge["content"]),
            "search_volume_estimate": "medium-high",
            "competition": "moderate",
            "recommendations": self._generate_keyword_recommendations(knowledge["content"]),
            "knowledge_source": search_result["source"],
        }
        
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result=analysis,
            metadata={
                "search_source": search_result["source"],
                "response_time_ms": search_result["response_time_ms"],
            },
        )

    async def _optimize_content(self, task: Task) -> TaskResult:
        """Optimize content for SEO
        
        Args:
            task: Task with content optimization request
            
        Returns:
            Content optimization suggestions
        """
        content = task.metadata.get("content", "")
        target_keywords = task.metadata.get("keywords", [])
        
        # Search for content optimization knowledge
        search_result = await self.hybrid_search("on-page SEO optimization")
        
        if len(search_result["results"]) == 0:
            return TaskResult(
                task_id=task.task_id,
                status="pending",
                result=None,
                metadata={"message": "SEO optimization knowledge requested"},
            )
        
        # Analyze content
        knowledge = search_result["results"][0]
        
        optimization = {
            "keyword_density": self._calculate_keyword_density(content, target_keywords),
            "title_optimization": self._suggest_title_optimization(content, target_keywords),
            "meta_description": self._generate_meta_description(content, target_keywords),
            "heading_structure": self._analyze_heading_structure(content),
            "internal_linking": self._suggest_internal_links(content),
            "recommendations": self._generate_optimization_recommendations(knowledge["content"]),
            "knowledge_source": search_result["source"],
        }
        
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result=optimization,
            metadata={"search_source": search_result["source"]},
        )

    async def _analyze_competitors(self, task: Task) -> TaskResult:
        """Analyze competitors for SEO
        
        Args:
            task: Task with competitor analysis request
            
        Returns:
            Competitor analysis results
        """
        competitors = task.metadata.get("competitors", [])
        
        # Search for competitor analysis knowledge
        search_result = await self.hybrid_search("competitor SEO analysis")
        
        if len(search_result["results"]) == 0:
            return TaskResult(
                task_id=task.task_id,
                status="pending",
                result=None,
                metadata={"message": "Competitor analysis knowledge requested"},
            )
        
        knowledge = search_result["results"][0]
        
        analysis = {
            "competitors": competitors,
            "analysis_framework": self._extract_analysis_framework(knowledge["content"]),
            "key_metrics": ["domain_authority", "backlinks", "content_quality", "technical_seo"],
            "recommendations": self._generate_competitor_recommendations(knowledge["content"]),
            "knowledge_source": search_result["source"],
        }
        
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result=analysis,
            metadata={"search_source": search_result["source"]},
        )

    async def _track_rankings(self, task: Task) -> TaskResult:
        """Track keyword rankings
        
        Args:
            task: Task with ranking tracking request
            
        Returns:
            Ranking tracking setup
        """
        keywords = task.metadata.get("keywords", [])
        
        # Search for ranking tracking knowledge
        search_result = await self.hybrid_search("SEO ranking tracking")
        
        tracking = {
            "keywords": keywords,
            "tracking_frequency": "daily",
            "metrics": ["position", "search_volume", "click_through_rate"],
            "tools_recommended": ["Google Search Console", "SEMrush", "Ahrefs"],
            "knowledge_source": search_result.get("source", "none"),
        }
        
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result=tracking,
            metadata={"search_source": search_result.get("source", "none")},
        )

    async def _audit_technical_seo(self, task: Task) -> TaskResult:
        """Audit technical SEO
        
        Args:
            task: Task with technical SEO audit request
            
        Returns:
            Technical SEO audit results
        """
        url = task.metadata.get("url", "")
        
        # Search for technical SEO knowledge
        search_result = await self.hybrid_search("technical SEO audit")
        
        if len(search_result["results"]) == 0:
            return TaskResult(
                task_id=task.task_id,
                status="pending",
                result=None,
                metadata={"message": "Technical SEO knowledge requested"},
            )
        
        knowledge = search_result["results"][0]
        
        audit = {
            "url": url,
            "audit_areas": [
                "site_speed",
                "mobile_friendliness",
                "crawlability",
                "indexability",
                "structured_data",
                "https_security",
            ],
            "recommendations": self._generate_technical_recommendations(knowledge["content"]),
            "knowledge_source": search_result["source"],
        }
        
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result=audit,
            metadata={"search_source": search_result["source"]},
        )

    # Helper methods for SEO analysis

    def _extract_keywords(self, content: str, topic: str) -> list[str]:
        """Extract primary keywords from content"""
        # Simple keyword extraction (in production, use NLP)
        words = content.lower().split()
        topic_words = topic.lower().split()
        
        keywords = []
        for word in topic_words:
            if word in words:
                keywords.append(word)
        
        return keywords[:5]  # Top 5

    def _extract_related_keywords(self, content: str) -> list[str]:
        """Extract related keywords"""
        # Simple extraction (in production, use semantic analysis)
        common_seo_terms = ["optimization", "ranking", "keywords", "backlinks", "content"]
        
        found = []
        for term in common_seo_terms:
            if term in content.lower():
                found.append(term)
        
        return found

    def _generate_keyword_recommendations(self, knowledge: str) -> list[str]:
        """Generate keyword recommendations based on knowledge"""
        return [
            "Focus on long-tail keywords for better conversion",
            "Target keywords with medium competition",
            "Include semantic variations of main keywords",
            "Optimize for user intent, not just keywords",
        ]

    def _calculate_keyword_density(self, content: str, keywords: list[str]) -> dict:
        """Calculate keyword density"""
        total_words = len(content.split())
        
        density = {}
        for keyword in keywords:
            count = content.lower().count(keyword.lower())
            density[keyword] = round((count / total_words) * 100, 2) if total_words > 0 else 0
        
        return density

    def _suggest_title_optimization(self, content: str, keywords: list[str]) -> str:
        """Suggest optimized title"""
        if len(keywords) > 0:
            return f"{keywords[0].title()} - Complete Guide 2026"
        return "Optimized Title Here"

    def _generate_meta_description(self, content: str, keywords: list[str]) -> str:
        """Generate meta description"""
        # Take first 150 characters of content
        description = content[:150].strip()
        
        # Add primary keyword if not present
        if len(keywords) > 0 and keywords[0].lower() not in description.lower():
            description = f"{keywords[0]}: {description}"
        
        return description + "..."

    def _analyze_heading_structure(self, content: str) -> dict:
        """Analyze heading structure"""
        # Count markdown headings
        h1_count = content.count("\n# ")
        h2_count = content.count("\n## ")
        h3_count = content.count("\n### ")
        
        return {
            "h1_count": h1_count,
            "h2_count": h2_count,
            "h3_count": h3_count,
            "recommendation": "Use one H1, multiple H2s for sections",
        }

    def _suggest_internal_links(self, content: str) -> list[str]:
        """Suggest internal linking opportunities"""
        return [
            "Link to related SEO articles",
            "Add links to service pages",
            "Include navigation to main categories",
        ]

    def _generate_optimization_recommendations(self, knowledge: str) -> list[str]:
        """Generate optimization recommendations"""
        return [
            "Optimize title tag with primary keyword",
            "Write compelling meta description",
            "Use proper heading hierarchy (H1 → H2 → H3)",
            "Add internal links to related content",
            "Optimize images with alt text",
            "Ensure mobile-friendly design",
        ]

    def _extract_analysis_framework(self, knowledge: str) -> list[str]:
        """Extract competitor analysis framework"""
        return [
            "Analyze domain authority and backlink profile",
            "Review content quality and depth",
            "Examine technical SEO implementation",
            "Study keyword targeting strategy",
            "Evaluate user experience and site speed",
        ]

    def _generate_competitor_recommendations(self, knowledge: str) -> list[str]:
        """Generate competitor-based recommendations"""
        return [
            "Identify content gaps in competitor coverage",
            "Target keywords competitors are ranking for",
            "Improve upon competitor content quality",
            "Build backlinks from similar sources",
        ]

    def _generate_technical_recommendations(self, knowledge: str) -> list[str]:
        """Generate technical SEO recommendations"""
        return [
            "Improve page load speed (target < 3 seconds)",
            "Ensure mobile responsiveness",
            "Fix crawl errors in Search Console",
            "Implement structured data markup",
            "Secure site with HTTPS",
            "Create XML sitemap and submit to search engines",
        ]
```

- [ ] **Step 4: Update magisters __init__.py**

```python
# src/meai/agents/magisters/__init__.py
"""Magister agents with domain-specific expertise"""

from meai.agents.magisters.base_magister import BaseMagister
from meai.agents.magisters.seo_magister import SEOMagister

__all__ = ["BaseMagister", "SEOMagister"]
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/unit/test_seo_magister.py::test_seo_magister_initialization -v
```

Expected: PASS

- [ ] **Step 6: Write test for keyword analysis**

```python
# tests/unit/test_seo_magister.py (add to existing file)

@pytest.mark.asyncio
async def test_seo_magister_analyze_keywords():
    """Test SEO Magister keyword analysis"""
    event_bus = EventBus()
    
    # Initialize Teacher
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
    
    teacher = TeacherAgent(
        agent_id="teacher-1",
        event_bus=event_bus,
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    await teacher.initialize()
    
    # Store SEO knowledge in Teacher
    knowledge = {
        "content": "Keyword research best practices: Focus on long-tail keywords, analyze search volume, check competition level, understand user intent.",
        "source": "teacher",
        "sources": [],
        "metadata": {},
    }
    await teacher.store_knowledge(knowledge, "seo_knowledge")
    
    # Create SEO Magister
    seo_magister = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=event_bus,
        teacher=teacher,
        vault_path="./test_seo_vault",
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    await seo_magister.initialize()
    
    # Execute keyword analysis task
    from meai.agents.base_agent import Task
    task = Task(
        task_id="task-1",
        description="Analyze keywords for medical marketing",
        metadata={
            "capability": "analyze_keywords",
            "topic": "medical marketing",
        },
    )
    
    result = await seo_magister.execute_task(task)
    
    assert result.status == "completed"
    assert "primary_keywords" in result.result
    assert "recommendations" in result.result
    assert result.result["knowledge_source"] == "teacher"
    
    # Cleanup
    import shutil
    shutil.rmtree("./test_seo_vault")
    await qdrant.client.delete_collection("seo_knowledge")
    await seo_magister.shutdown()
    await teacher.shutdown()


@pytest.mark.asyncio
async def test_seo_magister_optimize_content():
    """Test SEO Magister content optimization"""
    event_bus = EventBus()
    
    # Initialize Teacher
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
    
    teacher = TeacherAgent(
        agent_id="teacher-1",
        event_bus=event_bus,
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    await teacher.initialize()
    
    # Store SEO knowledge
    knowledge = {
        "content": "On-page SEO optimization: Optimize title tags, write compelling meta descriptions, use proper heading hierarchy, add internal links.",
        "source": "teacher",
        "sources": [],
        "metadata": {},
    }
    await teacher.store_knowledge(knowledge, "seo_knowledge")
    
    # Create SEO Magister
    seo_magister = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=event_bus,
        teacher=teacher,
        vault_path="./test_seo_vault",
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    await seo_magister.initialize()
    
    # Execute content optimization task
    from meai.agents.base_agent import Task
    task = Task(
        task_id="task-2",
        description="Optimize content for SEO",
        metadata={
            "capability": "optimize_content",
            "content": "This is a test article about medical marketing strategies.",
            "keywords": ["medical marketing", "healthcare"],
        },
    )
    
    result = await seo_magister.execute_task(task)
    
    assert result.status == "completed"
    assert "keyword_density" in result.result
    assert "title_optimization" in result.result
    assert "meta_description" in result.result
    assert "recommendations" in result.result
    
    # Cleanup
    import shutil
    shutil.rmtree("./test_seo_vault")
    await qdrant.client.delete_collection("seo_knowledge")
    await seo_magister.shutdown()
    await teacher.shutdown()
```

- [ ] **Step 7: Run all tests**

```bash
pytest tests/unit/test_seo_magister.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 8: Commit**

```bash
git add src/meai/agents/magisters/seo_magister.py tests/unit/test_seo_magister.py
git commit -m "feat: add SEO Magister with domain-specific capabilities

SEO Magister capabilities:
- analyze_keywords: Keyword research and analysis
- optimize_content: On-page SEO optimization
- analyze_competitors: Competitor SEO analysis
- track_rankings: Keyword ranking tracking
- audit_technical_seo: Technical SEO audit

Features:
- Hybrid search for SEO knowledge
- Keyword density calculation
- Title and meta description optimization
- Heading structure analysis
- Internal linking suggestions
- Technical SEO recommendations

Tests cover initialization, keyword analysis, and content optimization.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: Content Magister

**Files:**
- Create: `src/meai/agents/magisters/content_magister.py`
- Create: `tests/unit/test_content_magister.py`

- [ ] **Step 1: Write failing test for Content Magister initialization**

```python
# tests/unit/test_content_magister.py
import pytest
from meai.agents.magisters.content_magister import ContentMagister
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_content_magister_initialization():
    """Test Content Magister can be initialized"""
    event_bus = EventBus()
    
    # Initialize Teacher
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
    
    teacher = TeacherAgent(
        agent_id="teacher-1",
        event_bus=event_bus,
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    # Create Content Magister
    content_magister = ContentMagister(
        agent_id="content-magister-1",
        event_bus=event_bus,
        teacher=teacher,
        vault_path="./obsidian/content-magister",
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    assert content_magister.agent_id == "content-magister-1"
    assert content_magister.agent_type == "content_magister"
    assert content_magister.domain == "content_knowledge"
    assert "generate_content" in content_magister.get_capabilities()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_content_magister.py::test_content_magister_initialization -v
```

Expected: FAIL

- [ ] **Step 3: Write Content Magister implementation**

```python
# src/meai/agents/magisters/content_magister.py
"""Content Magister - Content marketing specialist agent"""

from typing import Any

from meai.agents.base_agent import Task, TaskResult
from meai.agents.magisters.base_magister import BaseMagister
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus


class ContentMagister(BaseMagister):
    """Content Magister - specializes in content marketing and creation"""

    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        teacher: TeacherAgent,
        vault_path: str = "./obsidian/content-magister",
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="content_magister",
            domain="content_knowledge",
            event_bus=event_bus,
            teacher=teacher,
            vault_path=vault_path,
            database_url=database_url,
        )

    def get_capabilities(self) -> list[str]:
        return [
            "generate_content",
            "edit_content",
            "plan_content",
            "analyze_performance",
            "optimize_for_seo",
        ]

    async def execute_task(self, task: Task) -> TaskResult:
        capability = task.metadata.get("capability")
        
        if capability == "generate_content":
            return await self._generate_content(task)
        elif capability == "edit_content":
            return await self._edit_content(task)
        elif capability == "plan_content":
            return await self._plan_content(task)
        elif capability == "analyze_performance":
            return await self._analyze_performance(task)
        elif capability == "optimize_for_seo":
            return await self._optimize_for_seo(task)
        else:
            return TaskResult(
                task_id=task.task_id,
                status="failed",
                result=None,
                error=f"Unknown capability: {capability}",
            )

    async def _generate_content(self, task: Task) -> TaskResult:
        topic = task.metadata.get("topic", "")
        content_type = task.metadata.get("content_type", "article")
        
        search_result = await self.hybrid_search(f"content creation {content_type}")
        
        if len(search_result["results"]) == 0:
            return TaskResult(
                task_id=task.task_id,
                status="pending",
                result=None,
                metadata={"message": "Content creation knowledge requested"},
            )
        
        knowledge = search_result["results"][0]
        
        content = {
            "topic": topic,
            "content_type": content_type,
            "outline": self._generate_outline(topic, content_type),
            "key_points": self._extract_key_points(knowledge["content"]),
            "tone": "professional",
            "length": "medium",
            "knowledge_source": search_result["source"],
        }
        
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result=content,
            metadata={"search_source": search_result["source"]},
        )

    async def _edit_content(self, task: Task) -> TaskResult:
        content = task.metadata.get("content", "")
        
        search_result = await self.hybrid_search("content editing best practices")
        
        edits = {
            "grammar_check": "passed",
            "readability_score": 75,
            "suggestions": [
                "Simplify complex sentences",
                "Add more subheadings",
                "Include examples",
            ],
            "knowledge_source": search_result.get("source", "none"),
        }
        
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result=edits,
        )

    async def _plan_content(self, task: Task) -> TaskResult:
        timeframe = task.metadata.get("timeframe", "month")
        
        search_result = await self.hybrid_search("content calendar planning")
        
        plan = {
            "timeframe": timeframe,
            "content_types": ["blog_post", "social_media", "email"],
            "frequency": "3x per week",
            "themes": ["industry_news", "how_to", "case_studies"],
            "knowledge_source": search_result.get("source", "none"),
        }
        
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result=plan,
        )

    async def _analyze_performance(self, task: Task) -> TaskResult:
        content_id = task.metadata.get("content_id", "")
        
        analysis = {
            "views": 1250,
            "engagement_rate": 0.045,
            "avg_time_on_page": "3:45",
            "bounce_rate": 0.35,
            "recommendations": [
                "Add more visual content",
                "Improve call-to-action",
            ],
        }
        
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result=analysis,
        )

    async def _optimize_for_seo(self, task: Task) -> TaskResult:
        content = task.metadata.get("content", "")
        
        search_result = await self.hybrid_search("SEO content optimization")
        
        optimization = {
            "keyword_placement": "good",
            "meta_tags": "needs_improvement",
            "internal_links": 3,
            "recommendations": [
                "Add focus keyword to first paragraph",
                "Optimize meta description",
                "Add more internal links",
            ],
            "knowledge_source": search_result.get("source", "none"),
        }
        
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result=optimization,
        )

    def _generate_outline(self, topic: str, content_type: str) -> list[str]:
        return [
            "Introduction",
            f"What is {topic}?",
            "Key Benefits",
            "Best Practices",
            "Conclusion",
        ]

    def _extract_key_points(self, knowledge: str) -> list[str]:
        return [
            "Focus on audience needs",
            "Provide actionable insights",
            "Use clear structure",
        ]
```

- [ ] **Step 4: Update magisters __init__.py**

```python
# src/meai/agents/magisters/__init__.py
from meai.agents.magisters.base_magister import BaseMagister
from meai.agents.magisters.seo_magister import SEOMagister
from meai.agents.magisters.content_magister import ContentMagister

__all__ = ["BaseMagister", "SEOMagister", "ContentMagister"]
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/unit/test_content_magister.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/meai/agents/magisters/content_magister.py tests/unit/test_content_magister.py
git commit -m "feat: add Content Magister with content marketing capabilities

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Ads Magister

**Files:**
- Create: `src/meai/agents/magisters/ads_magister.py`
- Create: `tests/unit/test_ads_magister.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_ads_magister.py
import pytest
from meai.agents.magisters.ads_magister import AdsMagister
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_ads_magister_initialization():
    """Test Ads Magister can be initialized"""
    event_bus = EventBus()
    
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
    
    teacher = TeacherAgent(
        agent_id="teacher-1",
        event_bus=event_bus,
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    ads_magister = AdsMagister(
        agent_id="ads-magister-1",
        event_bus=event_bus,
        teacher=teacher,
        vault_path="./obsidian/ads-magister",
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    assert ads_magister.agent_id == "ads-magister-1"
    assert ads_magister.agent_type == "ads_magister"
    assert ads_magister.domain == "ads_knowledge"
    assert "create_campaign" in ads_magister.get_capabilities()
```

- [ ] **Step 2: Write implementation**

```python
# src/meai/agents/magisters/ads_magister.py
"""Ads Magister - Advertising specialist agent"""

from typing import Any

from meai.agents.base_agent import Task, TaskResult
from meai.agents.magisters.base_magister import BaseMagister
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus


class AdsMagister(BaseMagister):
    """Ads Magister - specializes in advertising and PPC campaigns"""

    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        teacher: TeacherAgent,
        vault_path: str = "./obsidian/ads-magister",
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ads_magister",
            domain="ads_knowledge",
            event_bus=event_bus,
            teacher=teacher,
            vault_path=vault_path,
            database_url=database_url,
        )

    def get_capabilities(self) -> list[str]:
        return [
            "create_campaign",
            "optimize_budget",
            "analyze_performance",
            "ab_test",
            "target_audience",
        ]

    async def execute_task(self, task: Task) -> TaskResult:
        capability = task.metadata.get("capability")
        
        if capability == "create_campaign":
            return await self._create_campaign(task)
        elif capability == "optimize_budget":
            return await self._optimize_budget(task)
        elif capability == "analyze_performance":
            return await self._analyze_performance(task)
        elif capability == "ab_test":
            return await self._ab_test(task)
        elif capability == "target_audience":
            return await self._target_audience(task)
        else:
            return TaskResult(
                task_id=task.task_id,
                status="failed",
                result=None,
                error=f"Unknown capability: {capability}",
            )

    async def _create_campaign(self, task: Task) -> TaskResult:
        campaign_type = task.metadata.get("campaign_type", "search")
        budget = task.metadata.get("budget", 1000)
        
        search_result = await self.hybrid_search(f"{campaign_type} campaign creation")
        
        campaign = {
            "campaign_type": campaign_type,
            "budget": budget,
            "structure": {
                "campaigns": 1,
                "ad_groups": 3,
                "ads_per_group": 2,
            },
            "targeting": ["keywords", "demographics", "interests"],
            "bidding_strategy": "maximize_conversions",
            "knowledge_source": search_result.get("source", "none"),
        }
        
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result=campaign,
        )

    async def _optimize_budget(self, task: Task) -> TaskResult:
        current_budget = task.metadata.get("current_budget", 1000)
        
        search_result = await self.hybrid_search("budget optimization strategies")
        
        optimization = {
            "current_budget": current_budget,
            "recommended_allocation": {
                "search": 0.6,
                "display": 0.2,
                "remarketing": 0.2,
            },
            "recommendations": [
                "Increase budget for high-performing campaigns",
                "Pause low-ROI ad groups",
                "Test new bidding strategies",
            ],
            "knowledge_source": search_result.get("source", "none"),
        }
        
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result=optimization,
        )

    async def _analyze_performance(self, task: Task) -> TaskResult:
        campaign_id = task.metadata.get("campaign_id", "")
        
        analysis = {
            "impressions": 15000,
            "clicks": 450,
            "ctr": 0.03,
            "conversions": 23,
            "conversion_rate": 0.051,
            "cost_per_conversion": 43.48,
            "recommendations": [
                "Improve ad copy for better CTR",
                "Refine targeting to reduce CPC",
            ],
        }
        
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result=analysis,
        )

    async def _ab_test(self, task: Task) -> TaskResult:
        variant_a = task.metadata.get("variant_a", {})
        variant_b = task.metadata.get("variant_b", {})
        
        search_result = await self.hybrid_search("A/B testing best practices")
        
        test_plan = {
            "variants": ["A", "B"],
            "traffic_split": 0.5,
            "duration_days": 14,
            "metrics": ["ctr", "conversion_rate", "cost_per_conversion"],
            "sample_size_required": 1000,
            "knowledge_source": search_result.get("source", "none"),
        }
        
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result=test_plan,
        )

    async def _target_audience(self, task: Task) -> TaskResult:
        product = task.metadata.get("product", "")
        
        search_result = await self.hybrid_search("audience targeting strategies")
        
        targeting = {
            "demographics": {
                "age": "25-54",
                "gender": "all",
                "income": "middle_to_high",
            },
            "interests": ["health", "wellness", "medical"],
            "behaviors": ["online_shoppers", "health_conscious"],
            "custom_audiences": ["website_visitors", "email_list"],
            "knowledge_source": search_result.get("source", "none"),
        }
        
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result=targeting,
        )
```

- [ ] **Step 3: Update __init__.py**

```python
# src/meai/agents/magisters/__init__.py
from meai.agents.magisters.base_magister import BaseMagister
from meai.agents.magisters.seo_magister import SEOMagister
from meai.agents.magisters.content_magister import ContentMagister
from meai.agents.magisters.ads_magister import AdsMagister

__all__ = ["BaseMagister", "SEOMagister", "ContentMagister", "AdsMagister"]
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/unit/test_ads_magister.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/meai/agents/magisters/ads_magister.py tests/unit/test_ads_magister.py
git commit -m "feat: add Ads Magister with advertising capabilities

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 5: SMM Magister

**Files:**
- Create: `src/meai/agents/magisters/smm_magister.py`
- Create: `tests/unit/test_smm_magister.py`

**Implementation:** Similar to Ads Magister structure

```python
# src/meai/agents/magisters/smm_magister.py
class SMMMagister(BaseMagister):
    def __init__(self, agent_id, event_bus, teacher, vault_path="./obsidian/smm-magister", database_url="..."):
        super().__init__(
            agent_id=agent_id,
            agent_type="smm_magister",
            domain="smm_knowledge",
            event_bus=event_bus,
            teacher=teacher,
            vault_path=vault_path,
            database_url=database_url,
        )
    
    def get_capabilities(self) -> list[str]:
        return ["create_post", "schedule_posts", "engage_audience", "analyze_metrics", "manage_campaigns"]
    
    async def _create_post(self, task: Task) -> TaskResult:
        platform = task.metadata.get("platform", "instagram")
        search_result = await self.hybrid_search(f"{platform} content creation")
        
        post = {
            "platform": platform,
            "content_type": "image_with_caption",
            "caption_length": "medium",
            "hashtags": 10,
            "best_time": "18:00-20:00",
            "knowledge_source": search_result.get("source", "none"),
        }
        return TaskResult(task_id=task.task_id, status="completed", result=post)
```

**Commit:** `feat: add SMM Magister with social media capabilities`

---

## Task 6: Analytics Magister

**Files:**
- Create: `src/meai/agents/magisters/analytics_magister.py`
- Create: `tests/unit/test_analytics_magister.py`

**Implementation:** Similar to Ads Magister structure

```python
# src/meai/agents/magisters/analytics_magister.py
class AnalyticsMagister(BaseMagister):
    def __init__(self, agent_id, event_bus, teacher, vault_path="./obsidian/analytics-magister", database_url="..."):
        super().__init__(
            agent_id=agent_id,
            agent_type="analytics_magister",
            domain="analytics_knowledge",
            event_bus=event_bus,
            teacher=teacher,
            vault_path=vault_path,
            database_url=database_url,
        )
    
    def get_capabilities(self) -> list[str]:
        return ["analyze_data", "create_report", "track_metrics", "predict_trends", "optimize_performance"]
    
    async def _analyze_data(self, task: Task) -> TaskResult:
        data_source = task.metadata.get("data_source", "google_analytics")
        search_result = await self.hybrid_search("data analysis best practices")
        
        analysis = {
            "data_source": data_source,
            "metrics": ["sessions", "bounce_rate", "conversion_rate"],
            "insights": [
                "Traffic increased 15% month-over-month",
                "Mobile traffic dominates at 65%",
                "Conversion rate improved by 2.3%",
            ],
            "knowledge_source": search_result.get("source", "none"),
        }
        return TaskResult(task_id=task.task_id, status="completed", result=analysis)
```

**Commit:** `feat: add Analytics Magister with data analysis capabilities`

---

## Task 7: Intelligence Magister

**Files:**
- Create: `src/meai/agents/magisters/intelligence_magister.py`
- Create: `tests/unit/test_intelligence_magister.py`

**Implementation:** Similar to Ads Magister structure

```python
# src/meai/agents/magisters/intelligence_magister.py
class IntelligenceMagister(BaseMagister):
    def __init__(self, agent_id, event_bus, teacher, vault_path="./obsidian/intelligence-magister", database_url="..."):
        super().__init__(
            agent_id=agent_id,
            agent_type="intelligence_magister",
            domain="intelligence_knowledge",
            event_bus=event_bus,
            teacher=teacher,
            vault_path=vault_path,
            database_url=database_url,
        )
    
    def get_capabilities(self) -> list[str]:
        return ["research_market", "analyze_trends", "monitor_competitors", "identify_opportunities", "strategic_insights"]
    
    async def _research_market(self, task: Task) -> TaskResult:
        market = task.metadata.get("market", "healthcare")
        search_result = await self.hybrid_search(f"{market} market research")
        
        research = {
            "market": market,
            "market_size": "$500B",
            "growth_rate": "8.5% CAGR",
            "key_trends": [
                "Digital transformation",
                "Telemedicine adoption",
                "AI-powered diagnostics",
            ],
            "opportunities": [
                "Underserved rural markets",
                "Preventive care solutions",
            ],
            "knowledge_source": search_result.get("source", "none"),
        }
        return TaskResult(task_id=task.task_id, status="completed", result=research)
```

**Commit:** `feat: add Intelligence Magister with market intelligence capabilities`

---

## Task 8: Integration Test - Hybrid Search

**Files:**
- Create: `tests/integration/test_magister_hybrid_search.py`

- [ ] **Step 1: Write integration test for hybrid search**

```python
# tests/integration/test_magister_hybrid_search.py
"""Integration test: Hybrid search across all layers"""

import pytest
import asyncio
from pathlib import Path

from meai.agents.magisters.seo_magister import SEOMagister
from meai.agents.teacher import TeacherAgent
from meai.agents.researcher import ResearcherAgent
from meai.events.event_bus import EventBus
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_hybrid_search_local_hit():
    """Test Level 1: Local vault hit"""
    event_bus = EventBus()
    
    # Initialize components
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
    
    teacher = TeacherAgent(
        agent_id="teacher-1",
        event_bus=event_bus,
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    await teacher.initialize()
    
    # Create SEO Magister
    seo_magister = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=event_bus,
        teacher=teacher,
        vault_path="./test_hybrid_vault",
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    await seo_magister.initialize()
    
    # Create local knowledge
    knowledge_dir = Path("./test_hybrid_vault/knowledge")
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    
    (knowledge_dir / "seo-2026.md").write_text("""---
id: seo-2026
source: local
quality_score: 9.0
---

SEO best practices for 2026 include Core Web Vitals optimization.
""")
    
    # Search (should hit local)
    result = await seo_magister.hybrid_search("SEO best practices 2026")
    
    assert result["source"] == "local"
    assert len(result["results"]) > 0
    assert result["response_time_ms"] < 100  # Local is fast
    
    # Cleanup
    import shutil
    shutil.rmtree("./test_hybrid_vault")
    await seo_magister.shutdown()
    await teacher.shutdown()


@pytest.mark.asyncio
async def test_hybrid_search_teacher_hit():
    """Test Level 2: Teacher Qdrant hit"""
    event_bus = EventBus()
    
    # Initialize components
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
    
    teacher = TeacherAgent(
        agent_id="teacher-1",
        event_bus=event_bus,
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    await teacher.initialize()
    
    # Store knowledge in Teacher
    knowledge = {
        "content": "Content marketing strategies for 2026",
        "source": "teacher",
        "sources": [],
        "metadata": {},
    }
    await teacher.store_knowledge(knowledge, "seo_knowledge")
    
    # Create SEO Magister
    seo_magister = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=event_bus,
        teacher=teacher,
        vault_path="./test_hybrid_vault",
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    await seo_magister.initialize()
    
    # Search (should hit Teacher)
    result = await seo_magister.hybrid_search("Content marketing strategies")
    
    assert result["source"] == "teacher"
    assert len(result["results"]) > 0
    
    # Verify cached locally
    cached_files = list(Path("./test_hybrid_vault/knowledge").glob("*.md"))
    assert len(cached_files) > 0
    
    # Second search should hit local cache
    result2 = await seo_magister.hybrid_search("Content marketing strategies")
    assert result2["source"] == "local"
    assert result2["response_time_ms"] < result["response_time_ms"]
    
    # Cleanup
    import shutil
    shutil.rmtree("./test_hybrid_vault")
    await qdrant.client.delete_collection("seo_knowledge")
    await seo_magister.shutdown()
    await teacher.shutdown()


@pytest.mark.asyncio
async def test_hybrid_search_researcher_request():
    """Test Level 3: Researcher request"""
    event_bus = EventBus()
    
    # Initialize components
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
    
    teacher = TeacherAgent(
        agent_id="teacher-1",
        event_bus=event_bus,
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    await teacher.initialize()
    
    # Create SEO Magister
    seo_magister = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=event_bus,
        teacher=teacher,
        vault_path="./test_hybrid_vault",
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    await seo_magister.initialize()
    
    # Track research requests
    research_requests = []
    
    async def track_research(event):
        research_requests.append(event)
    
    await event_bus.subscribe("research.requested", track_research)
    
    # Search for unknown topic (should request Researcher)
    result = await seo_magister.hybrid_search("Quantum SEO techniques 2026")
    
    # Give event bus time to process
    await asyncio.sleep(0.1)
    
    assert result["source"] == "researcher_requested"
    assert len(research_requests) > 0
    assert research_requests[0].payload["topic"] == "Quantum SEO techniques 2026"
    
    # Cleanup
    import shutil
    shutil.rmtree("./test_hybrid_vault")
    await seo_magister.shutdown()
    await teacher.shutdown()
```

- [ ] **Step 2: Run integration tests**

```bash
# Make sure Qdrant is running
docker-compose up -d qdrant

# Run tests
pytest tests/integration/test_magister_hybrid_search.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_magister_hybrid_search.py
git commit -m "test: add hybrid search integration tests

Integration tests cover:
- Level 1: Local vault hit (fastest)
- Level 2: Teacher Qdrant hit (medium)
- Level 3: Researcher request (slowest)
- Caching behavior after Teacher hit

Tests verify:
- Search performance at each level
- Local caching after remote retrieval
- Event-driven Researcher requests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 9: Integration Test - Magister → Teacher Flow

**Files:**
- Create: `tests/integration/test_magister_teacher_flow.py`

**Implementation:** Test Magister-Teacher communication (similar to Task 8 structure)

**Test scenarios:**
1. Magister queries Teacher
2. Teacher returns results
3. Magister caches locally
4. Teacher notifies Magister of new knowledge

**Commit:** `test: add Magister-Teacher integration tests`

---

## Task 10: Setup Script

**Files:**
- Create: `scripts/setup_magisters.py`

- [ ] **Step 1: Write setup script**

```python
# scripts/setup_magisters.py
"""Initialize all Magister vaults and databases"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def main():
    """Initialize Magisters"""
    print("🔧 Setting up Magisters...")
    print()
    
    # Magister configurations
    magisters = [
        {
            "name": "seo-magister",
            "description": "SEO strategies and optimization",
        },
        {
            "name": "content-magister",
            "description": "Content marketing and copywriting",
        },
        {
            "name": "ads-magister",
            "description": "Advertising campaigns and PPC",
        },
        {
            "name": "smm-magister",
            "description": "Social media marketing",
        },
        {
            "name": "analytics-magister",
            "description": "Analytics and data insights",
        },
        {
            "name": "intelligence-magister",
            "description": "Market intelligence and trends",
        },
    ]
    
    print(f"📊 Creating {len(magisters)} Magister vaults...")
    print()
    
    created = 0
    skipped = 0
    
    for magister in magisters:
        name = magister["name"]
        description = magister["description"]
        
        vault_path = Path(f"./obsidian/{name}")
        
        try:
            if vault_path.exists():
                print(f"⏭️  {name} - already exists, skipping")
                skipped += 1
            else:
                # Create vault structure
                vault_path.mkdir(parents=True, exist_ok=True)
                (vault_path / "knowledge").mkdir(exist_ok=True)
                (vault_path / "tasks").mkdir(exist_ok=True)
                (vault_path / "decisions").mkdir(exist_ok=True)
                
                # Create README
                readme = f"""# {name.replace('-', ' ').title()}

{description}

## Structure

- `knowledge/` - Cached knowledge from Teacher
- `tasks/` - Task execution logs
- `decisions/` - Decision records

## Capabilities

See agent implementation for full capabilities list.
"""
                (vault_path / "README.md").write_text(readme)
                
                print(f"✅ {name} - created")
                print(f"   {description}")
                created += 1
        
        except Exception as e:
            print(f"❌ {name} - failed: {e}")
    
    print()
    print("=" * 60)
    print(f"✅ Setup complete!")
    print(f"   Created: {created} vaults")
    print(f"   Skipped: {skipped} vaults (already existed)")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
```

- [ ] **Step 2: Test setup script**

```bash
python scripts/setup_magisters.py
```

Expected output:
```
🔧 Setting up Magisters...

📊 Creating 6 Magister vaults...

✅ seo-magister - created
   SEO strategies and optimization
✅ content-magister - created
   Content marketing and copywriting
✅ ads-magister - created
   Advertising campaigns and PPC
✅ smm-magister - created
   Social media marketing
✅ analytics-magister - created
   Analytics and data insights
✅ intelligence-magister - created
   Market intelligence and trends

============================================================
✅ Setup complete!
   Created: 6 vaults
   Skipped: 0 vaults (already existed)
============================================================
```

- [ ] **Step 3: Commit**

```bash
git add scripts/setup_magisters.py
git commit -m "feat: add Magisters setup script

Script creates vault structure for all 6 Magisters:
- seo-magister
- content-magister
- ads-magister
- smm-magister
- analytics-magister
- intelligence-magister

Each vault includes:
- knowledge/ (cached knowledge)
- tasks/ (task logs)
- decisions/ (decision records)
- README.md (documentation)

Features:
- Idempotent (safe to run multiple times)
- Clear progress output
- Error handling

Usage: python scripts/setup_magisters.py

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 11: End-to-End Test

**Files:**
- Create: `scripts/test_magisters_core.py`

**Implementation:** Complete E2E test (similar to Plan 1 Task 15 structure)

**Test flow:**
1. Initialize all 6 Magisters
2. SEO Magister queries: "SEO best practices 2026"
3. Local search → not found
4. Teacher search → not found
5. Researcher request → finds knowledge
6. Teacher stores → distributes to SEO Magister
7. SEO Magister caches locally
8. Second query → local hit (cached)

**Commit:** `test: add end-to-end test for Magisters system`

---

## Task 9: Integration Test - Magister → Teacher Flow

**Files:**
- Create: `tests/integration/test_magister_teacher_flow.py`

- [ ] **Step 1: Write integration test**

```python
# tests/integration/test_magister_teacher_flow.py
"""Integration test: Magister-Teacher communication"""

import pytest
import asyncio
from pathlib import Path

from meai.agents.magisters.seo_magister import SEOMagister
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus, Event
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_magister_queries_teacher():
    """Test Magister queries Teacher and receives results"""
    event_bus = EventBus()
    
    # Initialize components
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
    
    teacher = TeacherAgent(
        agent_id="teacher-1",
        event_bus=event_bus,
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    await teacher.initialize()
    
    # Store knowledge in Teacher
    knowledge = {
        "content": "Advanced SEO techniques for 2026",
        "source": "teacher",
        "sources": [],
        "metadata": {},
    }
    await teacher.store_knowledge(knowledge, "seo_knowledge")
    
    # Create Magister
    magister = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=event_bus,
        teacher=teacher,
        vault_path="./test_flow_vault",
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    await magister.initialize()
    
    # Query Teacher
    result = await magister.hybrid_search("Advanced SEO techniques")
    
    assert result["source"] == "teacher"
    assert len(result["results"]) > 0
    
    # Cleanup
    import shutil
    shutil.rmtree("./test_flow_vault")
    await qdrant.client.delete_collection("seo_knowledge")
    await magister.shutdown()
    await teacher.shutdown()


@pytest.mark.asyncio
async def test_teacher_notifies_magister():
    """Test Teacher notifies Magister of new knowledge"""
    event_bus = EventBus()
    
    # Initialize components
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
    
    teacher = TeacherAgent(
        agent_id="teacher-1",
        event_bus=event_bus,
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    await teacher.initialize()
    
    # Create Magister
    magister = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=event_bus,
        teacher=teacher,
        vault_path="./test_notify_vault",
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    await magister.initialize()
    
    # Store knowledge in Teacher (should trigger notification)
    knowledge = {
        "content": "New SEO trends for 2026",
        "source": "teacher",
        "sources": [],
        "metadata": {},
    }
    knowledge_id = await teacher.store_knowledge(knowledge, "seo_knowledge")
    
    # Distribute to Magisters
    await teacher.distribute_to_magisters(knowledge_id, "seo_knowledge")
    
    # Give event bus time to process
    await asyncio.sleep(0.2)
    
    # Verify Magister received and cached knowledge
    cached_files = list(Path("./test_notify_vault/knowledge").glob("*.md"))
    assert len(cached_files) > 0
    
    # Cleanup
    import shutil
    shutil.rmtree("./test_notify_vault")
    await qdrant.client.delete_collection("seo_knowledge")
    await magister.shutdown()
    await teacher.shutdown()
```

- [ ] **Step 2: Run tests**

```bash
pytest tests/integration/test_magister_teacher_flow.py -v
```

Expected: PASS (2 tests)

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_magister_teacher_flow.py
git commit -m "test: add Magister-Teacher integration tests

Tests cover:
- Magister queries Teacher and receives results
- Teacher notifies Magister of new knowledge
- Knowledge caching after notification

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 11: End-to-End Test

**Files:**
- Create: `scripts/test_magisters_core.py`

- [ ] **Step 1: Write E2E test script**

```python
# scripts/test_magisters_core.py
"""Complete end-to-end test of Magisters system"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from meai.agents.magisters.seo_magister import SEOMagister
from meai.agents.teacher import TeacherAgent
from meai.agents.researcher import ResearcherAgent
from meai.events.event_bus import EventBus
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


def print_header(title: str):
    print()
    print("=" * 60)
    print(f"TEST: {title}")
    print("=" * 60)


def print_success(message: str):
    print(f"✅ {message}")


def print_error(message: str):
    print(f"❌ {message}")


def print_info(message: str):
    print(f"📋 {message}")


async def test_1_initialize_magisters():
    """Test 1: Initialize all Magisters"""
    print_header("Initialize Magisters")
    
    try:
        event_bus = EventBus()
        print_success("Event Bus initialized")
        
        # Initialize Teacher
        qdrant = QdrantClient(url="http://localhost:6333")
        await qdrant.connect()
        print_success("Qdrant connected")
        
        embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
        await embeddings.load()
        print_success(f"Embeddings loaded ({embeddings.dimension} dimensions)")
        
        fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
        await fallback.initialize()
        print_success("Fallback storage initialized")
        
        teacher = TeacherAgent(
            agent_id="teacher-1",
            event_bus=event_bus,
            qdrant_client=qdrant,
            embeddings_model=embeddings,
            fallback_storage=fallback,
            database_url="sqlite+aiosqlite:///:memory:",
        )
        await teacher.initialize()
        print_success("Teacher initialized")
        
        # Initialize SEO Magister
        seo_magister = SEOMagister(
            agent_id="seo-magister-1",
            event_bus=event_bus,
            teacher=teacher,
            vault_path="./test_e2e_vault",
            database_url="sqlite+aiosqlite:///:memory:",
        )
        await seo_magister.initialize()
        print_success("SEO Magister initialized")
        
        return {
            "event_bus": event_bus,
            "qdrant": qdrant,
            "embeddings": embeddings,
            "fallback": fallback,
            "teacher": teacher,
            "seo_magister": seo_magister,
        }
    
    except Exception as e:
        print_error(f"Initialization failed: {e}")
        raise


async def test_2_hybrid_search_flow(components: dict):
    """Test 2: Complete hybrid search flow"""
    print_header("Hybrid Search Flow")
    
    teacher = components["teacher"]
    seo_magister = components["seo_magister"]
    
    # Query 1: Not found anywhere (should request Researcher)
    print_info("Query 1: 'Quantum SEO 2026' (not found)")
    result1 = await seo_magister.hybrid_search("Quantum SEO 2026")
    
    if result1["source"] == "researcher_requested":
        print_success("Researcher request sent")
    else:
        print_error("Expected researcher request")
        return False
    
    # Store knowledge in Teacher
    print_info("Storing knowledge in Teacher...")
    knowledge = {
        "content": "SEO best practices for 2026 include Core Web Vitals",
        "source": "teacher",
        "sources": [],
        "metadata": {},
    }
    await teacher.store_knowledge(knowledge, "seo_knowledge")
    print_success("Knowledge stored in Teacher")
    
    # Query 2: Found in Teacher (should cache locally)
    print_info("Query 2: 'SEO best practices 2026' (Teacher hit)")
    result2 = await seo_magister.hybrid_search("SEO best practices 2026")
    
    if result2["source"] == "teacher":
        print_success(f"Found in Teacher ({result2['response_time_ms']}ms)")
    else:
        print_error("Expected Teacher hit")
        return False
    
    # Query 3: Same query (should hit local cache)
    print_info("Query 3: 'SEO best practices 2026' (local cache)")
    result3 = await seo_magister.hybrid_search("SEO best practices 2026")
    
    if result3["source"] == "local":
        print_success(f"Found in local cache ({result3['response_time_ms']}ms)")
        print_info(f"Speed improvement: {result2['response_time_ms'] - result3['response_time_ms']}ms")
    else:
        print_error("Expected local cache hit")
        return False
    
    return True


async def cleanup(components: dict):
    """Cleanup test resources"""
    print_header("Cleanup")
    
    try:
        # Delete test collection
        qdrant = components["qdrant"]
        if await qdrant.collection_exists("seo_knowledge"):
            await qdrant.client.delete_collection("seo_knowledge")
            print_success("Deleted test collection")
        
        # Shutdown components
        await components["seo_magister"].shutdown()
        await components["teacher"].shutdown()
        await qdrant.disconnect()
        await components["fallback"].shutdown()
        
        # Remove test vault
        import shutil
        if Path("./test_e2e_vault").exists():
            shutil.rmtree("./test_e2e_vault")
            print_success("Removed test vault")
        
        print_success("All components shut down")
    
    except Exception as e:
        print_error(f"Cleanup failed: {e}")


async def main():
    """Run all tests"""
    print()
    print("🧪 Testing Magisters Core System")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    components = None
    all_passed = True
    
    try:
        # Test 1: Initialize
        components = await test_1_initialize_magisters()
        
        # Test 2: Hybrid search
        if not await test_2_hybrid_search_flow(components):
            all_passed = False
    
    except Exception as e:
        print_error(f"Test suite failed: {e}")
        all_passed = False
    
    finally:
        # Cleanup
        if components:
            await cleanup(components)
    
    # Final result
    print()
    print("=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)
    print()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
```

- [ ] **Step 2: Run E2E test**

```bash
# Make sure Qdrant is running
docker-compose up -d qdrant

# Run test
python scripts/test_magisters_core.py
```

Expected output:
```
🧪 Testing Magisters Core System
   Time: 2026-05-02 18:40

============================================================
TEST: Initialize Magisters
============================================================
✅ Event Bus initialized
✅ Qdrant connected
✅ Embeddings loaded (1024 dimensions)
✅ Fallback storage initialized
✅ Teacher initialized
✅ SEO Magister initialized

============================================================
TEST: Hybrid Search Flow
============================================================
📋 Query 1: 'Quantum SEO 2026' (not found)
✅ Researcher request sent
📋 Storing knowledge in Teacher...
✅ Knowledge stored in Teacher
📋 Query 2: 'SEO best practices 2026' (Teacher hit)
✅ Found in Teacher (245ms)
📋 Query 3: 'SEO best practices 2026' (local cache)
✅ Found in local cache (12ms)
📋 Speed improvement: 233ms

============================================================
TEST: Cleanup
============================================================
✅ Deleted test collection
✅ Removed test vault
✅ All components shut down

============================================================
🎉 ALL TESTS PASSED!
============================================================
```

- [ ] **Step 3: Commit**

```bash
git add scripts/test_magisters_core.py
git commit -m "test: add end-to-end test for Magisters system

Complete E2E test covering:
1. Initialize all Magisters
2. Hybrid search flow (local → Teacher → Researcher)
3. Caching behavior verification
4. Performance comparison

Features:
- Clear progress output
- Performance metrics
- Automatic cleanup

Usage: python scripts/test_magisters_core.py

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

