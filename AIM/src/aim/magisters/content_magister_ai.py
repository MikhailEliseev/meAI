"""Content Magister AI Integration

Integrates AI components with Content Magister:
- Content Generator (AI-powered content creation)
- Content Optimizer (AI-powered optimization)
- Readability Analyzer (AI-powered readability analysis)
- SEO Content Analyzer (AI-powered SEO analysis)

Part of: Phase 10 - AI Enhancement (Task 2.3)
"""

from typing import Any, Dict, List
from datetime import datetime, timezone
import structlog

from src.aim.magisters.content_magister import ContentMagister
from src.aim.ai.llm.client import LLMClient

logger = structlog.get_logger(__name__)


class ContentMagisterAI(ContentMagister):
    """Content Magister with AI Enhancement

    Extends base Content Magister with AI capabilities:
    - AI-powered content generation
    - AI-powered content optimization
    - AI-powered readability analysis
    - AI-powered SEO content analysis

    Target Improvements:
    - Content creation time: -70%
    - Content quality score: >85/100
    - Readability score: >80/100
    - SEO optimization: >90/100
    """

    def __init__(
        self,
        magister_id: str = "content-magister-ai",
        database_url: str = "sqlite+aiosqlite:///./AIM/data/aim.db",
        vault_path: str = "./AIM/obsidian/content-magister",
        event_bus: Any | None = None,
        vault: Any | None = None,
        llm_client: LLMClient | None = None,
    ):
        """Initialize AI-enhanced Content Magister

        Args:
            magister_id: Unique Magister ID
            database_url: Database connection URL
            vault_path: Path to Content Magister's Obsidian vault
            event_bus: Optional EventBus instance (for testing)
            vault: Optional ObsidianVault instance (for testing)
            llm_client: Optional LLM client (for testing)
        """
        super().__init__(
            magister_id=magister_id,
            database_url=database_url,
            vault_path=vault_path,
            event_bus=event_bus,
            vault=vault,
        )

        # Initialize AI components
        self.llm_client = llm_client or LLMClient()

        logger.info(
            "content_magister_ai_initialized",
            magister_id=magister_id,
            ai_components=["llm_client"],
        )

    async def generate_content(
        self,
        topic: str,
        content_type: str,
        target_audience: str | None = None,
        tone: str | None = None,
        word_count: int = 1000,
    ) -> Dict[str, Any]:
        """Generate AI-powered content

        Args:
            topic: Content topic
            content_type: Type of content (article, blog_post, landing_page, etc.)
            target_audience: Target audience description
            tone: Content tone (professional, friendly, authoritative, etc.)
            word_count: Target word count

        Returns:
            Generated content with metadata
        """
        logger.info(
            "generating_content",
            topic=topic,
            content_type=content_type,
            word_count=word_count,
        )

        # Build prompt
        prompt = f"""Generate {content_type} content about: {topic}

Target word count: {word_count}
"""
        if target_audience:
            prompt += f"Target audience: {target_audience}\n"
        if tone:
            prompt += f"Tone: {tone}\n"

        prompt += """
Requirements:
- High-quality, engaging content
- SEO-optimized with natural keyword usage
- Clear structure with headings
- Actionable insights
- Medical accuracy (if applicable)

Return the content in markdown format.
"""

        # Generate content
        from src.aim.ai.llm.schemas import LLMRequest

        request = LLMRequest(
            prompt=prompt,
            temperature=0.7,
            max_tokens=word_count * 2,
        )

        response = await self.llm_client.generate(request)

        # Calculate metrics
        content_text = response.content
        actual_word_count = len(content_text.split())
        generation_cost = response.cost_usd

        # Log to Obsidian
        await self._log_operation(
            "generate_content",
            f"Generated {content_type} about '{topic}'. "
            f"Words: {actual_word_count}, Cost: ${generation_cost:.4f}"
        )

        logger.info(
            "content_generated",
            topic=topic,
            content_type=content_type,
            word_count=actual_word_count,
            generation_cost=generation_cost,
        )

        return {
            "topic": topic,
            "content_type": content_type,
            "content": content_text,
            "word_count": actual_word_count,
            "generation_cost": generation_cost,
            "metadata": {
                "target_audience": target_audience,
                "tone": tone,
                "target_word_count": word_count,
            },
        }

    async def optimize_content(
        self,
        content: str,
        optimization_goals: List[str],
    ) -> Dict[str, Any]:
        """Optimize content with AI

        Args:
            content: Original content to optimize
            optimization_goals: List of optimization goals
                (readability, seo, engagement, clarity, etc.)

        Returns:
            Optimized content with improvements
        """
        logger.info(
            "optimizing_content",
            content_length=len(content),
            goals=optimization_goals,
        )

        # Build prompt
        goals_text = ", ".join(optimization_goals)
        prompt = f"""Optimize the following content for: {goals_text}

Original content:
{content}

Requirements:
- Maintain the core message and facts
- Improve based on specified goals
- Provide specific improvements made
- Return optimized content in markdown format

Return format:
## Optimized Content
[optimized content here]

## Improvements Made
- [list of specific improvements]
"""

        # Optimize content
        from src.aim.ai.llm.schemas import LLMRequest

        request = LLMRequest(
            prompt=prompt,
            temperature=0.5,
            max_tokens=len(content.split()) * 3,
        )

        response = await self.llm_client.generate(request)

        # Parse response
        response_text = response.content
        parts = response_text.split("## Improvements Made")

        optimized_content = parts[0].replace("## Optimized Content", "").strip()
        improvements = []
        if len(parts) > 1:
            improvements_text = parts[1].strip()
            improvements = [
                line.strip("- ").strip()
                for line in improvements_text.split("\n")
                if line.strip().startswith("-")
            ]

        optimization_cost = response.cost_usd

        # Log to Obsidian
        await self._log_operation(
            "optimize_content",
            f"Optimized content for {goals_text}. "
            f"Improvements: {len(improvements)}, Cost: ${optimization_cost:.4f}"
        )

        logger.info(
            "content_optimized",
            improvements_count=len(improvements),
            optimization_cost=optimization_cost,
        )

        return {
            "original_content": content,
            "optimized_content": optimized_content,
            "improvements": improvements,
            "optimization_goals": optimization_goals,
            "optimization_cost": optimization_cost,
        }

    async def analyze_readability(
        self,
        content: str,
    ) -> Dict[str, Any]:
        """Analyze content readability with AI

        Args:
            content: Content to analyze

        Returns:
            Readability analysis with score and recommendations
        """
        logger.info(
            "analyzing_readability",
            content_length=len(content),
        )

        # Build prompt
        prompt = f"""Analyze the readability of the following content:

{content}

Provide:
1. Readability score (0-100, where 100 is most readable)
2. Reading level (e.g., "8th grade", "college", "professional")
3. Specific readability issues
4. Recommendations for improvement

Return in this format:
Score: [0-100]
Reading Level: [level]
Issues:
- [issue 1]
- [issue 2]
Recommendations:
- [recommendation 1]
- [recommendation 2]
"""

        # Analyze readability
        from src.aim.ai.llm.schemas import LLMRequest

        request = LLMRequest(
            prompt=prompt,
            temperature=0.3,
            max_tokens=1000,
        )

        response = await self.llm_client.generate(request)

        # Parse response
        response_text = response.content

        # Extract score
        score = 0.0
        if "Score:" in response_text:
            score_line = [line for line in response_text.split("\n") if "Score:" in line][0]
            score = float(score_line.split(":")[1].strip())

        # Extract reading level
        reading_level = "Unknown"
        if "Reading Level:" in response_text:
            level_line = [line for line in response_text.split("\n") if "Reading Level:" in line][0]
            reading_level = level_line.split(":")[1].strip()

        # Extract issues
        issues = []
        if "Issues:" in response_text:
            issues_section = response_text.split("Issues:")[1].split("Recommendations:")[0]
            issues = [
                line.strip("- ").strip()
                for line in issues_section.split("\n")
                if line.strip().startswith("-")
            ]

        # Extract recommendations
        recommendations = []
        if "Recommendations:" in response_text:
            rec_section = response_text.split("Recommendations:")[1]
            recommendations = [
                line.strip("- ").strip()
                for line in rec_section.split("\n")
                if line.strip().startswith("-")
            ]

        analysis_cost = response.cost_usd

        # Log to Obsidian
        await self._log_operation(
            "analyze_readability",
            f"Readability score: {score:.1f}/100, Level: {reading_level}, "
            f"Issues: {len(issues)}, Cost: ${analysis_cost:.4f}"
        )

        logger.info(
            "readability_analyzed",
            score=score,
            reading_level=reading_level,
            issues_count=len(issues),
            analysis_cost=analysis_cost,
        )

        return {
            "score": score,
            "reading_level": reading_level,
            "issues": issues,
            "recommendations": recommendations,
            "analysis_cost": analysis_cost,
        }

    async def analyze_seo_content(
        self,
        content: str,
        target_keywords: List[str],
    ) -> Dict[str, Any]:
        """Analyze content for SEO with AI

        Args:
            content: Content to analyze
            target_keywords: Target keywords for SEO

        Returns:
            SEO analysis with score and recommendations
        """
        logger.info(
            "analyzing_seo_content",
            content_length=len(content),
            keywords_count=len(target_keywords),
        )

        # Build prompt
        keywords_text = ", ".join(target_keywords)
        prompt = f"""Analyze the SEO quality of the following content for keywords: {keywords_text}

Content:
{content}

Provide:
1. SEO score (0-100, where 100 is best optimized)
2. Keyword usage analysis (frequency, placement, naturalness)
3. SEO issues found
4. Recommendations for improvement

Return in this format:
Score: [0-100]
Keyword Usage:
- [keyword 1]: [analysis]
- [keyword 2]: [analysis]
Issues:
- [issue 1]
- [issue 2]
Recommendations:
- [recommendation 1]
- [recommendation 2]
"""

        # Analyze SEO
        from src.aim.ai.llm.schemas import LLMRequest

        request = LLMRequest(
            prompt=prompt,
            temperature=0.3,
            max_tokens=1500,
        )

        response = await self.llm_client.generate(request)

        # Parse response
        response_text = response.content

        # Extract score
        score = 0.0
        if "Score:" in response_text:
            score_line = [line for line in response_text.split("\n") if "Score:" in line][0]
            score = float(score_line.split(":")[1].strip())

        # Extract keyword usage
        keyword_usage = {}
        if "Keyword Usage:" in response_text:
            usage_section = response_text.split("Keyword Usage:")[1].split("Issues:")[0]
            for line in usage_section.split("\n"):
                if ":" in line and line.strip().startswith("-"):
                    parts = line.strip("- ").split(":", 1)
                    if len(parts) == 2:
                        keyword_usage[parts[0].strip()] = parts[1].strip()

        # Extract issues
        issues = []
        if "Issues:" in response_text:
            issues_section = response_text.split("Issues:")[1].split("Recommendations:")[0]
            issues = [
                line.strip("- ").strip()
                for line in issues_section.split("\n")
                if line.strip().startswith("-")
            ]

        # Extract recommendations
        recommendations = []
        if "Recommendations:" in response_text:
            rec_section = response_text.split("Recommendations:")[1]
            recommendations = [
                line.strip("- ").strip()
                for line in rec_section.split("\n")
                if line.strip().startswith("-")
            ]

        analysis_cost = response.cost_usd

        # Log to Obsidian
        await self._log_operation(
            "analyze_seo_content",
            f"SEO score: {score:.1f}/100, Keywords: {len(target_keywords)}, "
            f"Issues: {len(issues)}, Cost: ${analysis_cost:.4f}"
        )

        logger.info(
            "seo_content_analyzed",
            score=score,
            keywords_count=len(target_keywords),
            issues_count=len(issues),
            analysis_cost=analysis_cost,
        )

        return {
            "score": score,
            "target_keywords": target_keywords,
            "keyword_usage": keyword_usage,
            "issues": issues,
            "recommendations": recommendations,
            "analysis_cost": analysis_cost,
        }

    async def close(self):
        """Close AI components and base magister"""
        # Close AI components
        await self.llm_client.close()
