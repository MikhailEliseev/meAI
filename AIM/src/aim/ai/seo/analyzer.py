"""
AI SEO Analyzer

Main orchestrator for comprehensive SEO analysis.
Combines content quality, entity optimization, SERP analysis, and conversational optimization.
"""

from typing import Optional, Dict, Any
import asyncio

from ..llm.client import LLMClient
from .content_quality import ContentQualityAnalyzer
from .entity_optimizer import EntityOptimizer
from .serp_analyzer import SERPAnalyzer
from .conversational_optimizer import ConversationalOptimizer
from .schemas import SEOAnalysisResult


class SEOAnalyzer:
    """
    Comprehensive AI-powered SEO analyzer.

    Combines:
    - Content quality (N-E-E-A-T-T)
    - Entity optimization (Knowledge Graph)
    - SERP analysis (features, gaps)
    - Conversational optimization (AI Overviews, ChatGPT, Perplexity)

    Returns unified SEOAnalysisResult with overall score and priority actions.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        serp_api_key: str,
        spacy_model: str = "ru_core_news_lg",
        serp_engine: str = "google",
    ):
        """
        Initialize SEO analyzer.

        Args:
            llm_client: LLM client for content analysis
            serp_api_key: SerpAPI key for SERP analysis
            spacy_model: spaCy model for entity extraction
            serp_engine: Search engine (google, yandex)
        """
        self.content_analyzer = ContentQualityAnalyzer(llm_client)
        self.entity_optimizer = EntityOptimizer(spacy_model)
        self.serp_analyzer = SERPAnalyzer(serp_api_key, serp_engine)
        self.conversational_optimizer = ConversationalOptimizer(llm_client)

    async def close(self) -> None:
        """Close all clients."""
        await self.serp_analyzer.close()

    async def analyze(
        self,
        url: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        target_query: Optional[str] = None,
        include_serp: bool = True,
    ) -> SEOAnalysisResult:
        """
        Perform comprehensive SEO analysis.

        Args:
            url: Page URL
            content: HTML content
            metadata: Optional metadata (title, description, published_date, etc.)
            target_query: Optional target query for SERP analysis
            include_serp: Whether to include SERP analysis (default: True)

        Returns:
            SEOAnalysisResult with all analysis components
        """
        # Run analyses in parallel
        tasks = [
            self.content_analyzer.analyze(content, url, metadata),
            self.entity_optimizer.analyze(content, url, metadata),
            self.conversational_optimizer.analyze(content, url, metadata),
        ]

        # Add SERP analysis if target query provided
        if include_serp and target_query:
            tasks.append(
                self.serp_analyzer.analyze(
                    query=target_query,
                    location="Russia",
                    language="ru",
                )
            )

        # Execute all analyses
        results = await asyncio.gather(*tasks)

        # Unpack results
        content_quality = results[0]
        entity_analysis = results[1]
        conversational = results[2]
        serp_analysis = results[3] if include_serp and target_query else None

        # Calculate overall score
        overall_score = self._calculate_overall_score(
            content_quality=content_quality,
            entity_analysis=entity_analysis,
            conversational=conversational,
            serp_analysis=serp_analysis,
        )

        # Generate priority actions
        priority_actions = self._generate_priority_actions(
            content_quality=content_quality,
            entity_analysis=entity_analysis,
            conversational=conversational,
            serp_analysis=serp_analysis,
        )

        # Estimate impact
        estimated_impact = self._estimate_impact(overall_score, priority_actions)

        return SEOAnalysisResult(
            url=url,
            content_quality=content_quality,
            entity_analysis=entity_analysis,
            serp_analysis=serp_analysis,
            conversational=conversational,
            overall_score=overall_score,
            priority_actions=priority_actions,
            estimated_impact=estimated_impact,
        )

    def _calculate_overall_score(
        self,
        content_quality,
        entity_analysis,
        conversational,
        serp_analysis,
    ) -> float:
        """
        Calculate overall SEO score (0-100).

        Weighted average:
        - Content quality: 35%
        - Entity optimization: 20%
        - Conversational: 25%
        - SERP features: 20%

        Args:
            content_quality: ContentQualityScore
            entity_analysis: EntityAnalysis
            conversational: ConversationalOptimization
            serp_analysis: Optional SERPAnalysis

        Returns:
            Overall score 0-100
        """
        # Content quality score (35%)
        content_score = content_quality.overall * 0.35

        # Entity optimization score (20%)
        entity_score = 0.0
        if entity_analysis.knowledge_graph_ready:
            entity_score += 10.0
        if entity_analysis.density >= 2.0 and entity_analysis.density <= 5.0:
            entity_score += 5.0
        if len(entity_analysis.schema_suggestions) >= 3:
            entity_score += 5.0
        entity_score = entity_score * 0.20 / 0.20  # Normalize to 20%

        # Conversational score (25%)
        conv_avg = (
            conversational.ai_overviews_score +
            conversational.chatgpt_score +
            conversational.perplexity_score
        ) / 3
        conv_score = conv_avg * 0.25

        # SERP features score (20%)
        serp_score = 0.0
        if serp_analysis:
            # Score based on owned features
            owned_features = sum(1 for f in serp_analysis.serp_features if f.owned)
            total_features = len(serp_analysis.serp_features)
            if total_features > 0:
                serp_score = (owned_features / total_features) * 100 * 0.20

        # Total score
        overall = content_score + entity_score + conv_score + serp_score

        return round(overall, 1)

    def _generate_priority_actions(
        self,
        content_quality,
        entity_analysis,
        conversational,
        serp_analysis,
    ) -> list[str]:
        """
        Generate priority actions based on analysis.

        Returns top 5-7 actions sorted by impact.

        Args:
            content_quality: ContentQualityScore
            entity_analysis: EntityAnalysis
            conversational: ConversationalOptimization
            serp_analysis: Optional SERPAnalysis

        Returns:
            List of priority actions
        """
        actions = []

        # Content quality actions
        if content_quality.overall < 70:
            if content_quality.expertise < 70:
                actions.append(
                    ("🎓 Expertise: Добавить экспертные сигналы (автор, квалификация, цитаты)", 90)
                )
            if content_quality.trustworthiness < 70:
                actions.append(
                    ("🔒 Trust: Усилить сигналы доверия (HTTPS, контакты, отзывы)", 85)
                )
            if content_quality.readability < 70:
                actions.append(
                    ("📖 Readability: Улучшить читаемость (короче предложения, структура)", 75)
                )

        # Entity optimization actions
        if not entity_analysis.knowledge_graph_ready:
            if entity_analysis.density < 2.0:
                actions.append(
                    ("🏷️ Entities: Увеличить плотность сущностей (добавить имена, места, организации)", 80)
                )
            if len(entity_analysis.schema_suggestions) < 3:
                actions.append(
                    ("📋 Schema: Добавить schema.org разметку (минимум 3 типа)", 85)
                )

        # Conversational optimization actions
        if conversational.ai_overviews_score < 70:
            actions.append(
                ("🤖 AI Overviews: Оптимизировать для Google AI (структура, прямые ответы)", 90)
            )
        if conversational.chatgpt_score < 70:
            actions.append(
                ("💬 ChatGPT: Улучшить цитируемость (факты, источники, цитаты)", 85)
            )
        if not conversational.answer_box_ready:
            actions.append(
                ("❓ Answer Box: Добавить FAQ-секцию с вопросами-ответами", 80)
            )

        # SERP actions
        if serp_analysis:
            # Add top 3 competitor gaps
            for gap in serp_analysis.competitor_gaps[:3]:
                actions.append((f"🎯 SERP: {gap}", 85))

        # Sort by priority (second element of tuple)
        actions.sort(key=lambda x: x[1], reverse=True)

        # Return top 7 actions (text only, without priority score)
        return [action[0] for action in actions[:7]]

    def _estimate_impact(self, overall_score: float, priority_actions: list[str]) -> str:
        """
        Estimate impact of implementing priority actions.

        Args:
            overall_score: Current overall score
            priority_actions: List of priority actions

        Returns:
            Impact estimate (LOW, MEDIUM, HIGH, CRITICAL)
        """
        # Calculate potential improvement
        action_count = len(priority_actions)
        potential_improvement = action_count * 5  # ~5 points per action

        # Current score + potential improvement
        potential_score = overall_score + potential_improvement

        # Estimate impact based on current score and potential
        if overall_score < 50:
            return "CRITICAL - Требуется полная переработка контента"
        elif overall_score < 70:
            if potential_score >= 80:
                return "HIGH - Значительное улучшение возможно (до +15-20 позиций)"
            else:
                return "MEDIUM - Умеренное улучшение (до +10 позиций)"
        elif overall_score < 85:
            return "MEDIUM - Точечные улучшения (до +5 позиций)"
        else:
            return "LOW - Контент уже оптимизирован, фокус на поддержку"


async def analyze_url(
    url: str,
    content: str,
    llm_client: LLMClient,
    serp_api_key: str,
    target_query: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> SEOAnalysisResult:
    """
    Convenience function for single URL analysis.

    Args:
        url: Page URL
        content: HTML content
        llm_client: LLM client
        serp_api_key: SerpAPI key
        target_query: Optional target query
        metadata: Optional metadata

    Returns:
        SEOAnalysisResult
    """
    analyzer = SEOAnalyzer(
        llm_client=llm_client,
        serp_api_key=serp_api_key,
    )

    try:
        result = await analyzer.analyze(
            url=url,
            content=content,
            metadata=metadata,
            target_query=target_query,
        )
        return result
    finally:
        await analyzer.close()
