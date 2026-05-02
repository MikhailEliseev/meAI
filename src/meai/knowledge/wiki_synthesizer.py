"""Wiki-style knowledge synthesis (Karpathy pattern)"""

import re
from typing import Any
from collections import defaultdict


class WikiSynthesizer:
    """Synthesize knowledge into wiki-style pages with cross-references

    Based on Karpathy's LLM-maintained wiki pattern:
    - Extract wikilinks [[topic]] from content
    - Build cross-reference graph
    - Merge duplicate/related knowledge
    - Create backlinks
    """

    def __init__(self):
        """Initialize synthesizer"""
        self.wikilink_pattern = re.compile(r'\[\[([^\]]+)\]\]')

    def extract_wikilinks(self, content: str) -> list[str]:
        """Extract wikilinks from content

        Args:
            content: Text content with [[wikilinks]]

        Returns:
            List of normalized wikilink topics
        """
        matches = self.wikilink_pattern.findall(content)
        return [self.normalize_wikilink(link) for link in matches]

    def normalize_wikilink(self, link: str) -> str:
        """Normalize wikilink text

        Args:
            link: Raw wikilink text

        Returns:
            Normalized lowercase link
        """
        return link.strip().lower()

    def build_cross_references(
        self, knowledge_items: list[dict[str, Any]]
    ) -> dict[str, list[str]]:
        """Build cross-reference graph from knowledge items

        Args:
            knowledge_items: List of knowledge items with id and content

        Returns:
            Dictionary mapping wikilink to list of knowledge IDs that reference it
        """
        graph = defaultdict(list)

        for item in knowledge_items:
            content = item.get("content", "")
            item_id = item.get("id", "")

            # Extract all wikilinks from this item
            links = self.extract_wikilinks(content)

            # Add this item to each wikilink's reference list
            for link in links:
                if item_id not in graph[link]:
                    graph[link].append(item_id)

        return dict(graph)

    async def synthesize(
        self, knowledge_items: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Synthesize multiple knowledge items into a unified structure

        Args:
            knowledge_items: List of knowledge items to synthesize

        Returns:
            Synthesized knowledge with topic, content, and wikilinks
        """
        if not knowledge_items:
            return {
                "topic": "unknown",
                "content": "",
                "wikilinks": [],
                "cross_references": {},
            }

        # Get primary topic from first item
        topic = knowledge_items[0].get("topic", "unknown")

        # Collect all wikilinks
        all_wikilinks = set()
        for item in knowledge_items:
            content = item.get("content", "")
            links = self.extract_wikilinks(content)
            all_wikilinks.update(links)

        # Build cross-reference graph
        cross_refs = self.build_cross_references(knowledge_items)

        # Merge content (simple concatenation for now)
        merged_content = "\n\n".join(
            item.get("content", "") for item in knowledge_items
        )

        return {
            "topic": topic,
            "content": merged_content,
            "wikilinks": sorted(list(all_wikilinks)),
            "cross_references": cross_refs,
            "item_count": len(knowledge_items),
        }

    def create_backlinks(
        self, cross_references: dict[str, list[str]]
    ) -> dict[str, list[str]]:
        """Create backlinks from cross-references

        Args:
            cross_references: Forward references (topic -> items that mention it)

        Returns:
            Backlinks (item -> topics it mentions)
        """
        backlinks = defaultdict(list)

        for topic, item_ids in cross_references.items():
            for item_id in item_ids:
                if topic not in backlinks[item_id]:
                    backlinks[item_id].append(topic)

        return dict(backlinks)
