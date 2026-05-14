"""
Content Brief Generator - Automated Content Brief Creation.

Creates detailed content briefs for writers based on target keywords
and competitor analysis.

Based on: CI Content Analyzer + Keyword Research Agent
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import structlog

from AIM.src.aim.subagents.competitive_intel.agents.ci_content_improved import (
    CIContentAgentImproved,
)
from AIM.src.aim.subagents.seo.keyword_research_agent import KeywordResearchAgent


@dataclass
class HeaderStructure:
    """Recommended header structure."""

    level: int  # H1, H2, H3
    text: str
    keywords: list[str]


@dataclass
class TopicCoverage:
    """Topic that should be covered."""

    topic: str
    priority: str  # high, medium, low
    reason: str
    competitor_coverage: int  # How many competitors cover this


@dataclass
class QuestionToAnswer:
    """Question that content should answer."""

    question: str
    priority: str  # high, medium, low
    source: str  # competitor URL or "user intent"


@dataclass
class ContentBrief:
    """Complete content brief."""

    target_keyword: str
    timestamp: str

    # Keyword analysis
    search_volume: int
    keyword_difficulty: float
    search_intent: str

    # Content recommendations
    recommended_word_count: int
    word_count_range: tuple[int, int]
    tone: str  # professional, casual, technical

    # Structure
    header_structure: list[HeaderStructure]

    # Topics
    topics_to_cover: list[TopicCoverage]
    total_topics: int

    # Questions
    questions_to_answer: list[QuestionToAnswer]
    total_questions: int

    # Competitor insights
    competitor_avg_word_count: int
    competitor_urls: list[str]
    top_performing_competitor: str | None

    # SEO recommendations
    title_suggestions: list[str]
    meta_description_suggestion: str


class ContentBriefGenerator:
    """
    Content Brief Generator.

    Creates detailed content briefs for writers based on
    keyword research and competitor analysis.
    """

    def __init__(
        self,
        semrush_api_key: str | None = None,
        ahrefs_api_key: str | None = None,
    ):
        """
        Initialize Content Brief Generator.

        Args:
            semrush_api_key: SEMrush API key for keyword research
            ahrefs_api_key: Ahrefs API key for keyword research
        """
        self.logger = structlog.get_logger()
        self.keyword_agent = KeywordResearchAgent(
            semrush_api_key=semrush_api_key,
            ahrefs_api_key=ahrefs_api_key,
        )
        self.content_analyzer = CIContentAgentImproved(
            agent_id="ci-content-brief-helper"
        )

    async def generate(
        self,
        target_keyword: str,
        competitor_urls: list[str],
        target_word_count: int | None = None,
    ) -> ContentBrief:
        """
        Generate content brief.

        Args:
            target_keyword: Target keyword for content
            competitor_urls: Competitor URLs to analyze (3-5 recommended)
            target_word_count: Target word count (None = auto-calculate)

        Returns:
            Complete content brief with recommendations
        """
        self.logger.info(
            "content_brief_generation_start",
            keyword=target_keyword,
            competitors=len(competitor_urls),
        )

        # Step 1: Keyword research
        keyword_data = await self._analyze_keyword(target_keyword)

        # Step 2: Competitor analysis
        competitor_analysis = await self._analyze_competitors(competitor_urls)

        # Step 3: Calculate word count
        word_count = self._calculate_word_count(
            competitor_analysis,
            target_word_count,
        )

        # Step 4: Generate header structure
        headers = self._generate_header_structure(
            target_keyword,
            competitor_analysis,
        )

        # Step 5: Identify topics to cover
        topics = self._identify_topics(
            competitor_analysis,
        )

        # Step 6: Generate questions
        questions = self._generate_questions(
            target_keyword,
            keyword_data["intent"],
        )

        # Step 7: SEO recommendations
        title_suggestions = self._generate_title_suggestions(target_keyword)
        meta_description = self._generate_meta_description(
            target_keyword,
            keyword_data["intent"],
        )

        # Step 8: Determine tone
        tone = self._determine_tone(keyword_data["intent"])

        # Find top performer
        top_performer = None
        if competitor_analysis:
            top_performer = max(
                competitor_analysis,
                key=lambda x: x.get("quality_score", 0),
            ).get("url")

        brief = ContentBrief(
            target_keyword=target_keyword,
            timestamp=datetime.now().isoformat(),
            search_volume=keyword_data["volume"],
            keyword_difficulty=keyword_data["difficulty"],
            search_intent=keyword_data["intent"],
            recommended_word_count=word_count["recommended"],
            word_count_range=word_count["range"],
            tone=tone,
            header_structure=headers,
            topics_to_cover=topics,
            total_topics=len(topics),
            questions_to_answer=questions,
            total_questions=len(questions),
            competitor_avg_word_count=word_count["competitor_avg"],
            competitor_urls=competitor_urls,
            top_performing_competitor=top_performer,
            title_suggestions=title_suggestions,
            meta_description_suggestion=meta_description,
        )

        self.logger.info(
            "content_brief_generation_complete",
            word_count=word_count["recommended"],
            topics=len(topics),
            questions=len(questions),
        )

        return brief

    async def _analyze_keyword(self, keyword: str) -> dict[str, Any]:
        """Analyze target keyword."""
        # Use keyword research agent
        research = await self.keyword_agent.research(
            seed_keyword=keyword,
            max_keywords=1,
            min_volume=0,
        )

        if research.keywords:
            kw = research.keywords[0]
            return {
                "volume": kw.volume,
                "difficulty": kw.difficulty,
                "intent": research.intents[0].intent if research.intents else "informational",
            }

        # Fallback if no data
        return {
            "volume": 0,
            "difficulty": 50.0,
            "intent": "informational",
        }

    async def _analyze_competitors(
        self,
        urls: list[str],
    ) -> list[dict[str, Any]]:
        """Analyze competitor content."""
        analyses = []

        for url in urls[:5]:  # Limit to 5 competitors
            try:
                result = await self.content_analyzer.analyze(
                    target_url=url,
                    competitor_urls=[],  # No comparison needed
                )

                analyses.append({
                    "url": url,
                    "word_count": result.target_analysis.word_count,
                    "quality_score": result.target_analysis.quality_score,
                    "headers": result.target_analysis.headers,
                })
            except Exception as e:
                self.logger.warning(
                    "competitor_analysis_failed",
                    url=url,
                    error=str(e),
                )

        return analyses

    def _calculate_word_count(
        self,
        competitor_analysis: list[dict[str, Any]],
        target: int | None,
    ) -> dict[str, Any]:
        """Calculate recommended word count."""
        if target:
            return {
                "recommended": target,
                "range": (int(target * 0.9), int(target * 1.1)),
                "competitor_avg": 0,
            }

        if not competitor_analysis:
            return {
                "recommended": 1500,
                "range": (1200, 1800),
                "competitor_avg": 0,
            }

        # Calculate from competitors
        word_counts = [c["word_count"] for c in competitor_analysis]
        avg = sum(word_counts) / len(word_counts)

        # Aim for 10-20% more than average
        recommended = int(avg * 1.15)

        return {
            "recommended": recommended,
            "range": (int(recommended * 0.9), int(recommended * 1.1)),
            "competitor_avg": int(avg),
        }

    def _generate_header_structure(
        self,
        keyword: str,
        competitor_analysis: list[dict[str, Any]],
    ) -> list[HeaderStructure]:
        """Generate recommended header structure."""
        headers = [
            HeaderStructure(
                level=1,
                text=f"{keyword.title()}: Complete Guide",
                keywords=[keyword],
            ),
        ]

        # Common H2 sections
        common_h2 = [
            f"What is {keyword}?",
            f"Benefits of {keyword}",
            f"How to {keyword}",
            f"{keyword} Best Practices",
            "Conclusion",
        ]

        for h2_text in common_h2:
            headers.append(
                HeaderStructure(
                    level=2,
                    text=h2_text,
                    keywords=[keyword],
                )
            )

        return headers

    def _identify_topics(
        self,
        competitor_analysis: list[dict[str, Any]],
    ) -> list[TopicCoverage]:
        """Identify topics to cover based on competitor analysis."""
        # Placeholder: In real implementation, would extract topics from competitor content
        topics = [
            TopicCoverage(
                topic="Introduction and overview",
                priority="high",
                reason="Essential foundation for readers",
                competitor_coverage=len(competitor_analysis),
            ),
            TopicCoverage(
                topic="Key benefits and advantages",
                priority="high",
                reason="Addresses user intent",
                competitor_coverage=len(competitor_analysis),
            ),
            TopicCoverage(
                topic="Step-by-step implementation",
                priority="medium",
                reason="Practical value for readers",
                competitor_coverage=max(1, len(competitor_analysis) - 1),
            ),
        ]

        return topics

    def _generate_questions(
        self,
        keyword: str,
        intent: str,
    ) -> list[QuestionToAnswer]:
        """Generate questions content should answer."""
        questions = []

        # Intent-based questions
        if intent == "informational":
            questions.extend([
                QuestionToAnswer(
                    question=f"What is {keyword}?",
                    priority="high",
                    source="user intent",
                ),
                QuestionToAnswer(
                    question=f"How does {keyword} work?",
                    priority="high",
                    source="user intent",
                ),
                QuestionToAnswer(
                    question=f"Why is {keyword} important?",
                    priority="medium",
                    source="user intent",
                ),
            ])
        elif intent == "commercial":
            questions.extend([
                QuestionToAnswer(
                    question=f"What are the best {keyword} options?",
                    priority="high",
                    source="user intent",
                ),
                QuestionToAnswer(
                    question=f"How to choose {keyword}?",
                    priority="high",
                    source="user intent",
                ),
                QuestionToAnswer(
                    question=f"What are the pros and cons of {keyword}?",
                    priority="medium",
                    source="user intent",
                ),
            ])

        return questions

    def _generate_title_suggestions(self, keyword: str) -> list[str]:
        """Generate title suggestions."""
        return [
            f"{keyword.title()}: Complete Guide for 2026",
            f"Everything You Need to Know About {keyword.title()}",
            f"{keyword.title()}: Benefits, Tips, and Best Practices",
        ]

    def _generate_meta_description(
        self,
        keyword: str,
        intent: str,
    ) -> str:
        """Generate meta description."""
        if intent == "informational":
            return f"Learn everything about {keyword}. Complete guide with tips, best practices, and expert insights."
        elif intent == "commercial":
            return f"Compare the best {keyword} options. Expert reviews, pros and cons, and buying guide."
        else:
            return f"Discover {keyword}. Comprehensive guide with actionable insights and recommendations."

    def _determine_tone(self, intent: str) -> str:
        """Determine content tone based on intent."""
        if intent == "informational":
            return "educational"
        elif intent == "commercial":
            return "professional"
        else:
            return "conversational"


async def main():
    """Example usage."""
    import os

    semrush_key = os.getenv("SEMRUSH_API_KEY")
    ahrefs_key = os.getenv("AHREFS_API_KEY")

    generator = ContentBriefGenerator(
        semrush_api_key=semrush_key,
        ahrefs_api_key=ahrefs_key,
    )

    brief = await generator.generate(
        target_keyword="dental implants",
        competitor_urls=[
            "https://example.com/dental-implants-guide",
            "https://example.com/implants-cost",
            "https://example.com/best-implants",
        ],
    )

    print(f"Target Keyword: {brief.target_keyword}")
    print(f"Search Volume: {brief.search_volume:,}")
    print(f"Recommended Word Count: {brief.recommended_word_count}")
    print(f"Tone: {brief.tone}")
    print()

    print("Header Structure:")
    for header in brief.header_structure[:5]:
        indent = "  " * (header.level - 1)
        print(f"{indent}H{header.level}: {header.text}")

    print(f"\nTopics to Cover: {brief.total_topics}")
    print(f"Questions to Answer: {brief.total_questions}")


if __name__ == "__main__":
    asyncio.run(main())
