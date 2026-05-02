# University Infrastructure + Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the foundational infrastructure for the University knowledge system with Qdrant vector DB, embeddings, Researcher Agent, and Teacher Agent.

**Architecture:** Qdrant (Docker) for vector storage, bge-m3 for embeddings, Researcher collects knowledge from Perplexity/YouTube/Telegram, Teacher evaluates and stores in Qdrant, Event Bus for async communication.

**Tech Stack:** Python 3.11+, Qdrant, sentence-transformers (bge-m3), Perplexity API, YouTube API, Telegram API, Docker, SQLAlchemy, FastAPI

---

## File Structure

**New files:**
```
src/meai/
├── knowledge/
│   ├── __init__.py
│   ├── qdrant_client.py          # Qdrant connection & operations
│   ├── embeddings.py              # bge-m3 embeddings model
│   └── fallback_storage.py        # SQLite fallback
│
├── integrations/
│   ├── __init__.py
│   ├── perplexity.py              # Perplexity API client
│   ├── youtube.py                 # YouTube API client
│   └── telegram.py                # Telegram API client
│
├── agents/
│   ├── researcher.py              # Researcher Agent
│   └── teacher.py                 # Teacher Agent

tests/
├── unit/
│   ├── test_qdrant_client.py
│   ├── test_embeddings.py
│   ├── test_fallback_storage.py
│   ├── test_perplexity.py
│   ├── test_youtube.py
│   ├── test_telegram.py
│   ├── test_researcher.py
│   └── test_teacher.py
│
├── integration/
│   ├── test_researcher_teacher_flow.py
│   └── test_qdrant_integration.py

scripts/
├── setup_qdrant.py
└── test_university_core.py

docker-compose.yml
```

**Modified files:**
- `requirements.txt` — add dependencies

---

## Task 1: Docker Compose for Qdrant

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: Write docker-compose.yml**

```yaml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: meai-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./data/qdrant:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
    restart: unless-stopped
```

- [ ] **Step 2: Create data directory**

```bash
mkdir -p data/qdrant
```

- [ ] **Step 3: Start Qdrant**

```bash
docker-compose up -d qdrant
```

Expected: Container starts successfully

- [ ] **Step 4: Verify Qdrant is running**

```bash
curl http://localhost:6333/
```

Expected: JSON response with Qdrant version

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml .gitignore
git commit -m "feat: add Qdrant Docker setup"
```

---

## Task 2: Update Dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add new dependencies to requirements.txt**

```txt
# Existing dependencies
fastapi>=0.104.0
uvicorn>=0.24.0
sqlalchemy>=2.0.0
aiosqlite>=0.19.0
pydantic>=2.0.0
anthropic>=0.7.0

# Vector DB
qdrant-client>=1.7.0

# Embeddings
sentence-transformers>=2.3.0
torch>=2.1.0

# API Integrations
httpx>=0.25.0
google-api-python-client>=2.100.0
telethon>=1.34.0

[dev]
pytest>=7.4.0
pytest-asyncio>=0.21.0
ruff>=0.1.0
mypy>=1.7.0
```

- [ ] **Step 2: Install dependencies**

```bash
source venv/bin/activate
pip install -r requirements.txt
```

Expected: All packages install successfully

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "deps: add Qdrant, embeddings, and API integration dependencies"
```

---

## Task 3: Qdrant Client

**Files:**
- Create: `src/meai/knowledge/__init__.py`
- Create: `src/meai/knowledge/qdrant_client.py`
- Create: `tests/unit/test_qdrant_client.py`

- [ ] **Step 1: Write failing test for QdrantClient initialization**

```python
# tests/unit/test_qdrant_client.py
import pytest
from meai.knowledge.qdrant_client import QdrantClient


@pytest.mark.asyncio
async def test_qdrant_client_initialization():
    """Test QdrantClient can be initialized"""
    client = QdrantClient(url="http://localhost:6333")
    assert client.url == "http://localhost:6333"
    assert client.client is None  # Not connected yet


@pytest.mark.asyncio
async def test_qdrant_client_connect():
    """Test QdrantClient can connect to Qdrant"""
    client = QdrantClient(url="http://localhost:6333")
    await client.connect()
    assert client.client is not None
    await client.disconnect()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_qdrant_client.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'meai.knowledge'"

- [ ] **Step 3: Create knowledge package**

```python
# src/meai/knowledge/__init__.py
"""Knowledge management components"""

from meai.knowledge.qdrant_client import QdrantClient

__all__ = ["QdrantClient"]
```

- [ ] **Step 4: Write minimal QdrantClient implementation**

```python
# src/meai/knowledge/qdrant_client.py
"""Qdrant vector database client"""

from typing import Any
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


class QdrantClient:
    """Async Qdrant client wrapper"""

    def __init__(self, url: str = "http://localhost:6333"):
        """Initialize Qdrant client
        
        Args:
            url: Qdrant server URL
        """
        self.url = url
        self.client: AsyncQdrantClient | None = None

    async def connect(self) -> None:
        """Connect to Qdrant server"""
        self.client = AsyncQdrantClient(url=self.url)

    async def disconnect(self) -> None:
        """Disconnect from Qdrant server"""
        if self.client:
            await self.client.close()
            self.client = None

    async def create_collection(
        self,
        collection_name: str,
        vector_size: int = 768,
        distance: Distance = Distance.COSINE,
    ) -> None:
        """Create a collection
        
        Args:
            collection_name: Name of the collection
            vector_size: Size of vectors (default: 768 for bge-m3)
            distance: Distance metric (default: COSINE)
        """
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")

        await self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=distance),
        )

    async def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            True if collection exists, False otherwise
        """
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")

        collections = await self.client.get_collections()
        return any(c.name == collection_name for c in collections.collections)

    async def upsert_points(
        self,
        collection_name: str,
        points: list[PointStruct],
    ) -> None:
        """Insert or update points in collection
        
        Args:
            collection_name: Name of the collection
            points: List of points to upsert
        """
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")

        await self.client.upsert(
            collection_name=collection_name,
            points=points,
        )

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 5,
        score_threshold: float | None = None,
    ) -> list[Any]:
        """Search for similar vectors
        
        Args:
            collection_name: Name of the collection
            query_vector: Query vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of search results
        """
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")

        results = await self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
        )

        return results
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/unit/test_qdrant_client.py -v
```

Expected: PASS (2 tests)

- [ ] **Step 6: Write test for collection creation**

```python
# tests/unit/test_qdrant_client.py (add to existing file)

@pytest.mark.asyncio
async def test_create_collection():
    """Test creating a collection"""
    client = QdrantClient(url="http://localhost:6333")
    await client.connect()
    
    collection_name = "test_collection"
    await client.create_collection(collection_name, vector_size=768)
    
    exists = await client.collection_exists(collection_name)
    assert exists is True
    
    # Cleanup
    await client.client.delete_collection(collection_name)
    await client.disconnect()


@pytest.mark.asyncio
async def test_upsert_and_search():
    """Test upserting points and searching"""
    from qdrant_client.models import PointStruct
    
    client = QdrantClient(url="http://localhost:6333")
    await client.connect()
    
    collection_name = "test_search"
    await client.create_collection(collection_name, vector_size=3)
    
    # Upsert test points
    points = [
        PointStruct(
            id=1,
            vector=[1.0, 0.0, 0.0],
            payload={"content": "test1"}
        ),
        PointStruct(
            id=2,
            vector=[0.0, 1.0, 0.0],
            payload={"content": "test2"}
        ),
    ]
    await client.upsert_points(collection_name, points)
    
    # Search
    results = await client.search(
        collection_name=collection_name,
        query_vector=[1.0, 0.0, 0.0],
        limit=1,
    )
    
    assert len(results) == 1
    assert results[0].id == 1
    assert results[0].payload["content"] == "test1"
    
    # Cleanup
    await client.client.delete_collection(collection_name)
    await client.disconnect()
```

- [ ] **Step 7: Run tests**

```bash
pytest tests/unit/test_qdrant_client.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 8: Commit**

```bash
git add src/meai/knowledge/ tests/unit/test_qdrant_client.py
git commit -m "feat: add QdrantClient with collection and search operations"
```

---

## Task 4: Embeddings Model

**Files:**
- Create: `src/meai/knowledge/embeddings.py`
- Create: `tests/unit/test_embeddings.py`

- [ ] **Step 1: Write failing test for EmbeddingsModel**

```python
# tests/unit/test_embeddings.py
import pytest
from meai.knowledge.embeddings import EmbeddingsModel


@pytest.mark.asyncio
async def test_embeddings_model_initialization():
    """Test EmbeddingsModel can be initialized"""
    model = EmbeddingsModel(model_name="BAAI/bge-m3")
    assert model.model_name == "BAAI/bge-m3"
    assert model.model is None  # Not loaded yet


@pytest.mark.asyncio
async def test_embeddings_model_load():
    """Test EmbeddingsModel can load model"""
    model = EmbeddingsModel(model_name="BAAI/bge-m3")
    await model.load()
    assert model.model is not None
    assert model.dimension == 1024  # bge-m3 dimension


@pytest.mark.asyncio
async def test_encode_text():
    """Test encoding text to vector"""
    model = EmbeddingsModel(model_name="BAAI/bge-m3")
    await model.load()
    
    text = "This is a test sentence"
    vector = await model.encode(text)
    
    assert len(vector) == 1024
    assert all(isinstance(v, float) for v in vector)


@pytest.mark.asyncio
async def test_encode_batch():
    """Test encoding multiple texts"""
    model = EmbeddingsModel(model_name="BAAI/bge-m3")
    await model.load()
    
    texts = ["First sentence", "Second sentence", "Third sentence"]
    vectors = await model.encode_batch(texts)
    
    assert len(vectors) == 3
    assert all(len(v) == 1024 for v in vectors)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_embeddings.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write EmbeddingsModel implementation**

```python
# src/meai/knowledge/embeddings.py
"""Text embeddings using sentence-transformers"""

import asyncio
from typing import Any
from sentence_transformers import SentenceTransformer


class EmbeddingsModel:
    """Async wrapper for sentence-transformers embeddings model"""

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        """Initialize embeddings model
        
        Args:
            model_name: HuggingFace model name (default: BAAI/bge-m3)
        """
        self.model_name = model_name
        self.model: SentenceTransformer | None = None
        self.dimension: int = 0

    async def load(self) -> None:
        """Load the model (runs in thread pool to avoid blocking)"""
        loop = asyncio.get_event_loop()
        self.model = await loop.run_in_executor(
            None, SentenceTransformer, self.model_name
        )
        
        # Get dimension from model
        self.dimension = self.model.get_sentence_embedding_dimension()

    async def encode(self, text: str) -> list[float]:
        """Encode text to vector
        
        Args:
            text: Text to encode
            
        Returns:
            Vector representation
        """
        if not self.model:
            raise RuntimeError("Model not loaded. Call load() first.")

        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, self.model.encode, text
        )
        
        return embedding.tolist()

    async def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts to vectors
        
        Args:
            texts: List of texts to encode
            
        Returns:
            List of vector representations
        """
        if not self.model:
            raise RuntimeError("Model not loaded. Call load() first.")

        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, self.model.encode, texts
        )
        
        return [emb.tolist() for emb in embeddings]
```

- [ ] **Step 4: Update knowledge __init__.py**

```python
# src/meai/knowledge/__init__.py
"""Knowledge management components"""

from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel

__all__ = ["QdrantClient", "EmbeddingsModel"]
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/unit/test_embeddings.py -v
```

Expected: PASS (4 tests) - Note: First run will download model (~2GB), may take time

- [ ] **Step 6: Commit**

```bash
git add src/meai/knowledge/embeddings.py tests/unit/test_embeddings.py
git commit -m "feat: add EmbeddingsModel with bge-m3 support"
```

---

## Task 5: SQLite Fallback Storage

**Files:**
- Create: `src/meai/knowledge/fallback_storage.py`
- Create: `tests/unit/test_fallback_storage.py`

- [ ] **Step 1: Write failing test for FallbackStorage**

```python
# tests/unit/test_fallback_storage.py
import pytest
from datetime import datetime, timezone
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_fallback_storage_initialization():
    """Test FallbackStorage can be initialized"""
    storage = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
    assert storage.database_url == "sqlite+aiosqlite:///:memory:"


@pytest.mark.asyncio
async def test_store_and_retrieve_knowledge():
    """Test storing and retrieving knowledge"""
    storage = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
    await storage.initialize()
    
    knowledge = {
        "content": "Test knowledge",
        "source": "test",
        "quality_score": 8.5,
        "collection": "test_collection",
        "vector": [0.1, 0.2, 0.3],
        "metadata": {"tag": "test"}
    }
    
    knowledge_id = await storage.store_knowledge(knowledge)
    assert knowledge_id is not None
    
    retrieved = await storage.get_pending_knowledge()
    assert len(retrieved) == 1
    assert retrieved[0]["content"] == "Test knowledge"
    
    await storage.shutdown()


@pytest.mark.asyncio
async def test_mark_as_synced():
    """Test marking knowledge as synced"""
    storage = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
    await storage.initialize()
    
    knowledge = {
        "content": "Test",
        "source": "test",
        "quality_score": 7.0,
        "collection": "test",
        "vector": [0.1],
        "metadata": {}
    }
    
    knowledge_id = await storage.store_knowledge(knowledge)
    await storage.mark_as_synced(knowledge_id)
    
    pending = await storage.get_pending_knowledge()
    assert len(pending) == 0
    
    await storage.shutdown()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_fallback_storage.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write FallbackStorage implementation**

```python
# src/meai/knowledge/fallback_storage.py
"""SQLite fallback storage for when Qdrant is unavailable"""

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from meai.storage.database import Database


class FallbackStorage:
    """SQLite fallback storage for knowledge"""

    def __init__(self, database_url: str):
        """Initialize fallback storage
        
        Args:
            database_url: SQLAlchemy database URL
        """
        self.database_url = database_url
        self.db = Database(database_url)

    async def initialize(self) -> None:
        """Initialize database and create tables"""
        await self.db.connect()
        await self._create_tables()

    async def shutdown(self) -> None:
        """Shutdown database connection"""
        await self.db.disconnect()

    async def _create_tables(self) -> None:
        """Create fallback storage tables"""
        async with self.db.session() as session:
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS fallback_knowledge (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    quality_score REAL NOT NULL,
                    collection TEXT NOT NULL,
                    vector TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP NOT NULL,
                    synced BOOLEAN DEFAULT FALSE,
                    synced_at TIMESTAMP
                )
                """)
            )
            await session.commit()

    async def store_knowledge(self, knowledge: dict[str, Any]) -> str:
        """Store knowledge in fallback storage
        
        Args:
            knowledge: Knowledge data with content, source, quality_score, 
                      collection, vector, metadata
                      
        Returns:
            Knowledge ID
        """
        knowledge_id = f"fallback-{uuid4().hex[:8]}"
        
        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO fallback_knowledge
                (id, content, source, quality_score, collection, vector, 
                 metadata, created_at, synced)
                VALUES (:id, :content, :source, :quality_score, :collection, 
                        :vector, :metadata, :created_at, :synced)
                """),
                {
                    "id": knowledge_id,
                    "content": knowledge["content"],
                    "source": knowledge["source"],
                    "quality_score": knowledge["quality_score"],
                    "collection": knowledge["collection"],
                    "vector": json.dumps(knowledge["vector"]),
                    "metadata": json.dumps(knowledge.get("metadata", {})),
                    "created_at": datetime.now(timezone.utc),
                    "synced": False,
                },
            )
            await session.commit()

        return knowledge_id

    async def get_pending_knowledge(self) -> list[dict[str, Any]]:
        """Get all knowledge that hasn't been synced to Qdrant
        
        Returns:
            List of pending knowledge items
        """
        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT id, content, source, quality_score, collection, 
                       vector, metadata, created_at
                FROM fallback_knowledge
                WHERE synced = FALSE
                ORDER BY created_at ASC
                """)
            )
            rows = result.fetchall()

        knowledge_list = []
        for row in rows:
            knowledge_list.append({
                "id": row[0],
                "content": row[1],
                "source": row[2],
                "quality_score": row[3],
                "collection": row[4],
                "vector": json.loads(row[5]),
                "metadata": json.loads(row[6]),
                "created_at": row[7],
            })

        return knowledge_list

    async def mark_as_synced(self, knowledge_id: str) -> None:
        """Mark knowledge as synced to Qdrant
        
        Args:
            knowledge_id: ID of knowledge to mark as synced
        """
        async with self.db.session() as session:
            await session.execute(
                text("""
                UPDATE fallback_knowledge
                SET synced = TRUE, synced_at = :synced_at
                WHERE id = :id
                """),
                {
                    "id": knowledge_id,
                    "synced_at": datetime.now(timezone.utc),
                },
            )
            await session.commit()
```

- [ ] **Step 4: Update knowledge __init__.py**

```python
# src/meai/knowledge/__init__.py
"""Knowledge management components"""

from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage

__all__ = ["QdrantClient", "EmbeddingsModel", "FallbackStorage"]
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/unit/test_fallback_storage.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add src/meai/knowledge/fallback_storage.py tests/unit/test_fallback_storage.py
git commit -m "feat: add SQLite fallback storage for Qdrant unavailability"
```

---

*Plan continues with Tasks 6-15 covering Perplexity/YouTube/Telegram integrations, Researcher Agent, Teacher Agent, and integration tests. Due to length, I'll create the complete file now...*

## Task 6: Perplexity API Integration

**Files:**
- Create: `src/meai/integrations/__init__.py`
- Create: `src/meai/integrations/perplexity.py`
- Create: `tests/unit/test_perplexity.py`

**Implementation:** Create async Perplexity API client with `research()` method that takes a query and returns findings with sources.

**Key methods:**
- `research(query: str) -> dict` — deep research via Perplexity API
- `_make_request(prompt: str) -> str` — internal API call

**Tests:** Mock API responses, test error handling, test rate limiting

**Commit:** `feat: add Perplexity API integration for deep research`

---

## Task 7: YouTube API Integration

**Files:**
- Create: `src/meai/integrations/youtube.py`
- Create: `tests/unit/test_youtube.py`

**Implementation:** YouTube API client for channel monitoring and transcript extraction.

**Key methods:**
- `get_channel_videos(channel_id: str, max_results: int) -> list` — get recent videos
- `get_video_transcript(video_id: str) -> str` — extract transcript
- `monitor_channels(channel_ids: list[str]) -> list` — monitor multiple channels

**Tests:** Mock YouTube API, test transcript extraction, test channel monitoring

**Commit:** `feat: add YouTube API integration for video content`

---

## Task 8: Telegram API Integration

**Files:**
- Create: `src/meai/integrations/telegram.py`
- Create: `tests/unit/test_telegram.py`

**Implementation:** Telegram client using Telethon for channel monitoring.

**Key methods:**
- `connect(api_id: str, api_hash: str) -> None` — connect to Telegram
- `get_channel_messages(channel: str, limit: int) -> list` — get messages
- `monitor_channels(channels: list[str]) -> list` — monitor multiple channels

**Tests:** Mock Telethon client, test message retrieval, test channel monitoring

**Commit:** `feat: add Telegram API integration for channel monitoring`

---

## Task 9: Researcher Agent

**Files:**
- Create: `src/meai/agents/researcher.py`
- Create: `tests/unit/test_researcher.py`

**Implementation:** Researcher Agent inheriting from `Agent` base class.

**Capabilities:**
- `research_topic` — use Perplexity for deep research
- `monitor_youtube` — monitor YouTube channels
- `monitor_telegram` — monitor Telegram channels
- `validate_source` — evaluate source quality

**Workflow:**
1. Receive research request from Teacher
2. Use Perplexity/YouTube/Telegram based on request
3. Collect findings
4. Validate sources
5. Send findings to Teacher via Event Bus

**Database tables:**
- `researcher_tasks`
- `researcher_sources`
- `researcher_youtube_channels`
- `researcher_telegram_channels`
- `researcher_findings`

**Tests:** Test each capability, test Event Bus integration, test error handling

**Commit:** `feat: add Researcher Agent with multi-source knowledge collection`

---

## Task 10: Teacher Agent - Core

**Files:**
- Create: `src/meai/agents/teacher.py`
- Create: `tests/unit/test_teacher.py`

- [ ] **Step 1: Write failing test for Teacher initialization**

```python
# tests/unit/test_teacher.py
import pytest
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_teacher_initialization():
    """Test TeacherAgent can be initialized"""
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
    )
    
    assert teacher.agent_id == "teacher-1"
    assert teacher.agent_type == "teacher"
    assert "evaluate_knowledge" in teacher.get_capabilities()
    assert "store_knowledge" in teacher.get_capabilities()
    assert "distribute_to_magisters" in teacher.get_capabilities()
    assert "search_knowledge" in teacher.get_capabilities()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_teacher.py::test_teacher_initialization -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'meai.agents.teacher'"

- [ ] **Step 3: Write Teacher Agent implementation**

```python
# src/meai/agents/teacher.py
"""Teacher Agent - evaluates and stores knowledge in University"""

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from qdrant_client.models import PointStruct, Distance
from sqlalchemy import text

from meai.agents.base_agent import Agent, Task, TaskResult, Feedback
from meai.events.event_bus import EventBus, Event
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage
from meai.storage.database import Database


class TeacherAgent(Agent):
    """Teacher Agent - evaluates knowledge quality and stores in Qdrant"""

    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        qdrant_client: QdrantClient,
        embeddings_model: EmbeddingsModel,
        fallback_storage: FallbackStorage,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
    ):
        """Initialize Teacher Agent
        
        Args:
            agent_id: Unique agent identifier
            event_bus: Event bus for communication
            qdrant_client: Qdrant client for vector storage
            embeddings_model: Embeddings model for vectorization
            fallback_storage: SQLite fallback storage
            database_url: Database URL for agent state
        """
        super().__init__(agent_id=agent_id, agent_type="teacher", event_bus=event_bus)
        
        self.qdrant = qdrant_client
        self.embeddings = embeddings_model
        self.fallback = fallback_storage
        self.db = Database(database_url)
        
        # Collections for different knowledge domains
        self.collections = [
            "seo_knowledge",
            "content_knowledge",
            "ads_knowledge",
            "smm_knowledge",
            "analytics_knowledge",
            "intelligence_knowledge",
        ]

    async def initialize(self) -> None:
        """Initialize Teacher Agent"""
        await self.db.connect()
        await self._create_tables()
        await self.qdrant.connect()
        await self.embeddings.load()
        await self.fallback.initialize()

    async def shutdown(self) -> None:
        """Shutdown Teacher Agent"""
        await self.db.disconnect()
        await self.qdrant.disconnect()
        await self.fallback.shutdown()

    async def _create_tables(self) -> None:
        """Create Teacher-specific database tables"""
        async with self.db.session() as session:
            # Knowledge metadata table
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS teacher_knowledge (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    quality_score REAL NOT NULL,
                    collection TEXT NOT NULL,
                    qdrant_point_id TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP
                )
                """)
            )
            
            # Evaluations table
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS teacher_evaluations (
                    id TEXT PRIMARY KEY,
                    knowledge_id TEXT NOT NULL,
                    evaluation_factors TEXT NOT NULL,
                    score REAL NOT NULL,
                    evaluated_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (knowledge_id) REFERENCES teacher_knowledge(id)
                )
                """)
            )
            
            # Distributions table (to Magisters)
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS teacher_distributions (
                    id TEXT PRIMARY KEY,
                    knowledge_id TEXT NOT NULL,
                    magister_id TEXT NOT NULL,
                    collection TEXT NOT NULL,
                    distributed_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (knowledge_id) REFERENCES teacher_knowledge(id)
                )
                """)
            )
            
            await session.commit()

    def get_capabilities(self) -> list[str]:
        """Get Teacher capabilities"""
        return [
            "evaluate_knowledge",
            "store_knowledge",
            "distribute_to_magisters",
            "search_knowledge",
        ]

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute a task based on capability
        
        Args:
            task: Task to execute
            
        Returns:
            Task result
        """
        capability = task.metadata.get("capability")
        
        if capability == "evaluate_knowledge":
            return await self._handle_evaluate_knowledge(task)
        elif capability == "store_knowledge":
            return await self._handle_store_knowledge(task)
        elif capability == "distribute_to_magisters":
            return await self._handle_distribute(task)
        elif capability == "search_knowledge":
            return await self._handle_search(task)
        else:
            return TaskResult(
                task_id=task.task_id,
                status="failed",
                result=None,
                error=f"Unknown capability: {capability}",
            )

    async def _handle_evaluate_knowledge(self, task: Task) -> TaskResult:
        """Handle knowledge evaluation task"""
        knowledge = task.metadata.get("knowledge", {})
        
        score = await self.evaluate_knowledge(knowledge)
        
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={"quality_score": score},
            metadata={"evaluated_at": datetime.now(timezone.utc).isoformat()},
        )

    async def _handle_store_knowledge(self, task: Task) -> TaskResult:
        """Handle knowledge storage task"""
        knowledge = task.metadata.get("knowledge", {})
        collection = task.metadata.get("collection", "intelligence_knowledge")
        
        knowledge_id = await self.store_knowledge(knowledge, collection)
        
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={"knowledge_id": knowledge_id},
            metadata={"stored_at": datetime.now(timezone.utc).isoformat()},
        )

    async def _handle_distribute(self, task: Task) -> TaskResult:
        """Handle distribution to Magisters"""
        knowledge_id = task.metadata.get("knowledge_id")
        collection = task.metadata.get("collection")
        
        distributed = await self.distribute_to_magisters(knowledge_id, collection)
        
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={"distributed_to": distributed},
            metadata={"distributed_at": datetime.now(timezone.utc).isoformat()},
        )

    async def _handle_search(self, task: Task) -> TaskResult:
        """Handle knowledge search task"""
        query = task.metadata.get("query")
        collection = task.metadata.get("collection", "intelligence_knowledge")
        limit = task.metadata.get("limit", 5)
        
        results = await self.search_knowledge(query, collection, limit)
        
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={"results": results},
            metadata={"searched_at": datetime.now(timezone.utc).isoformat()},
        )

    async def evaluate_knowledge(self, knowledge: dict[str, Any]) -> float:
        """Evaluate knowledge quality (1-10 scale)
        
        Evaluation factors:
        - Source authority (trusted domains = higher score)
        - Content length (too short = lower score)
        - Has citations (with citations = higher score)
        - Recency (recent = higher score for time-sensitive topics)
        
        Args:
            knowledge: Knowledge data with content, source, metadata
            
        Returns:
            Quality score (1.0 - 10.0)
        """
        score = 5.0  # base score
        factors = {}
        
        # Factor 1: Source authority
        source = knowledge.get("source", "").lower()
        trusted_domains = [
            "perplexity.ai",
            "youtube.com",
            "scholar.google.com",
            "arxiv.org",
            "github.com",
        ]
        
        if any(domain in source for domain in trusted_domains):
            score += 2.0
            factors["source_authority"] = "trusted"
        else:
            factors["source_authority"] = "unknown"
        
        # Factor 2: Content quality
        content = knowledge.get("content", "")
        content_length = len(content)
        
        if content_length > 500:
            score += 1.5
            factors["content_length"] = "sufficient"
        elif content_length > 200:
            score += 0.5
            factors["content_length"] = "moderate"
        else:
            factors["content_length"] = "short"
        
        # Factor 3: Citations
        sources = knowledge.get("sources", [])
        if len(sources) > 0:
            score += 1.5
            factors["has_citations"] = True
        else:
            factors["has_citations"] = False
        
        # Factor 4: Metadata richness
        metadata = knowledge.get("metadata", {})
        if len(metadata) > 2:
            score += 0.5
            factors["metadata_richness"] = "rich"
        
        # Cap at 10.0
        final_score = min(score, 10.0)
        
        # Store evaluation
        evaluation_id = f"eval-{uuid4().hex[:8]}"
        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO teacher_evaluations
                (id, knowledge_id, evaluation_factors, score, evaluated_at)
                VALUES (:id, :knowledge_id, :factors, :score, :evaluated_at)
                """),
                {
                    "id": evaluation_id,
                    "knowledge_id": knowledge.get("id", "unknown"),
                    "factors": json.dumps(factors),
                    "score": final_score,
                    "evaluated_at": datetime.now(timezone.utc),
                },
            )
            await session.commit()
        
        return final_score

    async def store_knowledge(
        self,
        knowledge: dict[str, Any],
        collection: str = "intelligence_knowledge",
    ) -> str:
        """Store knowledge in Qdrant (or fallback to SQLite)
        
        Steps:
        1. Evaluate knowledge quality
        2. Generate embeddings
        3. Try to store in Qdrant
        4. If Qdrant fails → store in FallbackStorage
        5. Return knowledge ID
        
        Args:
            knowledge: Knowledge data with content, source, metadata
            collection: Qdrant collection name
            
        Returns:
            Knowledge ID
        """
        knowledge_id = f"knowledge-{uuid4().hex[:8]}"
        
        # Evaluate quality
        quality_score = await self.evaluate_knowledge(knowledge)
        
        # Generate embeddings
        content = knowledge.get("content", "")
        vector = await self.embeddings.encode(content)
        
        # Try to store in Qdrant
        qdrant_point_id = None
        try:
            # Create collection if doesn't exist
            if not await self.qdrant.collection_exists(collection):
                await self.qdrant.create_collection(
                    collection_name=collection,
                    vector_size=self.embeddings.dimension,
                    distance=Distance.COSINE,
                )
            
            # Store in Qdrant
            point = PointStruct(
                id=knowledge_id,
                vector=vector,
                payload={
                    "content": content,
                    "source": knowledge.get("source", ""),
                    "quality_score": quality_score,
                    "metadata": knowledge.get("metadata", {}),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            
            await self.qdrant.upsert_points(collection, [point])
            qdrant_point_id = knowledge_id
            
        except Exception as e:
            # Fallback to SQLite
            await self.fallback.store_knowledge({
                "content": content,
                "source": knowledge.get("source", ""),
                "quality_score": quality_score,
                "collection": collection,
                "vector": vector,
                "metadata": knowledge.get("metadata", {}),
            })
        
        # Store metadata in database
        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO teacher_knowledge
                (id, content, source, quality_score, collection, 
                 qdrant_point_id, metadata, created_at)
                VALUES (:id, :content, :source, :quality_score, :collection,
                        :qdrant_point_id, :metadata, :created_at)
                """),
                {
                    "id": knowledge_id,
                    "content": content,
                    "source": knowledge.get("source", ""),
                    "quality_score": quality_score,
                    "collection": collection,
                    "qdrant_point_id": qdrant_point_id,
                    "metadata": json.dumps(knowledge.get("metadata", {})),
                    "created_at": datetime.now(timezone.utc),
                },
            )
            await session.commit()
        
        return knowledge_id

    async def distribute_to_magisters(
        self,
        knowledge_id: str,
        collection: str,
    ) -> list[str]:
        """Distribute knowledge to relevant Magisters via Event Bus
        
        Args:
            knowledge_id: Knowledge ID to distribute
            collection: Collection name (determines which Magisters)
            
        Returns:
            List of Magister IDs that received the knowledge
        """
        # Map collections to Magister types
        collection_to_magister = {
            "seo_knowledge": "seo-magister",
            "content_knowledge": "content-magister",
            "ads_knowledge": "ads-magister",
            "smm_knowledge": "smm-magister",
            "analytics_knowledge": "analytics-magister",
            "intelligence_knowledge": "all",  # broadcast to all
        }
        
        magister_type = collection_to_magister.get(collection, "all")
        
        # Create distribution event
        event = Event(
            event_type="knowledge.distributed",
            source_agent_id=self.agent_id,
            target_agent_id=magister_type,
            priority=2,  # Medium priority
            payload={
                "knowledge_id": knowledge_id,
                "collection": collection,
                "action": "new_knowledge_available",
            },
        )
        
        await self.event_bus.publish(event)
        
        # Record distribution
        distribution_id = f"dist-{uuid4().hex[:8]}"
        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO teacher_distributions
                (id, knowledge_id, magister_id, collection, distributed_at)
                VALUES (:id, :knowledge_id, :magister_id, :collection, :distributed_at)
                """),
                {
                    "id": distribution_id,
                    "knowledge_id": knowledge_id,
                    "magister_id": magister_type,
                    "collection": collection,
                    "distributed_at": datetime.now(timezone.utc),
                },
            )
            await session.commit()
        
        return [magister_type]

    async def search_knowledge(
        self,
        query: str,
        collection: str = "intelligence_knowledge",
        limit: int = 5,
        score_threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """Search for knowledge in Qdrant using vector similarity
        
        Args:
            query: Search query
            collection: Collection to search in
            limit: Maximum number of results
            score_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of search results with content and metadata
        """
        # Generate query embedding
        query_vector = await self.embeddings.encode(query)
        
        # Search in Qdrant
        try:
            results = await self.qdrant.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "content": result.payload.get("content", ""),
                    "source": result.payload.get("source", ""),
                    "quality_score": result.payload.get("quality_score", 0),
                    "similarity_score": result.score,
                    "metadata": result.payload.get("metadata", {}),
                })
            
            return formatted_results
            
        except Exception as e:
            # If Qdrant fails, return empty results
            return []

    async def handle_magister_query(
        self,
        query: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle a query from a Magister
        
        Workflow:
        1. Search in relevant Qdrant collection
        2. If found (similarity >= threshold) → return results
        3. If not found → request Researcher to investigate
        
        Args:
            query: Query data with query text, collection, magister_id
            
        Returns:
            Response with results or research request status
        """
        query_text = query.get("query", "")
        collection = query.get("collection", "intelligence_knowledge")
        magister_id = query.get("magister_id", "unknown")
        
        # Search in Qdrant
        results = await self.search_knowledge(
            query=query_text,
            collection=collection,
            limit=5,
            score_threshold=0.7,
        )
        
        if len(results) > 0:
            # Found relevant knowledge
            return {
                "status": "success",
                "results": results,
                "source": "qdrant",
                "magister_id": magister_id,
            }
        else:
            # Not found - request Researcher
            await self.request_research(
                topic=query_text,
                collection=collection,
                requesting_magister=magister_id,
            )
            
            return {
                "status": "not_found",
                "action": "research_requested",
                "requested_from": "researcher",
                "magister_id": magister_id,
            }

    async def request_research(
        self,
        topic: str,
        collection: str = "intelligence_knowledge",
        requesting_magister: str = "unknown",
    ) -> None:
        """Request Researcher to investigate a topic
        
        Args:
            topic: Topic to research
            collection: Target collection for results
            requesting_magister: Magister ID that requested research
        """
        # Create research request event
        event = Event(
            event_type="research.requested",
            source_agent_id=self.agent_id,
            target_agent_id="researcher",
            priority=2,  # Medium priority
            payload={
                "topic": topic,
                "collection": collection,
                "requesting_magister": requesting_magister,
                "requested_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        
        await self.event_bus.publish(event)
        
        # Log research request
        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO teacher_knowledge
                (id, content, source, quality_score, collection, metadata, created_at)
                VALUES (:id, :content, :source, :quality_score, :collection, :metadata, :created_at)
                """),
                {
                    "id": f"research-request-{uuid4().hex[:8]}",
                    "content": f"Research requested: {topic}",
                    "source": "teacher",
                    "quality_score": 0.0,  # Not evaluated yet
                    "collection": collection,
                    "metadata": json.dumps({
                        "type": "research_request",
                        "requesting_magister": requesting_magister,
                    }),
                    "created_at": datetime.now(timezone.utc),
                },
            )
            await session.commit()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_teacher.py::test_teacher_initialization -v
```

Expected: PASS

- [ ] **Step 5: Write test for knowledge evaluation**

```python
# tests/unit/test_teacher.py (add to existing file)

@pytest.mark.asyncio
async def test_evaluate_knowledge():
    """Test knowledge evaluation"""
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
    
    await teacher.initialize()
    
    # High quality knowledge
    high_quality = {
        "id": "test-1",
        "content": "This is a comprehensive article about SEO best practices in 2026. " * 10,
        "source": "https://perplexity.ai/search/seo-2026",
        "sources": ["source1", "source2", "source3"],
        "metadata": {"author": "Expert", "date": "2026-05-01", "tags": ["seo"]},
    }
    
    score = await teacher.evaluate_knowledge(high_quality)
    assert score >= 8.0  # Should be high quality
    
    # Low quality knowledge
    low_quality = {
        "id": "test-2",
        "content": "Short text",
        "source": "unknown",
        "sources": [],
        "metadata": {},
    }
    
    score = await teacher.evaluate_knowledge(low_quality)
    assert score <= 6.0  # Should be low quality
    
    await teacher.shutdown()
```

- [ ] **Step 6: Write test for knowledge storage**

```python
# tests/unit/test_teacher.py (add to existing file)

@pytest.mark.asyncio
async def test_store_knowledge():
    """Test storing knowledge in Qdrant"""
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
    
    await teacher.initialize()
    
    knowledge = {
        "content": "SEO best practices for 2026",
        "source": "https://perplexity.ai/search/seo",
        "sources": ["source1"],
        "metadata": {"topic": "seo"},
    }
    
    knowledge_id = await teacher.store_knowledge(knowledge, "seo_knowledge")
    
    assert knowledge_id is not None
    assert knowledge_id.startswith("knowledge-")
    
    # Verify stored in Qdrant
    exists = await qdrant.collection_exists("seo_knowledge")
    assert exists is True
    
    # Cleanup
    await qdrant.client.delete_collection("seo_knowledge")
    await teacher.shutdown()
```

- [ ] **Step 7: Write test for knowledge search**

```python
# tests/unit/test_teacher.py (add to existing file)

@pytest.mark.asyncio
async def test_search_knowledge():
    """Test searching knowledge in Qdrant"""
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
    
    await teacher.initialize()
    
    # Store some knowledge
    knowledge1 = {
        "content": "SEO optimization techniques for 2026",
        "source": "test",
        "sources": [],
        "metadata": {},
    }
    
    knowledge2 = {
        "content": "Content marketing strategies",
        "source": "test",
        "sources": [],
        "metadata": {},
    }
    
    await teacher.store_knowledge(knowledge1, "test_collection")
    await teacher.store_knowledge(knowledge2, "test_collection")
    
    # Search for SEO-related knowledge
    results = await teacher.search_knowledge(
        query="SEO optimization",
        collection="test_collection",
        limit=5,
        score_threshold=0.5,
    )
    
    assert len(results) > 0
    assert "SEO" in results[0]["content"]
    assert results[0]["similarity_score"] > 0.5
    
    # Cleanup
    await qdrant.client.delete_collection("test_collection")
    await teacher.shutdown()
```

- [ ] **Step 8: Run all tests**

```bash
pytest tests/unit/test_teacher.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 9: Commit**

```bash
git add src/meai/agents/teacher.py tests/unit/test_teacher.py
git commit -m "feat: add Teacher Agent with knowledge evaluation and storage

Teacher Agent capabilities:
- Evaluate knowledge quality (1-10 scale)
- Store knowledge in Qdrant with embeddings
- Fallback to SQLite when Qdrant unavailable
- Search knowledge using vector similarity
- Distribute knowledge to Magisters via Event Bus

Database tables:
- teacher_knowledge (metadata)
- teacher_evaluations (quality scores)
- teacher_distributions (Magister notifications)

Tests cover initialization, evaluation, storage, and search.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 11: Teacher Agent - Search & Distribution

**Files:**
- Modify: `src/meai/agents/teacher.py`
- Modify: `tests/unit/test_teacher.py`

- [ ] **Step 1: Write failing test for Magister query handling**

```python
# tests/unit/test_teacher.py (add to existing file)

@pytest.mark.asyncio
async def test_handle_magister_query():
    """Test handling Magister queries"""
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
    
    await teacher.initialize()
    
    # Store knowledge first
    knowledge = {
        "content": "SEO best practices include keyword research, on-page optimization, and link building",
        "source": "test",
        "sources": [],
        "metadata": {},
    }
    await teacher.store_knowledge(knowledge, "seo_knowledge")
    
    # Magister query
    query = {
        "query": "What are SEO best practices?",
        "collection": "seo_knowledge",
        "magister_id": "seo-magister-1",
    }
    
    response = await teacher.handle_magister_query(query)
    
    assert response["status"] == "success"
    assert len(response["results"]) > 0
    assert "SEO" in response["results"][0]["content"]
    
    # Cleanup
    await qdrant.client.delete_collection("seo_knowledge")
    await teacher.shutdown()


@pytest.mark.asyncio
async def test_handle_magister_query_not_found():
    """Test Magister query when knowledge not found"""
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
    
    await teacher.initialize()
    
    # Query without any stored knowledge
    query = {
        "query": "What is quantum computing?",
        "collection": "seo_knowledge",
        "magister_id": "seo-magister-1",
    }
    
    response = await teacher.handle_magister_query(query)
    
    assert response["status"] == "not_found"
    assert response["action"] == "research_requested"
    assert "researcher" in response["requested_from"]
    
    await teacher.shutdown()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_teacher.py::test_handle_magister_query -v
```

Expected: FAIL with "AttributeError: 'TeacherAgent' object has no attribute 'handle_magister_query'"

- [ ] **Step 3: Methods already added in Task 10 Step 3**

The methods `handle_magister_query()` and `request_research()` were already included in the Teacher Agent implementation in Task 10 Step 3.

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/unit/test_teacher.py::test_handle_magister_query -v
pytest tests/unit/test_teacher.py::test_handle_magister_query_not_found -v
```

Expected: PASS (2 tests)

- [ ] **Step 5: Write test for research request**

```python
# tests/unit/test_teacher.py (add to existing file)

@pytest.mark.asyncio
async def test_request_research():
    """Test requesting research from Researcher"""
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
    
    await teacher.initialize()
    
    # Subscribe to events to verify research request was published
    received_events = []
    
    async def event_handler(event: Event):
        received_events.append(event)
    
    await event_bus.subscribe("research.requested", event_handler)
    
    # Request research
    await teacher.request_research(
        topic="AI trends 2026",
        collection="intelligence_knowledge",
        requesting_magister="seo-magister-1",
    )
    
    # Give event bus time to process
    import asyncio
    await asyncio.sleep(0.1)
    
    # Verify event was published
    assert len(received_events) == 1
    assert received_events[0].event_type == "research.requested"
    assert received_events[0].payload["topic"] == "AI trends 2026"
    assert received_events[0].target_agent_id == "researcher"
    
    await teacher.shutdown()
```

- [ ] **Step 6: Write test for distribution to Magisters**

```python
# tests/unit/test_teacher.py (add to existing file)

@pytest.mark.asyncio
async def test_distribute_to_magisters():
    """Test distributing knowledge to Magisters"""
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
    
    await teacher.initialize()
    
    # Subscribe to events
    received_events = []
    
    async def event_handler(event: Event):
        received_events.append(event)
    
    await event_bus.subscribe("knowledge.distributed", event_handler)
    
    # Store knowledge
    knowledge = {
        "content": "SEO best practices",
        "source": "test",
        "sources": [],
        "metadata": {},
    }
    knowledge_id = await teacher.store_knowledge(knowledge, "seo_knowledge")
    
    # Distribute to Magisters
    distributed = await teacher.distribute_to_magisters(knowledge_id, "seo_knowledge")
    
    # Give event bus time to process
    import asyncio
    await asyncio.sleep(0.1)
    
    # Verify distribution
    assert len(distributed) > 0
    assert "seo-magister" in distributed[0]
    
    # Verify event was published
    assert len(received_events) == 1
    assert received_events[0].event_type == "knowledge.distributed"
    assert received_events[0].payload["knowledge_id"] == knowledge_id
    
    # Cleanup
    await qdrant.client.delete_collection("seo_knowledge")
    await teacher.shutdown()
```

- [ ] **Step 7: Run all tests**

```bash
pytest tests/unit/test_teacher.py -v
```

Expected: PASS (7 tests total)

- [ ] **Step 8: Commit**

```bash
git add src/meai/agents/teacher.py tests/unit/test_teacher.py
git commit -m "feat: add search and distribution to Teacher Agent

New capabilities:
- handle_magister_query: Answer Magister questions from Qdrant
- request_research: Request Researcher when knowledge not found
- Enhanced distribute_to_magisters: Notify relevant Magisters

Workflow:
1. Magister asks question
2. Teacher searches Qdrant
3. If found → return results
4. If not found → request Researcher via Event Bus
5. Researcher finds knowledge → sends to Teacher
6. Teacher stores and distributes to Magisters

Tests cover Magister queries, research requests, and distribution.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 12: Integration Test - Researcher → Teacher

**Files:**
- Create: `tests/integration/__init__.py`
- Create: `tests/integration/test_researcher_teacher_flow.py`

- [ ] **Step 1: Write integration test**

```python
# tests/integration/__init__.py
"""Integration tests for meAI agents"""
```

```python
# tests/integration/test_researcher_teacher_flow.py
"""Integration test: Researcher → Teacher → Qdrant flow"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from meai.agents.researcher import ResearcherAgent
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus, Event
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_researcher_teacher_flow():
    """Test full flow: Researcher → Teacher → Qdrant
    
    Scenario:
    1. Teacher requests research on "SEO best practices 2026"
    2. Researcher uses Perplexity (mocked) to find knowledge
    3. Researcher sends findings to Teacher via Event Bus
    4. Teacher evaluates and stores in Qdrant
    5. Verify knowledge is searchable in Qdrant
    """
    # Initialize components
    event_bus = EventBus()
    qdrant = QdrantClient(url="http://localhost:6333")
    embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
    fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
    
    # Initialize Researcher
    researcher = ResearcherAgent(
        agent_id="researcher-1",
        event_bus=event_bus,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    # Initialize Teacher
    teacher = TeacherAgent(
        agent_id="teacher-1",
        event_bus=event_bus,
        qdrant_client=qdrant,
        embeddings_model=embeddings,
        fallback_storage=fallback,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    
    await researcher.initialize()
    await teacher.initialize()
    
    # Mock Perplexity API response
    mock_research_result = {
        "content": "SEO best practices for 2026 include: 1) Focus on user experience and Core Web Vitals, 2) Create high-quality, E-E-A-T content, 3) Optimize for voice search and AI-powered search engines, 4) Build authoritative backlinks, 5) Implement structured data markup",
        "source": "https://perplexity.ai/search/seo-2026",
        "sources": [
            "https://moz.com/blog/seo-2026",
            "https://searchengineland.com/seo-trends-2026",
        ],
        "metadata": {
            "topic": "seo",
            "date": "2026-05-01",
            "confidence": "high",
        },
    }
    
    # Track events
    knowledge_stored = asyncio.Event()
    stored_knowledge_id = None
    
    async def on_knowledge_stored(event: Event):
        nonlocal stored_knowledge_id
        if event.event_type == "knowledge.stored":
            stored_knowledge_id = event.payload.get("knowledge_id")
            knowledge_stored.set()
    
    await event_bus.subscribe("knowledge.stored", on_knowledge_stored)
    
    # Step 1: Teacher requests research
    await teacher.request_research(
        topic="SEO best practices 2026",
        collection="seo_knowledge",
        requesting_magister="seo-magister-1",
    )
    
    # Step 2: Researcher receives request and researches (mocked)
    with patch.object(researcher.perplexity, 'research', new_callable=AsyncMock) as mock_research:
        mock_research.return_value = mock_research_result
        
        # Simulate Researcher handling the research request
        research_event = Event(
            event_type="research.requested",
            source_agent_id="teacher-1",
            target_agent_id="researcher-1",
            priority=2,
            payload={
                "topic": "SEO best practices 2026",
                "collection": "seo_knowledge",
                "requesting_magister": "seo-magister-1",
            },
        )
        
        # Researcher executes research
        from meai.agents.base_agent import Task
        task = Task(
            task_id="research-task-1",
            description="Research SEO best practices 2026",
            metadata={
                "capability": "research_topic",
                "topic": "SEO best practices 2026",
                "collection": "seo_knowledge",
            },
        )
        
        result = await researcher.execute_task(task)
        assert result.status == "completed"
        
        # Step 3: Researcher sends findings to Teacher
        findings_event = Event(
            event_type="research.completed",
            source_agent_id="researcher-1",
            target_agent_id="teacher-1",
            priority=2,
            payload={
                "findings": mock_research_result,
                "collection": "seo_knowledge",
            },
        )
        
        await event_bus.publish(findings_event)
    
    # Step 4: Teacher receives and stores knowledge
    # Simulate Teacher handling the findings
    knowledge_id = await teacher.store_knowledge(
        knowledge=mock_research_result,
        collection="seo_knowledge",
    )
    
    assert knowledge_id is not None
    
    # Publish knowledge.stored event
    stored_event = Event(
        event_type="knowledge.stored",
        source_agent_id="teacher-1",
        target_agent_id="all",
        priority=2,
        payload={"knowledge_id": knowledge_id},
    )
    await event_bus.publish(stored_event)
    
    # Wait for event processing
    await asyncio.wait_for(knowledge_stored.wait(), timeout=2.0)
    
    # Step 5: Verify knowledge is in Qdrant
    search_results = await teacher.search_knowledge(
        query="SEO best practices 2026",
        collection="seo_knowledge",
        limit=5,
        score_threshold=0.7,
    )
    
    assert len(search_results) > 0
    assert "SEO" in search_results[0]["content"]
    assert search_results[0]["quality_score"] >= 7.0  # Should be high quality
    assert search_results[0]["similarity_score"] >= 0.7
    
    # Cleanup
    await qdrant.client.delete_collection("seo_knowledge")
    await researcher.shutdown()
    await teacher.shutdown()


@pytest.mark.asyncio
async def test_researcher_teacher_flow_with_distribution():
    """Test flow with distribution to Magisters
    
    Scenario:
    1. Researcher finds knowledge
    2. Teacher stores and evaluates
    3. Teacher distributes to relevant Magisters
    4. Verify Magisters receive notification
    """
    # Initialize components
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
    
    await teacher.initialize()
    
    # Track distribution events
    distribution_events = []
    
    async def on_distribution(event: Event):
        distribution_events.append(event)
    
    await event_bus.subscribe("knowledge.distributed", on_distribution)
    
    # Store knowledge
    knowledge = {
        "content": "Content marketing strategies for 2026",
        "source": "https://perplexity.ai/search/content-marketing",
        "sources": ["source1", "source2"],
        "metadata": {"topic": "content"},
    }
    
    knowledge_id = await teacher.store_knowledge(knowledge, "content_knowledge")
    
    # Distribute to Magisters
    distributed = await teacher.distribute_to_magisters(knowledge_id, "content_knowledge")
    
    # Wait for event processing
    await asyncio.sleep(0.2)
    
    # Verify distribution
    assert len(distributed) > 0
    assert "content-magister" in distributed[0]
    
    # Verify event was published
    assert len(distribution_events) > 0
    assert distribution_events[0].event_type == "knowledge.distributed"
    assert distribution_events[0].payload["knowledge_id"] == knowledge_id
    assert distribution_events[0].target_agent_id == "content-magister"
    
    # Cleanup
    await qdrant.client.delete_collection("content_knowledge")
    await teacher.shutdown()
```

- [ ] **Step 2: Run integration test**

```bash
# Make sure Qdrant is running
docker-compose up -d qdrant

# Run test
pytest tests/integration/test_researcher_teacher_flow.py -v
```

Expected: PASS (2 tests)

- [ ] **Step 3: Commit**

```bash
git add tests/integration/
git commit -m "test: add integration test for Researcher → Teacher flow

Integration tests cover:
- Full flow: research request → findings → storage → search
- Distribution to Magisters via Event Bus
- Qdrant storage verification
- Event-driven communication

Tests use mocked Perplexity API for reproducibility.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 13: Integration Test - Qdrant Fallback

**Files:**
- Create: `tests/integration/test_qdrant_integration.py`

- [ ] **Step 1: Write integration test for Qdrant fallback**

```python
# tests/integration/test_qdrant_integration.py
"""Integration test: Qdrant fallback to SQLite"""

import pytest
import asyncio
from unittest.mock import patch

from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


@pytest.mark.asyncio
async def test_qdrant_normal_operation():
    """Test normal operation: Qdrant available, knowledge stored successfully"""
    # Initialize components
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
    
    await teacher.initialize()
    
    # Store knowledge
    knowledge = {
        "content": "Test knowledge for normal operation",
        "source": "test",
        "sources": [],
        "metadata": {"test": "normal"},
    }
    
    knowledge_id = await teacher.store_knowledge(knowledge, "test_normal")
    
    # Verify stored in Qdrant
    assert knowledge_id is not None
    
    # Verify collection exists
    exists = await qdrant.collection_exists("test_normal")
    assert exists is True
    
    # Verify searchable
    results = await teacher.search_knowledge(
        query="Test knowledge",
        collection="test_normal",
        limit=5,
        score_threshold=0.5,
    )
    
    assert len(results) > 0
    assert results[0]["content"] == "Test knowledge for normal operation"
    
    # Verify NOT in fallback storage
    pending = await fallback.get_pending_knowledge()
    assert len(pending) == 0  # Should be empty (stored in Qdrant)
    
    # Cleanup
    await qdrant.client.delete_collection("test_normal")
    await teacher.shutdown()


@pytest.mark.asyncio
async def test_qdrant_fallback_to_sqlite():
    """Test fallback: Qdrant unavailable, knowledge stored in SQLite"""
    # Initialize components
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
    
    await teacher.initialize()
    
    # Mock Qdrant to simulate failure
    with patch.object(qdrant, 'upsert_points', side_effect=Exception("Qdrant unavailable")):
        # Store knowledge (should fallback to SQLite)
        knowledge = {
            "content": "Test knowledge for fallback",
            "source": "test",
            "sources": [],
            "metadata": {"test": "fallback"},
        }
        
        knowledge_id = await teacher.store_knowledge(knowledge, "test_fallback")
        
        assert knowledge_id is not None
        
        # Verify stored in fallback storage
        pending = await fallback.get_pending_knowledge()
        assert len(pending) == 1
        assert pending[0]["content"] == "Test knowledge for fallback"
        assert pending[0]["collection"] == "test_fallback"
    
    await teacher.shutdown()


@pytest.mark.asyncio
async def test_qdrant_recovery_and_sync():
    """Test recovery: Qdrant comes back online, SQLite knowledge synced"""
    # Initialize components
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
    
    await teacher.initialize()
    
    # Step 1: Simulate Qdrant failure - store in fallback
    with patch.object(qdrant, 'upsert_points', side_effect=Exception("Qdrant down")):
        knowledge1 = {
            "content": "Knowledge stored during outage 1",
            "source": "test",
            "sources": [],
            "metadata": {},
        }
        
        knowledge2 = {
            "content": "Knowledge stored during outage 2",
            "source": "test",
            "sources": [],
            "metadata": {},
        }
        
        await teacher.store_knowledge(knowledge1, "test_recovery")
        await teacher.store_knowledge(knowledge2, "test_recovery")
    
    # Verify stored in fallback
    pending = await fallback.get_pending_knowledge()
    assert len(pending) == 2
    
    # Step 2: Qdrant recovers - sync fallback knowledge
    # Create collection
    if not await qdrant.collection_exists("test_recovery"):
        await qdrant.create_collection(
            collection_name="test_recovery",
            vector_size=embeddings.dimension,
        )
    
    # Sync pending knowledge from fallback to Qdrant
    for knowledge in pending:
        from qdrant_client.models import PointStruct
        
        point = PointStruct(
            id=knowledge["id"],
            vector=knowledge["vector"],
            payload={
                "content": knowledge["content"],
                "source": knowledge["source"],
                "quality_score": knowledge["quality_score"],
                "metadata": knowledge["metadata"],
            },
        )
        
        await qdrant.upsert_points("test_recovery", [point])
        await fallback.mark_as_synced(knowledge["id"])
    
    # Step 3: Verify sync completed
    pending_after = await fallback.get_pending_knowledge()
    assert len(pending_after) == 0  # All synced
    
    # Verify knowledge is now in Qdrant
    results = await teacher.search_knowledge(
        query="Knowledge stored during outage",
        collection="test_recovery",
        limit=5,
        score_threshold=0.5,
    )
    
    assert len(results) == 2
    assert "outage" in results[0]["content"]
    
    # Cleanup
    await qdrant.client.delete_collection("test_recovery")
    await teacher.shutdown()


@pytest.mark.asyncio
async def test_qdrant_partial_failure():
    """Test partial failure: some operations succeed, some fail"""
    # Initialize components
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
    
    await teacher.initialize()
    
    # Store first knowledge (succeeds)
    knowledge1 = {
        "content": "First knowledge - should succeed",
        "source": "test",
        "sources": [],
        "metadata": {},
    }
    
    knowledge_id1 = await teacher.store_knowledge(knowledge1, "test_partial")
    assert knowledge_id1 is not None
    
    # Verify in Qdrant
    exists = await qdrant.collection_exists("test_partial")
    assert exists is True
    
    # Simulate Qdrant failure for second operation
    with patch.object(qdrant, 'upsert_points', side_effect=Exception("Network error")):
        knowledge2 = {
            "content": "Second knowledge - should fallback",
            "source": "test",
            "sources": [],
            "metadata": {},
        }
        
        knowledge_id2 = await teacher.store_knowledge(knowledge2, "test_partial")
        assert knowledge_id2 is not None
    
    # Verify first is in Qdrant, second is in fallback
    results = await teacher.search_knowledge(
        query="First knowledge",
        collection="test_partial",
        limit=5,
        score_threshold=0.5,
    )
    assert len(results) == 1  # Only first knowledge
    
    pending = await fallback.get_pending_knowledge()
    assert len(pending) == 1  # Second knowledge in fallback
    assert "Second knowledge" in pending[0]["content"]
    
    # Cleanup
    await qdrant.client.delete_collection("test_partial")
    await teacher.shutdown()
```

- [ ] **Step 2: Run integration tests**

```bash
# Make sure Qdrant is running
docker-compose up -d qdrant

# Run tests
pytest tests/integration/test_qdrant_integration.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_qdrant_integration.py
git commit -m "test: add Qdrant fallback integration tests

Integration tests cover:
- Normal operation: Qdrant available, storage succeeds
- Fallback: Qdrant unavailable, storage goes to SQLite
- Recovery: Qdrant comes back, SQLite syncs to Qdrant
- Partial failure: some operations succeed, some fallback

Tests verify resilience and data integrity during outages.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 14: Setup Script

**Files:**
- Create: `scripts/setup_qdrant.py`

- [ ] **Step 1: Write setup script**

```python
# scripts/setup_qdrant.py
"""Initialize Qdrant collections for University knowledge system"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from meai.knowledge.qdrant_client import QdrantClient
from qdrant_client.models import Distance


async def main():
    """Initialize Qdrant collections"""
    print("🔧 Setting up Qdrant collections for University...")
    print()
    
    # Connect to Qdrant
    qdrant = QdrantClient(url="http://localhost:6333")
    
    try:
        await qdrant.connect()
        print("✅ Connected to Qdrant at http://localhost:6333")
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        print("   Make sure Qdrant is running: docker-compose up -d qdrant")
        return 1
    
    # Collections to create
    collections = [
        {
            "name": "seo_knowledge",
            "description": "SEO strategies, techniques, and best practices",
        },
        {
            "name": "content_knowledge",
            "description": "Content marketing, copywriting, and content strategy",
        },
        {
            "name": "ads_knowledge",
            "description": "Advertising campaigns, ad optimization, and PPC",
        },
        {
            "name": "smm_knowledge",
            "description": "Social media marketing and community management",
        },
        {
            "name": "analytics_knowledge",
            "description": "Analytics, metrics, and data-driven insights",
        },
        {
            "name": "intelligence_knowledge",
            "description": "General marketing intelligence and industry trends",
        },
    ]
    
    # Vector configuration
    vector_size = 1024  # bge-m3 dimension
    distance = Distance.COSINE
    
    print()
    print(f"📊 Creating {len(collections)} collections...")
    print(f"   Vector size: {vector_size} (bge-m3)")
    print(f"   Distance metric: {distance}")
    print()
    
    created = 0
    skipped = 0
    
    for collection in collections:
        name = collection["name"]
        description = collection["description"]
        
        try:
            # Check if exists
            exists = await qdrant.collection_exists(name)
            
            if exists:
                print(f"⏭️  {name} - already exists, skipping")
                skipped += 1
            else:
                # Create collection
                await qdrant.create_collection(
                    collection_name=name,
                    vector_size=vector_size,
                    distance=distance,
                )
                print(f"✅ {name} - created")
                print(f"   {description}")
                created += 1
        
        except Exception as e:
            print(f"❌ {name} - failed: {e}")
    
    print()
    print("=" * 60)
    print(f"✅ Setup complete!")
    print(f"   Created: {created} collections")
    print(f"   Skipped: {skipped} collections (already existed)")
    print("=" * 60)
    
    await qdrant.disconnect()
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
```

- [ ] **Step 2: Test setup script**

```bash
# Make sure Qdrant is running
docker-compose up -d qdrant

# Run setup script
python scripts/setup_qdrant.py
```

Expected output:
```
🔧 Setting up Qdrant collections for University...

✅ Connected to Qdrant at http://localhost:6333

📊 Creating 6 collections...
   Vector size: 1024 (bge-m3)
   Distance metric: cosine

✅ seo_knowledge - created
   SEO strategies, techniques, and best practices
✅ content_knowledge - created
   Content marketing, copywriting, and content strategy
✅ ads_knowledge - created
   Advertising campaigns, ad optimization, and PPC
✅ smm_knowledge - created
   Social media marketing and community management
✅ analytics_knowledge - created
   Analytics, metrics, and data-driven insights
✅ intelligence_knowledge - created
   General marketing intelligence and industry trends

============================================================
✅ Setup complete!
   Created: 6 collections
   Skipped: 0 collections (already existed)
============================================================
```

- [ ] **Step 3: Test idempotency (run again)**

```bash
python scripts/setup_qdrant.py
```

Expected output:
```
🔧 Setting up Qdrant collections for University...

✅ Connected to Qdrant at http://localhost:6333

📊 Creating 6 collections...
   Vector size: 1024 (bge-m3)
   Distance metric: cosine

⏭️  seo_knowledge - already exists, skipping
⏭️  content_knowledge - already exists, skipping
⏭️  ads_knowledge - already exists, skipping
⏭️  smm_knowledge - already exists, skipping
⏭️  analytics_knowledge - already exists, skipping
⏭️  intelligence_knowledge - already exists, skipping

============================================================
✅ Setup complete!
   Created: 0 collections
   Skipped: 6 collections (already existed)
============================================================
```

- [ ] **Step 4: Commit**

```bash
git add scripts/setup_qdrant.py
git commit -m "feat: add Qdrant setup script for collection initialization

Script creates 6 knowledge collections:
- seo_knowledge
- content_knowledge
- ads_knowledge
- smm_knowledge
- analytics_knowledge
- intelligence_knowledge

Features:
- Idempotent (safe to run multiple times)
- Clear progress output
- Error handling with helpful messages
- Vector size: 1024 (bge-m3)
- Distance: COSINE

Usage: python scripts/setup_qdrant.py

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 15: End-to-End Test

**Files:**
- Create: `scripts/test_university_core.py`

- [ ] **Step 1: Write end-to-end test script**

```python
# scripts/test_university_core.py
"""Complete end-to-end test of University core system"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from meai.agents.researcher import ResearcherAgent
from meai.agents.teacher import TeacherAgent
from meai.events.event_bus import EventBus
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage


def print_header(title: str):
    """Print section header"""
    print()
    print("=" * 60)
    print(f"TEST: {title}")
    print("=" * 60)


def print_success(message: str):
    """Print success message"""
    print(f"✅ {message}")


def print_error(message: str):
    """Print error message"""
    print(f"❌ {message}")


def print_info(message: str):
    """Print info message"""
    print(f"📋 {message}")


async def test_1_initialize_components():
    """Test 1: Initialize all components"""
    print_header("Initialize Components")
    
    try:
        # Event Bus
        event_bus = EventBus()
        print_success("Event Bus initialized")
        
        # Qdrant
        qdrant = QdrantClient(url="http://localhost:6333")
        await qdrant.connect()
        print_success("Qdrant connected (http://localhost:6333)")
        
        # Embeddings
        embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
        await embeddings.load()
        print_success(f"Embeddings model loaded (bge-m3, {embeddings.dimension} dimensions)")
        
        # Fallback Storage
        fallback = FallbackStorage(database_url="sqlite+aiosqlite:///:memory:")
        await fallback.initialize()
        print_success("Fallback storage initialized (SQLite in-memory)")
        
        # Researcher Agent
        researcher = ResearcherAgent(
            agent_id="researcher-test",
            event_bus=event_bus,
            database_url="sqlite+aiosqlite:///:memory:",
        )
        await researcher.initialize()
        print_success("Researcher Agent initialized")
        
        # Teacher Agent
        teacher = TeacherAgent(
            agent_id="teacher-test",
            event_bus=event_bus,
            qdrant_client=qdrant,
            embeddings_model=embeddings,
            fallback_storage=fallback,
            database_url="sqlite+aiosqlite:///:memory:",
        )
        await teacher.initialize()
        print_success("Teacher Agent initialized")
        
        return {
            "event_bus": event_bus,
            "qdrant": qdrant,
            "embeddings": embeddings,
            "fallback": fallback,
            "researcher": researcher,
            "teacher": teacher,
        }
    
    except Exception as e:
        print_error(f"Initialization failed: {e}")
        raise


async def test_2_research_to_teacher_to_qdrant(components: dict):
    """Test 2: Research → Teacher → Qdrant flow"""
    print_header("Research → Teacher → Qdrant")
    
    teacher = components["teacher"]
    researcher = components["researcher"]
    
    # Mock Perplexity response
    mock_findings = {
        "content": "SEO best practices for 2026 include: 1) Focus on user experience and Core Web Vitals (LCP, FID, CLS), 2) Create high-quality E-E-A-T content (Experience, Expertise, Authoritativeness, Trustworthiness), 3) Optimize for AI-powered search engines and voice search, 4) Build authoritative backlinks from trusted domains, 5) Implement comprehensive structured data markup (Schema.org)",
        "source": "https://perplexity.ai/search/seo-best-practices-2026",
        "sources": [
            "https://moz.com/blog/seo-trends-2026",
            "https://searchengineland.com/seo-2026-guide",
            "https://backlinko.com/seo-this-year",
        ],
        "metadata": {
            "topic": "seo",
            "date": "2026-05-02",
            "confidence": "high",
            "keywords": ["seo", "core web vitals", "e-e-a-t", "structured data"],
        },
    }
    
    print_info("Research request: 'SEO best practices 2026'")
    
    # Mock Researcher's Perplexity call
    with patch.object(researcher.perplexity, 'research', new_callable=AsyncMock) as mock_research:
        mock_research.return_value = mock_findings
        
        # Researcher collects findings
        from meai.agents.base_agent import Task
        task = Task(
            task_id="research-e2e-1",
            description="Research SEO best practices 2026",
            metadata={
                "capability": "research_topic",
                "topic": "SEO best practices 2026",
                "collection": "seo_knowledge",
            },
        )
        
        result = await researcher.execute_task(task)
        
        if result.status == "completed":
            findings_count = len(result.result.get("findings", {}).get("sources", []))
            print_success(f"Researcher collected findings ({findings_count} sources)")
        else:
            print_error("Researcher failed to collect findings")
            return False
    
    # Teacher evaluates and stores
    print_info("Teacher evaluating knowledge quality...")
    quality_score = await teacher.evaluate_knowledge(mock_findings)
    print_success(f"Knowledge evaluated (quality score: {quality_score:.1f}/10)")
    
    print_info("Teacher storing knowledge in Qdrant...")
    knowledge_id = await teacher.store_knowledge(mock_findings, "seo_knowledge")
    print_success(f"Knowledge stored in Qdrant (ID: {knowledge_id})")
    
    return True


async def test_3_search_knowledge(components: dict):
    """Test 3: Search for knowledge in Qdrant"""
    print_header("Search Knowledge")
    
    teacher = components["teacher"]
    
    print_info("Search query: 'SEO 2026'")
    
    results = await teacher.search_knowledge(
        query="SEO 2026",
        collection="seo_knowledge",
        limit=5,
        score_threshold=0.7,
    )
    
    if len(results) > 0:
        print_success(f"Found {len(results)} relevant results")
        
        top_result = results[0]
        print_info(f"Top result similarity: {top_result['similarity_score']:.2f}")
        print_info(f"Quality score: {top_result['quality_score']:.1f}/10")
        print_info(f"Content preview: {top_result['content'][:100]}...")
        
        return True
    else:
        print_error("No results found")
        return False


async def test_4_fallback_to_sqlite(components: dict):
    """Test 4: Fallback to SQLite when Qdrant unavailable"""
    print_header("Fallback to SQLite")
    
    teacher = components["teacher"]
    qdrant = components["qdrant"]
    fallback = components["fallback"]
    
    print_info("Simulating Qdrant outage...")
    
    # Mock Qdrant failure
    with patch.object(qdrant, 'upsert_points', side_effect=Exception("Qdrant unavailable")):
        knowledge = {
            "content": "Content marketing strategies for medical industry in 2026",
            "source": "https://perplexity.ai/search/medical-content-marketing",
            "sources": ["source1", "source2"],
            "metadata": {"topic": "content", "industry": "medical"},
        }
        
        print_info("Attempting to store knowledge (Qdrant down)...")
        knowledge_id = await teacher.store_knowledge(knowledge, "content_knowledge")
        print_success(f"Knowledge stored in SQLite fallback (ID: {knowledge_id})")
    
    # Verify in fallback storage
    pending = await fallback.get_pending_knowledge()
    
    if len(pending) > 0:
        print_success(f"Verified: {len(pending)} knowledge items in fallback storage")
        return True
    else:
        print_error("Fallback storage is empty")
        return False


async def test_5_qdrant_recovery_sync(components: dict):
    """Test 5: Sync fallback knowledge when Qdrant recovers"""
    print_header("Qdrant Recovery & Sync")
    
    teacher = components["teacher"]
    qdrant = components["qdrant"]
    fallback = components["fallback"]
    embeddings = components["embeddings"]
    
    print_info("Qdrant recovered, syncing fallback knowledge...")
    
    # Get pending knowledge
    pending = await fallback.get_pending_knowledge()
    initial_count = len(pending)
    print_info(f"Found {initial_count} pending knowledge items")
    
    # Sync to Qdrant
    synced = 0
    for knowledge in pending:
        try:
            from qdrant_client.models import PointStruct, Distance
            
            # Create collection if needed
            if not await qdrant.collection_exists(knowledge["collection"]):
                await qdrant.create_collection(
                    collection_name=knowledge["collection"],
                    vector_size=embeddings.dimension,
                    distance=Distance.COSINE,
                )
            
            # Sync to Qdrant
            point = PointStruct(
                id=knowledge["id"],
                vector=knowledge["vector"],
                payload={
                    "content": knowledge["content"],
                    "source": knowledge["source"],
                    "quality_score": knowledge["quality_score"],
                    "metadata": knowledge["metadata"],
                },
            )
            
            await qdrant.upsert_points(knowledge["collection"], [point])
            await fallback.mark_as_synced(knowledge["id"])
            synced += 1
        
        except Exception as e:
            print_error(f"Failed to sync {knowledge['id']}: {e}")
    
    print_success(f"Synced {synced}/{initial_count} knowledge items to Qdrant")
    
    # Verify fallback is empty
    pending_after = await fallback.get_pending_knowledge()
    
    if len(pending_after) == 0:
        print_success("Fallback storage cleared (all synced)")
        return True
    else:
        print_error(f"Fallback storage still has {len(pending_after)} items")
        return False


async def cleanup(components: dict):
    """Cleanup test resources"""
    print_header("Cleanup")
    
    try:
        # Delete test collections
        qdrant = components["qdrant"]
        
        collections = ["seo_knowledge", "content_knowledge"]
        for collection in collections:
            try:
                if await qdrant.collection_exists(collection):
                    await qdrant.client.delete_collection(collection)
                    print_success(f"Deleted collection: {collection}")
            except Exception as e:
                print_info(f"Could not delete {collection}: {e}")
        
        # Shutdown components
        await components["researcher"].shutdown()
        await components["teacher"].shutdown()
        await qdrant.disconnect()
        await components["fallback"].shutdown()
        
        print_success("All components shut down")
    
    except Exception as e:
        print_error(f"Cleanup failed: {e}")


async def main():
    """Run all tests"""
    print()
    print("🧪 Testing University Core System")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    components = None
    all_passed = True
    
    try:
        # Test 1: Initialize
        components = await test_1_initialize_components()
        
        # Test 2: Research → Teacher → Qdrant
        if not await test_2_research_to_teacher_to_qdrant(components):
            all_passed = False
        
        # Test 3: Search
        if not await test_3_search_knowledge(components):
            all_passed = False
        
        # Test 4: Fallback
        if not await test_4_fallback_to_sqlite(components):
            all_passed = False
        
        # Test 5: Recovery
        if not await test_5_qdrant_recovery_sync(components):
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

- [ ] **Step 2: Run end-to-end test**

```bash
# Make sure Qdrant is running
docker-compose up -d qdrant

# Run E2E test
python scripts/test_university_core.py
```

Expected output:
```
🧪 Testing University Core System
   Time: 2026-05-02 15:15:32

============================================================
TEST: Initialize Components
============================================================
✅ Event Bus initialized
✅ Qdrant connected (http://localhost:6333)
✅ Embeddings model loaded (bge-m3, 1024 dimensions)
✅ Fallback storage initialized (SQLite in-memory)
✅ Researcher Agent initialized
✅ Teacher Agent initialized

============================================================
TEST: Research → Teacher → Qdrant
============================================================
📋 Research request: 'SEO best practices 2026'
✅ Researcher collected findings (3 sources)
📋 Teacher evaluating knowledge quality...
✅ Knowledge evaluated (quality score: 9.0/10)
📋 Teacher storing knowledge in Qdrant...
✅ Knowledge stored in Qdrant (ID: knowledge-abc123)

============================================================
TEST: Search Knowledge
============================================================
📋 Search query: 'SEO 2026'
✅ Found 1 relevant results
📋 Top result similarity: 0.95
📋 Quality score: 9.0/10
📋 Content preview: SEO best practices for 2026 include: 1) Focus on user experience and Core Web Vitals (LCP...

============================================================
TEST: Fallback to SQLite
============================================================
📋 Simulating Qdrant outage...
📋 Attempting to store knowledge (Qdrant down)...
✅ Knowledge stored in SQLite fallback (ID: knowledge-def456)
✅ Verified: 1 knowledge items in fallback storage

============================================================
TEST: Qdrant Recovery & Sync
============================================================
📋 Qdrant recovered, syncing fallback knowledge...
📋 Found 1 pending knowledge items
✅ Synced 1/1 knowledge items to Qdrant
✅ Fallback storage cleared (all synced)

============================================================
TEST: Cleanup
============================================================
✅ Deleted collection: seo_knowledge
✅ Deleted collection: content_knowledge
✅ All components shut down

============================================================
🎉 ALL TESTS PASSED!
============================================================
```

- [ ] **Step 3: Commit**

```bash
git add scripts/test_university_core.py
git commit -m "test: add end-to-end test for University core system

Complete E2E test covering:
1. Component initialization (Qdrant, Embeddings, Agents)
2. Research → Teacher → Qdrant flow
3. Vector search in Qdrant
4. Fallback to SQLite when Qdrant unavailable
5. Recovery and sync from SQLite to Qdrant

Features:
- Clear progress output with emojis
- Mocked Perplexity API for reproducibility
- Automatic cleanup
- Exit code for CI/CD integration

Usage: python scripts/test_university_core.py

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Success Criteria

- [ ] ✅ Qdrant running in Docker
- [ ] ✅ Embeddings model (bge-m3) loaded and working
- [ ] ✅ SQLite fallback storage implemented
- [ ] ✅ Perplexity API integration working
- [ ] ✅ YouTube API integration working
- [ ] ✅ Telegram API integration working
- [ ] ✅ Researcher Agent collecting knowledge from all sources
- [ ] ✅ Teacher Agent evaluating and storing knowledge
- [ ] ✅ Knowledge searchable in Qdrant
- [ ] ✅ Fallback to SQLite when Qdrant unavailable
- [ ] ✅ Event Bus communication working
- [ ] ✅ All unit tests passing
- [ ] ✅ All integration tests passing
- [ ] ✅ End-to-end test passing

---

## Next Steps

After completing this plan:

1. **Plan 2: Magisters + Hybrid Search**
   - Implement 6 Magister agents
   - Hybrid search (local → Teacher → Researcher)
   - Magister-specific Qdrant collections

2. **Plan 3: Experience Learning**
   - Experience analysis in Magisters
   - Quality score updates in Teacher
   - Deprecation system
   - Success/failure tracking

---

## Notes

- **Model download:** First run of embeddings tests will download bge-m3 (~2GB)
- **Qdrant data:** Stored in `./data/qdrant/` (gitignored)
- **API keys:** Set environment variables:
  - `PERPLEXITY_API_KEY`
  - `YOUTUBE_API_KEY`
  - `TELEGRAM_API_ID`
  - `TELEGRAM_API_HASH`
- **Testing:** Run Qdrant before integration tests: `docker-compose up -d qdrant`

