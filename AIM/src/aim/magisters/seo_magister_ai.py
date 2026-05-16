"""SEO Magister with AI Enhancement - Coordinates SEO Analysis with AI

Extends base SEO Magister with AI-powered analysis:
- Content quality scoring (N-E-E-A-T-T framework)
- Entity optimization (Knowledge Graph)
- SERP analysis (features, gaps)
- Conversational optimization (AI Overviews, ChatGPT, Perplexity)

Part of: Phase 10 - AI Enhancement (Task 1.3)
"""

import asyncio
from datetime import datetime, timezone
from typing import Any

from AIM.src.aim.magisters.seo_magister import SEOMagister
from AIM.src.aim.ai.seo.analyzer import SEOAnalyzer
from AIM.src.aim.ai.seo.schemas import SEOAnalysisResult


class SEOMagisterAI(SEOMagister):
    """SEO Magister with AI Enhancement

    Extends base SEO Magister with AI-powered analysis components:
    - Traditional SEO analysis (technical, content, links)
    - AI content quality scoring (N-E-E-A-T-T)
    - Entity optimization for Knowledge Graph
    - SERP feature analysis
    - Conversational search optimization

    Combines traditional SEO metrics with AI insights for comprehensive analysis.
    """

    def __init__(
        self,
        llm_client: Any,
        serp_api_key: str,
        timeout: int = 600,
        spacy_model: str = "ru_core_news_lg",
        serp_engine: str = "google",
        **kwargs
    ):
        """Initialize SEO Magister with AI

        Args:
            llm_client: LLM client for AI analysis
            serp_api_key: SerpAPI key for SERP analysis
            timeout: Maximum time for analysis in seconds
            spacy_model: spaCy model for entity extraction
            serp_engine: SERP engine (google or yandex)
            **kwargs: Additional arguments for base SEOMagister
        """
        super().__init__(timeout=timeout, **kwargs)

        # AI SEO Analyzer
        self.ai_analyzer = SEOAnalyzer(
            llm_client=llm_client,
            serp_api_key=serp_api_key,
            spacy_model=spacy_model,
            serp_engine=serp_engine,
        )

    async def coordinate_analysis(
        self,
        url: str,
        correlation_id: str | None = None,
        target_query: str | None = None,
        include_serp: bool = True,
        include_ai: bool = True,
    ) -> dict[str, Any]:
        """Coordinate comprehensive SEO analysis with AI

        Runs traditional SEO analysis and AI analysis in parallel,
        then combines results into unified report.

        Args:
            url: Website URL to analyze
            correlation_id: Optional correlation ID for tracking
            target_query: Target search query for SERP analysis
            include_serp: Include SERP analysis (requires target_query)
            include_ai: Include AI analysis

        Returns:
            Comprehensive SEO analysis report with traditional + AI insights
        """
        if correlation_id is None:
            correlation_id = f"seo-ai-analysis-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

        start_time = datetime.now(timezone.utc)

        try:
            # Run traditional and AI analysis in parallel with timeout
            if include_ai:
                traditional_result, ai_result = await asyncio.wait_for(
                    asyncio.gather(
                        super().coordinate_analysis(url, correlation_id),
                        self._run_ai_analysis(url, target_query, include_serp),
                        return_exceptions=True,
                    ),
                    timeout=self.timeout,
                )
            else:
                traditional_result = await asyncio.wait_for(
                    super().coordinate_analysis(url, correlation_id),
                    timeout=self.timeout,
                )
                ai_result = None

            # Handle exceptions
            if isinstance(traditional_result, Exception):
                traditional_result = {
                    "status": "error",
                    "error": str(traditional_result),
                }

            if isinstance(ai_result, Exception):
                ai_result = {
                    "status": "error",
                    "error": str(ai_result),
                }

            # Combine results
            report = await self._combine_results(
                url=url,
                correlation_id=correlation_id,
                traditional_result=traditional_result,
                ai_result=ai_result,
                start_time=start_time,
            )

            return report

        except asyncio.TimeoutError:
            return {
                "url": url,
                "correlation_id": correlation_id,
                "status": "error",
                "error": f"Analysis timeout after {self.timeout} seconds",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                "url": url,
                "correlation_id": correlation_id,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    async def _run_ai_analysis(
        self,
        url: str,
        target_query: str | None,
        include_serp: bool,
    ) -> SEOAnalysisResult | dict[str, Any]:
        """Run AI SEO analysis

        Args:
            url: Website URL
            target_query: Target search query
            include_serp: Include SERP analysis

        Returns:
            AI analysis result or error dict
        """
        try:
            # Fetch page content (simplified - in production use proper scraper)
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                content = response.text

            # Run AI analysis
            result = await self.ai_analyzer.analyze(
                url=url,
                content=content,
                target_query=target_query,
                include_serp=include_serp and target_query is not None,
            )

            return result

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }

    async def _combine_results(
        self,
        url: str,
        correlation_id: str,
        traditional_result: dict[str, Any],
        ai_result: SEOAnalysisResult | dict[str, Any] | None,
        start_time: datetime,
    ) -> dict[str, Any]:
        """Combine traditional and AI analysis results

        Args:
            url: Website URL
            correlation_id: Correlation ID
            traditional_result: Traditional SEO analysis
            ai_result: AI SEO analysis
            start_time: Analysis start time

        Returns:
            Combined analysis report
        """
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        # Base report from traditional analysis
        report = {
            "url": url,
            "correlation_id": correlation_id,
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(duration, 2),
            "traditional_seo": traditional_result,
        }

        # Add AI analysis if available
        if ai_result and not isinstance(ai_result, dict):
            # SEOAnalysisResult object
            report["ai_seo"] = {
                "status": "success",
                "overall_score": ai_result.overall_score,
                "content_quality": {
                    "overall": ai_result.content_quality.overall,
                    "newsworthiness": ai_result.content_quality.newsworthiness,
                    "expertise": ai_result.content_quality.expertise,
                    "experience": ai_result.content_quality.experience,
                    "authoritativeness": ai_result.content_quality.authoritativeness,
                    "trustworthiness": ai_result.content_quality.trustworthiness,
                    "transparency": ai_result.content_quality.transparency,
                    "readability": ai_result.content_quality.readability,
                    "recommendations": ai_result.content_quality.recommendations,
                },
                "entity_analysis": {
                    "entity_count": len(ai_result.entity_analysis.entities),
                    "density": ai_result.entity_analysis.density,
                    "schema_suggestions": ai_result.entity_analysis.schema_suggestions,
                    "knowledge_graph_ready": ai_result.entity_analysis.knowledge_graph_ready,
                },
                "conversational": {
                    "ai_overviews_score": ai_result.conversational.ai_overviews_score,
                    "chatgpt_score": ai_result.conversational.chatgpt_score,
                    "perplexity_score": ai_result.conversational.perplexity_score,
                    "answer_box_ready": ai_result.conversational.answer_box_ready,
                    "citation_score": ai_result.conversational.citation_score,
                },
                "priority_actions": ai_result.priority_actions,
                "estimated_impact": ai_result.estimated_impact,
            }

            # Add SERP analysis if available
            if ai_result.serp_analysis:
                report["ai_seo"]["serp_analysis"] = {
                    "query": ai_result.serp_analysis.query,
                    "featured_snippet": ai_result.serp_analysis.featured_snippet,
                    "paa_questions": ai_result.serp_analysis.paa_questions,
                    "competitor_gaps": ai_result.serp_analysis.competitor_gaps,
                    "serp_features": [
                        {
                            "type": f.type,
                            "present": f.present,
                            "owned": f.owned,
                            "opportunity_score": f.opportunity_score,
                        }
                        for f in ai_result.serp_analysis.serp_features
                    ],
                }

            # Calculate combined score (50% traditional, 50% AI)
            traditional_score = traditional_result.get("scores", {}).get("overall", 0)
            ai_score = ai_result.overall_score
            combined_score = (traditional_score * 0.5) + (ai_score * 0.5)

            report["combined_score"] = round(combined_score, 1)
            report["score_breakdown"] = {
                "traditional": round(traditional_score, 1),
                "ai": round(ai_score, 1),
            }

            # Generate combined recommendations
            report["combined_recommendations"] = self._generate_combined_recommendations(
                traditional_result,
                ai_result,
            )

        elif ai_result and isinstance(ai_result, dict):
            # Error dict
            report["ai_seo"] = ai_result
            report["combined_score"] = traditional_result.get("scores", {}).get("overall", 0)

        else:
            # AI analysis not included
            report["ai_seo"] = {"status": "not_included"}
            report["combined_score"] = traditional_result.get("scores", {}).get("overall", 0)

        return report

    def _generate_combined_recommendations(
        self,
        traditional_result: dict[str, Any],
        ai_result: SEOAnalysisResult,
    ) -> list[dict[str, str]]:
        """Generate combined recommendations from traditional and AI analysis

        Args:
            traditional_result: Traditional SEO analysis
            ai_result: AI SEO analysis

        Returns:
            List of combined recommendations with priority
        """
        recommendations = []

        # Add traditional recommendations
        traditional_recs = traditional_result.get("recommendations", [])
        for rec in traditional_recs[:5]:  # Top 5 traditional
            recommendations.append({
                "source": "traditional",
                "priority": rec.get("priority", "medium"),
                "category": rec.get("category", "general"),
                "issue": rec.get("issue", ""),
                "action": rec.get("action", ""),
            })

        # Add AI priority actions
        for action in ai_result.priority_actions[:5]:  # Top 5 AI
            # Parse emoji and text
            parts = action.split(":", 1)
            if len(parts) == 2:
                category = parts[0].strip()
                action_text = parts[1].strip()
            else:
                category = "AI"
                action_text = action

            recommendations.append({
                "source": "ai",
                "priority": "high",
                "category": category,
                "issue": "AI-detected optimization opportunity",
                "action": action_text,
            })

        # Sort by priority (high > medium > low)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))

        return recommendations[:10]  # Top 10 combined

    async def close(self):
        """Close AI analyzer resources"""
        await self.ai_analyzer.close()
