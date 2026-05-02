"""Teacher Agent - evaluates and stores knowledge in University"""

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from qdrant_client.models import PointStruct, Distance
from sqlalchemy import text

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage
from meai.storage.database import Database


class TeacherAgent(Agent):
    """Teacher Agent - evaluates knowledge quality and stores in Qdrant

    Capabilities:
    - evaluate_knowledge: Assess quality of knowledge from sources
    - store_knowledge: Store validated knowledge in Qdrant/fallback
    - search_knowledge: Search for relevant knowledge
    """

    def __init__(
        self,
        agent_id: str = "teacher",
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian",
        qdrant_client: QdrantClient | None = None,
        embeddings_model: EmbeddingsModel | None = None,
        fallback_storage: FallbackStorage | None = None,
    ):
        """Initialize Teacher Agent

        Args:
            agent_id: Unique agent identifier
            database_url: Database URL for agent state
            vault_path: Path to Obsidian vault
            qdrant_client: Qdrant client for vector storage
            embeddings_model: Embeddings model for vectorization
            fallback_storage: SQLite fallback storage
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="teacher",
            database_url=database_url,
            vault_path=vault_path,
        )

        self.qdrant = qdrant_client or QdrantClient()
        self.embeddings = embeddings_model or EmbeddingsModel()
        self.fallback = fallback_storage or FallbackStorage()

        # Collections for different knowledge domains
        self.collections = [
            "seo_knowledge",
            "content_knowledge",
            "ads_knowledge",
            "general_knowledge",
        ]

        # Quality thresholds
        self.min_quality_score = 60  # Minimum score to store knowledge

    async def initialize(self) -> None:
        """Initialize Teacher Agent"""
        await super().initialize()
        await self.qdrant.connect()
        await self.embeddings.load()
        await self.fallback.initialize()

        # Create Qdrant collections
        for collection in self.collections:
            if not await self.qdrant.collection_exists(collection):
                await self.qdrant.create_collection(
                    collection_name=collection,
                    vector_size=1024,  # bge-m3 dimension
                    distance=Distance.COSINE,
                )

    async def shutdown(self) -> None:
        """Shutdown Teacher Agent"""
        await self.qdrant.disconnect()
        await self.fallback.shutdown()
        await super().shutdown()

    def get_capabilities(self) -> list[str]:
        """Get list of teacher capabilities

        Returns:
            List of action names
        """
        return [
            "evaluate_knowledge",
            "store_knowledge",
            "search_knowledge",
            "handle_magister_query",
        ]

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute teacher task

        Args:
            task: Task to execute

        Returns:
            Task result
        """
        start_time = datetime.now(timezone.utc)

        try:
            if task.action == "evaluate_knowledge":
                result = await self._evaluate_knowledge(task)
            elif task.action == "store_knowledge":
                result = await self._store_knowledge(task)
            elif task.action == "search_knowledge":
                result = await self._search_knowledge(task)
            elif task.action == "handle_magister_query":
                result = await self._handle_magister_query(task)
            else:
                raise ValueError(f"Unknown action: {task.action}")

            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="success",
                result=result,
                error=None,
                duration_seconds=duration,
                completed_at=end_time,
            )

        except Exception as e:
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="failed",
                result={},
                error=str(e),
                duration_seconds=duration,
                completed_at=end_time,
            )

    async def _evaluate_knowledge(self, task: Task) -> dict[str, Any]:
        """Evaluate knowledge quality

        Args:
            task: Task with knowledge content and source

        Returns:
            Evaluation result with quality score
        """
        content = task.description

        # Extract source if provided
        source = "unknown"
        if "from" in content:
            parts = content.split("from")
            if len(parts) > 1:
                source = parts[1].strip()
                content = parts[0].strip()

        # Simple quality scoring based on:
        # - Content length (longer = better, up to a point)
        # - Source trustworthiness
        # - Presence of specific keywords

        quality_score = 50  # Base score

        # Length scoring (0-20 points)
        if len(content) > 100:
            quality_score += 10
        if len(content) > 500:
            quality_score += 10

        # Source scoring (0-30 points)
        trusted_domains = ["moz.com", "google.com", "semrush.com", "ahrefs.com"]
        if any(domain in source for domain in trusted_domains):
            quality_score += 30

        # Keyword scoring (0-20 points)
        quality_keywords = ["best practices", "research", "data", "analysis", "strategy"]
        keyword_count = sum(1 for kw in quality_keywords if kw.lower() in content.lower())
        quality_score += min(keyword_count * 5, 20)

        # Cap at 100
        quality_score = min(quality_score, 100)

        return {
            "content": content,
            "source": source,
            "quality_score": quality_score,
            "evaluation": "high" if quality_score >= 80 else "medium" if quality_score >= 60 else "low",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _store_knowledge(self, task: Task) -> dict[str, Any]:
        """Store knowledge in Qdrant or fallback

        Args:
            task: Task with knowledge content

        Returns:
            Storage result with knowledge ID
        """
        content = task.description

        # Evaluate quality first
        eval_result = await self._evaluate_knowledge(task)
        quality_score = eval_result["quality_score"]

        # Only store if quality is sufficient
        if quality_score < self.min_quality_score:
            return {
                "stored": False,
                "reason": f"Quality score {quality_score} below threshold {self.min_quality_score}",
                "quality_score": quality_score,
            }

        # Generate embedding
        embedding = await self.embeddings.encode(content)

        # Determine collection (default to general_knowledge)
        collection = "general_knowledge"
        if "seo" in content.lower():
            collection = "seo_knowledge"
        elif "content" in content.lower():
            collection = "content_knowledge"
        elif "ads" in content.lower() or "advertising" in content.lower():
            collection = "ads_knowledge"

        knowledge_id = f"knowledge-{uuid4().hex[:8]}"

        # Try to store in Qdrant
        try:
            point = PointStruct(
                id=knowledge_id,
                vector=embedding,
                payload={
                    "content": content,
                    "quality_score": quality_score,
                    "source": eval_result.get("source", "unknown"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

            await self.qdrant.upsert_points(
                collection_name=collection,
                points=[point],
            )

            stored_in = "qdrant"

        except Exception as e:
            # Fallback to SQLite
            knowledge_id = await self.fallback.store_knowledge(
                content=content,
                embedding=embedding,
                metadata={
                    "quality_score": quality_score,
                    "source": eval_result.get("source", "unknown"),
                    "collection": collection,
                },
            )
            stored_in = "fallback"

        return {
            "stored": True,
            "knowledge_id": knowledge_id,
            "collection": collection,
            "stored_in": stored_in,
            "quality_score": quality_score,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _search_knowledge(self, task: Task) -> dict[str, Any]:
        """Search for relevant knowledge

        Args:
            task: Task with search query

        Returns:
            Search results
        """
        query = task.description

        # Generate query embedding
        query_embedding = await self.embeddings.encode(query)

        results = []

        # Search in Qdrant collections
        try:
            for collection in self.collections:
                if await self.qdrant.collection_exists(collection):
                    search_results = await self.qdrant.search(
                        collection_name=collection,
                        query_vector=query_embedding,
                        limit=5,
                    )

                    for hit in search_results:
                        results.append({
                            "content": hit.payload.get("content", ""),
                            "score": hit.score,
                            "collection": collection,
                            "source": hit.payload.get("source", "unknown"),
                        })

        except Exception:
            # Fallback to SQLite search
            fallback_results = await self.fallback.search_knowledge(query, limit=10)
            for item in fallback_results:
                results.append({
                    "content": item["content"],
                    "score": 0.5,  # Default score for fallback
                    "collection": item["metadata"].get("collection", "unknown"),
                    "source": item["metadata"].get("source", "unknown"),
                })

        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)

        return {
            "query": query,
            "results": results[:10],  # Top 10 results
            "count": len(results),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _handle_magister_query(self, task: Task) -> dict[str, Any]:
        """Handle query from Magister agent

        Args:
            task: Task with Magister query in description

        Returns:
            Search results for Magister
        """
        # Parse query from task description
        # Format: "query: <text> | collection: <name> | magister_id: <id>"
        query_text = task.description
        collection = None
        magister_id = None

        # Simple parsing
        if "|" in query_text:
            parts = query_text.split("|")
            for part in parts:
                if "query:" in part:
                    query_text = part.split("query:")[1].strip()
                elif "collection:" in part:
                    collection = part.split("collection:")[1].strip()
                elif "magister_id:" in part:
                    magister_id = part.split("magister_id:")[1].strip()

        # Generate query embedding
        query_embedding = await self.embeddings.encode(query_text)

        results = []

        # Search in specified collection or all collections
        collections_to_search = [collection] if collection else self.collections

        try:
            for coll in collections_to_search:
                if await self.qdrant.collection_exists(coll):
                    search_results = await self.qdrant.search(
                        collection_name=coll,
                        query_vector=query_embedding,
                        limit=5,
                    )

                    for hit in search_results:
                        results.append({
                            "content": hit.payload.get("content", ""),
                            "score": hit.score,
                            "collection": coll,
                            "source": hit.payload.get("source", "unknown"),
                        })

        except Exception:
            # Fallback to SQLite search
            fallback_results = await self.fallback.search_knowledge(query_text, limit=10)
            for item in fallback_results:
                results.append({
                    "content": item["content"],
                    "score": 0.5,
                    "collection": item["metadata"].get("collection", "unknown"),
                    "source": item["metadata"].get("source", "unknown"),
                })

        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)

        return {
            "status": "success",
            "query": query_text,
            "magister_id": magister_id,
            "results": results[:10],
            "count": len(results),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
