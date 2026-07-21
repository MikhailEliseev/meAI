"""Teacher → Hermes Knowledge Sync.

Синхронизирует знания из Teacher (Qdrant) в Hermes wiki/learnings/{domain}/.
Вызывается при старте Hermes или вручную через CLI.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class TeacherSync:
    """Syncs knowledge from Teacher Agent (Qdrant) to Hermes vault."""

    def __init__(self, vault, teacher_agent=None):
        self.vault = vault
        self.teacher = teacher_agent

    async def sync_domain(self, domain: str) -> int:
        """Sync knowledge for one domain from Teacher to Hermes.

        Returns count of learnings stored.
        """
        collection = f"{domain}_knowledge"
        results = []

        if self.teacher is not None:
            try:
                results = await self._search_teacher(domain, collection)
            except Exception as e:
                logger.warning(f"Teacher search failed for {domain}: {e}")

        if not results:
            logger.info(f"No Teacher knowledge to sync for {domain}")
            return 0

        stored = 0
        for r in results:
            await self.vault.store_learning(domain, {
                "source": "teacher",
                "name": f"teacher-{domain}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{stored}",
                "content": r.get("content", ""),
                "quality_score": r.get("score", 50),
            })
            stored += 1

        logger.info(f"[TeacherSync] Synced {stored} learnings for {domain}")
        return stored

    async def sync_all_domains(self) -> dict[str, int]:
        """Sync all knowledge domains."""
        results = {}
        for domain in ["seo", "content", "ads", "general"]:
            results[domain] = await self.sync_domain(domain)
        return results

    async def _search_teacher(self, domain: str, collection: str) -> list[dict]:
        """Search Teacher's Qdrant collections for best practices."""
        query = f"best practices {domain} marketing analysis"
        query_embedding = await self.teacher.embeddings.encode(query)

        try:
            if await self.teacher.qdrant.collection_exists(collection):
                hits = await self.teacher.qdrant.search(
                    collection_name=collection,
                    query_vector=query_embedding,
                    limit=10,
                )
                return [
                    {
                        "content": h.payload.get("content", ""),
                        "score": h.score,
                        "collection": collection,
                        "source": h.payload.get("source", "teacher"),
                    }
                    for h in hits
                ]
        except Exception as e:
            logger.warning(f"Qdrant search failed for {collection}: {e}")

        return []
