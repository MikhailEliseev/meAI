"""Hermes Knowledge Vault — execution experience storage (LLM Wiki Pattern).

Layers:
  raw/executions/   — immutable execution events from EventBus
  wiki/patterns/    — LLM-extracted patterns from executions
  wiki/learnings/   — Teacher-enriched external knowledge
  decisions/rules/  — validated, codified rules

Flow: raw → (LLM ingest) → wiki/patterns → (validation) → decisions/rules
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class HermesKnowledgeVault:
    """Manages Hermes knowledge across the LLM Wiki Pattern layers."""

    def __init__(self, base_path: str = "."):
        self.base = Path(base_path)
        self.raw = self.base / "raw" / "executions"
        self.wiki_patterns = self.base / "wiki" / "patterns"
        self.wiki_learnings = self.base / "wiki" / "learnings"
        self.decisions = self.base / "decisions" / "rules"

        for d in [self.raw, self.wiki_patterns, self.wiki_learnings, self.decisions]:
            d.mkdir(parents=True, exist_ok=True)

    # ── Ingest (EventBus → raw) ────────────────────────────────────────

    async def ingest_execution(self, event) -> str:
        """Store execution event from EventBus in raw/executions/.

        Args:
            event: Event dataclass (event_type, payload, event_id, timestamp)

        Returns:
            event_id for traceability
        """
        event_id = getattr(event, "event_id", event.payload.get("correlation_id", "unknown"))
        timestamp = datetime.now(timezone.utc).isoformat()

        doc = {
            "event_id": event_id,
            "event_type": getattr(event, "event_type", "unknown"),
            "payload": event.payload if isinstance(event.payload, dict) else {},
            "ingested_at": timestamp,
        }

        file_path = self.raw / f"{event_id}.json"
        file_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False, default=str))

        logger.info(f"[Hermes Vault] Ingested execution: {event_id} → raw/executions/")
        return event_id

    async def ingest_agent_result(self, event) -> str:
        """Store agent-level event (ci.agent.completed) from EventBus."""
        return await self.ingest_execution(event)

    # ── Query ──────────────────────────────────────────────────────────

    async def query_context(self, domain: str, action: str) -> dict:
        """Search knowledge vault for patterns relevant to domain+action.

        Searches: wiki/patterns/, wiki/learnings/{domain}/, decisions/rules/
        """
        patterns = self._list_files(self.wiki_patterns)
        learnings = self._list_files(self.wiki_learnings / domain)
        rules = self._list_files(self.decisions)

        relevant = {"patterns": [], "learnings": [], "rules": [], "query": f"{domain}:{action}"}

        keyword = action.split("_")[0] if "_" in action else action

        for p in patterns:
            if domain in p.stem or keyword in p.stem:
                relevant["patterns"].append({"name": p.stem, "content": p.read_text(encoding="utf-8")[:2000]})

        for l in learnings:
            relevant["learnings"].append({"name": l.stem, "content": l.read_text(encoding="utf-8")[:2000]})

        for r in rules:
            if domain in r.stem or keyword in r.stem:
                relevant["rules"].append({"name": r.stem, "content": r.read_text(encoding="utf-8")[:2000]})

        return relevant

    # ── Learnings ──────────────────────────────────────────────────────

    async def store_learning(self, domain: str, knowledge: dict) -> str:
        """Store Teacher-enriched knowledge in wiki/learnings/{domain}/."""
        domain_dir = self.wiki_learnings / domain
        domain_dir.mkdir(parents=True, exist_ok=True)

        source = knowledge.get("source", "teacher")
        name = knowledge.get("name", f"learning-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}")
        file_path = domain_dir / f"{name}.md"

        content = f"# {name}\n\n"
        content += f"**Source:** {source}\n"
        content += f"**Stored:** {datetime.now(timezone.utc).isoformat()}\n"
        content += f"**Quality:** {knowledge.get('quality_score', 'N/A')}\n\n"
        content += knowledge.get("content", "")

        file_path.write_text(content, encoding="utf-8")
        logger.info(f"[Hermes Vault] Stored learning: {name} → wiki/learnings/{domain}/")
        return str(file_path)

    # ── Status ─────────────────────────────────────────────────────────

    async def get_status(self) -> dict:
        """Return vault health status."""
        executions = list(self.raw.glob("*.json"))
        last_ingest = None
        if executions:
            last_file = max(executions, key=lambda p: p.stat().st_mtime)
            try:
                data = json.loads(last_file.read_text(encoding="utf-8"))
                last_ingest = data.get("ingested_at")
            except (json.JSONDecodeError, KeyError):
                pass

        return {
            "executions_count": len(executions),
            "patterns_count": len(list(self.wiki_patterns.glob("*.md"))),
            "learnings_count": len(list(self.wiki_learnings.rglob("*.md"))),
            "rules_count": len(list(self.decisions.glob("*.md"))),
            "last_ingest": last_ingest,
            "loop_health": "active" if executions else "idle",
        }

    # ── Helpers ────────────────────────────────────────────────────────

    def _list_files(self, directory: Path) -> list[Path]:
        if not directory.exists():
            return []
        return sorted(directory.glob("*.md")) + sorted(directory.glob("*.json"))

    def get_execution(self, execution_id: str) -> Optional[dict]:
        """Read a specific execution from raw/."""
        file_path = self.raw / f"{execution_id}.json"
        if file_path.exists():
            return json.loads(file_path.read_text(encoding="utf-8"))
        return None

    def get_latest_executions(self, limit: int = 10) -> list[dict]:
        """Get latest execution events from raw/."""
        files = sorted(self.raw.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        results = []
        for f in files[:limit]:
            try:
                results.append(json.loads(f.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                continue
        return results
