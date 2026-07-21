"""LLM Ingest — raw/executions → wiki/patterns (Pattern Extraction).

Flow: reads raw execution events, sends to LLM via OmniRoute,
saves extracted patterns in wiki/patterns/, updates index.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Ты — Knowledge Extraction Agent. Проанализируй результат CI-анализа и извлеки:

1. **Что сработало хорошо** (successful patterns) — какие агенты дали полезные результаты, какие данные оказались ценными
2. **Что можно улучшить** (improvement opportunities) — где данные неполные, где нужны дополнительные источники
3. **Неожиданные находки** (surprising findings) — что обнаружилось такого, чего не ожидали
4. **Конкретные цифры и метрики** — ключевые показатели из результатов

Формат: Markdown, каждая секция с заголовком ##, конкретные данные, без общих фраз."""


class LLMIngest:
    """Extracts patterns from raw execution events via LLM."""

    def __init__(self, vault):
        self.vault = vault

    async def extract_patterns(self, execution_id: str) -> list[str]:
        """Extract patterns from one or all (execution_id='latest') executions.

        Returns list of pattern file names created.
        """
        if execution_id == "latest":
            executions = self.vault.get_latest_executions(1)
            if not executions:
                logger.warning("No executions to extract patterns from")
                return []
            execution = executions[0]
            execution_id = execution.get("event_id", "unknown")
        else:
            execution = self.vault.get_execution(execution_id)
            if execution is None:
                logger.warning(f"Execution {execution_id} not found")
                return []

        pattern_name = await self._extract_single(execution_id, execution)
        return [pattern_name] if pattern_name else []

    async def extract_all(self) -> list[str]:
        """Extract patterns from all unprocessed executions."""
        raw_files = sorted(self.vault.raw.glob("*.json"), key=lambda p: p.stat().st_mtime)
        existing_patterns = {p.stem for p in self.vault.wiki_patterns.glob("*.md")}

        created = []
        for f in raw_files:
            source_id = f"source-{f.stem}"
            if source_id in existing_patterns:
                continue
            try:
                execution = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            pattern_name = await self._extract_single(f.stem, execution)
            if pattern_name:
                created.append(pattern_name)
                existing_patterns.add(pattern_name)

        return created

    async def _extract_single(self, execution_id: str, execution: dict) -> str | None:
        """Extract patterns from a single execution via LLM.

        Returns pattern file name or None if extraction failed.
        """
        event_type = execution.get("event_type", "unknown")
        payload = execution.get("payload", {})

        # Build context for LLM
        context = f"## Execution Event\n\n"
        context += f"- **Event ID:** {execution_id}\n"
        context += f"- **Event Type:** {event_type}\n"
        context += f"- **Payload keys:** {list(payload.keys())}\n"

        # Include payload summary (limit size)
        payload_str = json.dumps(payload, indent=2, ensure_ascii=False, default=str)
        if len(payload_str) > 4000:
            payload_str = payload_str[:4000] + "\n...(truncated)"
        context += f"\n<payload>\n{payload_str}\n</payload>\n"

        # Call LLM via OmniRoute
        try:
            from app.omniroute_direct import chat

            response = chat([
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": context},
            ])

            if not response or response.startswith("Извините"):
                logger.warning(f"LLM extraction failed for {execution_id}: {response}")
                return None

        except Exception as e:
            logger.exception(f"LLM call failed for {execution_id}")
            return None

        # Save pattern
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        pattern_name = f"pattern-{timestamp}"

        content = f"# Pattern: {pattern_name}\n\n"
        content += f"**Source:** {execution_id}\n"
        content += f"**Event Type:** {event_type}\n"
        content += f"**Extracted:** {datetime.now(timezone.utc).isoformat()}\n\n"
        content += "---\n\n"
        content += response

        pattern_path = self.vault.wiki_patterns / f"{pattern_name}.md"
        pattern_path.write_text(content, encoding="utf-8")

        # Update index
        await self._update_index(pattern_name, execution_id, event_type)

        logger.info(f"[LLM Ingest] Pattern extracted: {pattern_name} ← {execution_id}")
        return pattern_name

    async def _update_index(self, pattern_name: str, source_id: str, event_type: str) -> None:
        """Update wiki/patterns/index.md with new pattern entry."""
        index_path = self.vault.wiki_patterns / "index.md"
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

        entry = f"| {timestamp} | [{pattern_name}](./{pattern_name}.md) | {event_type} | {source_id} |\n"

        if index_path.exists():
            content = index_path.read_text(encoding="utf-8")
            # Append after table header
            if "|---|---|---|" in content:
                content += entry
            else:
                content = _build_index_table() + entry
        else:
            content = _build_index_table() + entry

        index_path.write_text(content, encoding="utf-8")


def _build_index_table() -> str:
    return (
        "# Wiki Patterns Index\n\n"
        "| Extracted | Pattern | Event Type | Source |\n"
        "|---|---|---|---|\n"
    )
