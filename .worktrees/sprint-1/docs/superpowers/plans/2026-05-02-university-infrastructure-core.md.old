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

**Implementation:** Teacher Agent inheriting from `Agent` base class.

**Capabilities:**
- `evaluate_knowledge` — score knowledge quality (1-10)
- `store_knowledge` — save to Qdrant with embeddings
- `distribute_to_magisters` — notify relevant Magisters
- `search_knowledge` — vector search in Qdrant

**Workflow (receiving knowledge):**
1. Receive findings from Researcher
2. Evaluate quality (source, relevance, completeness)
3. Generate embeddings via EmbeddingsModel
4. Store in Qdrant (or fallback to SQLite if unavailable)
5. Notify relevant Magisters via Event Bus

**Database tables:**
- `teacher_knowledge`
- `teacher_evaluations`
- `teacher_distributions`

**Qdrant collections:**
- `seo_knowledge`
- `content_knowledge`
- `ads_knowledge`
- `smm_knowledge`
- `analytics_knowledge`
- `intelligence_knowledge`

**Tests:** Test evaluation logic, test Qdrant storage, test fallback to SQLite, test Event Bus

**Commit:** `feat: add Teacher Agent with knowledge evaluation and storage`

---

## Task 11: Teacher Agent - Search & Distribution

**Files:**
- Modify: `src/meai/agents/teacher.py`
- Modify: `tests/unit/test_teacher.py`

**Implementation:** Add search and distribution capabilities to Teacher.

**New methods:**
- `search_knowledge(query: str, collection: str, limit: int) -> list` — vector search
- `handle_magister_query(query: dict) -> dict` — handle Magister questions
- `request_research(topic: str) -> None` — request Researcher to investigate

**Workflow (Magister query):**
1. Receive question from Magister
2. Generate query embedding
3. Search in relevant Qdrant collection
4. If not found (similarity < threshold) → request Researcher
5. Return results to Magister

**Tests:** Test search functionality, test Magister query handling, test Researcher requests

**Commit:** `feat: add search and distribution to Teacher Agent`

---

## Task 12: Integration Test - Researcher → Teacher

**Files:**
- Create: `tests/integration/test_researcher_teacher_flow.py`

**Implementation:** End-to-end test of knowledge flow from Researcher to Teacher.

**Test scenario:**
1. Start Qdrant (Docker)
2. Initialize Researcher and Teacher agents
3. Teacher requests research on topic
4. Researcher uses Perplexity (mocked) to find knowledge
5. Researcher sends findings to Teacher via Event Bus
6. Teacher evaluates and stores in Qdrant
7. Verify knowledge is in Qdrant with correct metadata

**Commit:** `test: add integration test for Researcher → Teacher flow`

---

## Task 13: Integration Test - Qdrant Fallback

**Files:**
- Create: `tests/integration/test_qdrant_integration.py`

**Implementation:** Test Qdrant fallback to SQLite when unavailable.

**Test scenarios:**
1. **Normal operation:** Qdrant available, knowledge stored successfully
2. **Fallback:** Qdrant unavailable, knowledge stored in SQLite
3. **Recovery:** Qdrant comes back online, SQLite knowledge synced to Qdrant

**Commit:** `test: add Qdrant fallback integration tests`

---

## Task 14: Setup Script

**Files:**
- Create: `scripts/setup_qdrant.py`

**Implementation:** Script to initialize Qdrant collections.

**Functionality:**
- Check if Qdrant is running
- Create all 6 knowledge collections (seo, content, ads, smm, analytics, intelligence)
- Set vector size to 1024 (bge-m3 dimension)
- Set distance metric to COSINE

**Usage:**
```bash
python scripts/setup_qdrant.py
```

**Commit:** `feat: add Qdrant setup script for collection initialization`

---

## Task 15: End-to-End Test

**Files:**
- Create: `scripts/test_university_core.py`

**Implementation:** Complete end-to-end test of University core system.

**Test flow:**
1. Start Qdrant
2. Initialize all components (Embeddings, Qdrant, Researcher, Teacher)
3. Teacher requests research: "SEO best practices 2026"
4. Researcher collects knowledge (Perplexity mocked)
5. Teacher evaluates and stores
6. Search for knowledge: "SEO 2026"
7. Verify results are relevant
8. Test fallback: stop Qdrant, store knowledge, restart Qdrant, verify sync

**Output:**
```
🧪 Testing University Core System

============================================================
TEST 1: Initialize Components
============================================================
✅ Qdrant connected
✅ Embeddings model loaded (bge-m3, 1024 dimensions)
✅ Researcher initialized
✅ Teacher initialized

============================================================
TEST 2: Research → Teacher → Qdrant
============================================================
📋 Research request: "SEO best practices 2026"
✅ Researcher collected 5 findings
✅ Teacher evaluated knowledge (avg score: 8.2)
✅ Knowledge stored in Qdrant (seo_knowledge collection)

============================================================
TEST 3: Search Knowledge
============================================================
🔍 Search query: "SEO 2026"
✅ Found 3 relevant results
✅ Top result similarity: 0.92

============================================================
TEST 4: Fallback to SQLite
============================================================
⚠️  Stopping Qdrant...
✅ Knowledge stored in SQLite fallback
✅ Qdrant restarted
✅ SQLite knowledge synced to Qdrant

============================================================
🎉 ALL TESTS PASSED!
============================================================
```

**Commit:** `test: add end-to-end test for University core system`

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
