"""
SkillComparator - Compare and rank skills from multiple sources.

Compares skills across multiple dimensions:
- Quality: Code quality, error handling, type hints
- Completeness: Feature coverage, edge cases
- Maintainability: Documentation, structure, readability
- Performance: Efficiency, optimization, scalability

Ranks skills by total score and identifies best implementation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from aim.teacher.skills.skill_selector import Skill

if TYPE_CHECKING:
    from aim.teacher.skills.skill_applier import TargetContext

logger = structlog.get_logger()


@dataclass
class ComparisonResult:
    """Result of skill comparison."""

    ranked_skills: list[Skill] = field(default_factory=list)  # Sorted by total score
    best_skill: Skill | None = None  # Highest scoring skill
    dimension_scores: dict[str, dict[str, float]] = field(
        default_factory=dict
    )  # {source_repo: {dimension: score}}


class SkillComparator:
    """
    Compare and rank skills from multiple sources.

    Responsibilities:
    - Score skills across 4 dimensions (quality, completeness, maintainability, performance)
    - Rank skills by total score
    - Identify best implementation
    - Handle edge cases (single skill, empty list, identical scores)
    """

    def __init__(self):
        self.logger = logger.bind(component="skill_comparator")

        # Domain keywords for each subagent type
        self.domain_keywords = {
            "ci-content": [
                "content", "extraction", "scraping", "parsing",
                "seo", "meta", "heading", "keyword", "density",
                "competitor", "comparison", "gap", "analysis",
                "trafilatura", "beautifulsoup", "html", "text",
                "article", "blog", "readability", "quality"
            ],
            "ci-tech": [
                "lighthouse", "performance", "vitals", "speed",
                "technical", "crawl", "sitemap", "robots",
                "schema", "structured", "data", "audit",
                "core web vitals", "lcp", "fid", "cls"
            ],
            "keyword-research": [
                "keyword", "search", "volume", "difficulty",
                "serp", "ranking", "competition", "cpc",
                "semrush", "ahrefs", "api", "research"
            ],
            "seo": [
                "seo", "optimization", "ranking", "serp",
                "backlink", "authority", "indexing", "crawl"
            ],
            "content": [
                "content", "generation", "writing", "blog",
                "article", "copywriting", "tone", "style"
            ],
            "ads": [
                "ads", "advertising", "campaign", "bidding",
                "yandex", "direct", "conversion", "roi"
            ],
        }

    def _score_domain_relevance(self, skill: Skill, subagent_name: str) -> float:
        """
        Score domain relevance for subagent.

        Args:
            skill: Skill to score
            subagent_name: Name of target subagent

        Returns:
            0-100 score (higher = more relevant to domain)
        """
        keywords = self.domain_keywords.get(subagent_name, [])

        if not keywords:
            # No domain keywords defined, return neutral score
            return 50.0

        # Combine skill text for matching
        text = f"{skill.name} {skill.description} {skill.code_example}".lower()

        # Count keyword matches
        matches = sum(1 for kw in keywords if kw in text)

        # Bonus for library usage (trafilatura.extract, BeautifulSoup, etc.)
        library_usage_bonus = 0.0
        has_trafilatura_extract = "trafilatura.extract" in text or "trafilatura.extract_metadata" in text
        has_beautifulsoup = "beautifulsoup" in text or "soup." in text
        has_lxml = "lxml" in text

        if has_trafilatura_extract:
            library_usage_bonus += 30.0
        if has_beautifulsoup:
            library_usage_bonus += 20.0
        if has_lxml:
            library_usage_bonus += 10.0

        # Score: 0-100 based on match percentage + library usage bonus
        max_matches = len(keywords)
        base_score = (matches / max_matches) * 100 if max_matches > 0 else 50.0
        final_score = min(base_score + library_usage_bonus, 100.0)

        # Log scoring details
        self.logger.info(
            "domain_relevance_scored",
            skill_name=skill.name,
            keyword_matches=matches,
            max_keywords=max_matches,
            base_score=round(base_score, 2),
            library_bonus=round(library_usage_bonus, 2),
            has_trafilatura=has_trafilatura_extract,
            has_beautifulsoup=has_beautifulsoup,
            has_lxml=has_lxml,
            final_score=round(final_score, 2),
        )

        return final_score

    async def compare(self, skills: list[Skill]) -> ComparisonResult:
        """
        Compare skills and rank by total score.

        Args:
            skills: List of skills to compare

        Returns:
            ComparisonResult with ranked skills and dimension scores
        """
        if not skills:
            self.logger.info("no_skills_to_compare")
            return ComparisonResult()

        if len(skills) == 1:
            self.logger.info("single_skill", skill=skills[0].name)
            dimension_scores = self._score_all_dimensions(skills[0])
            return ComparisonResult(
                ranked_skills=skills,
                best_skill=skills[0],
                dimension_scores={skills[0].source_repo: dimension_scores},
            )

        # Score all skills across all dimensions
        # Use source_repo as unique key (skills can have same name)
        all_dimension_scores = {}
        for skill in skills:
            dimension_scores = self._score_all_dimensions(skill)
            all_dimension_scores[skill.source_repo] = dimension_scores

        # Calculate total scores
        skill_totals = []
        for skill in skills:
            total = sum(all_dimension_scores[skill.source_repo].values())
            skill_totals.append((skill, total))

        # Sort by total score (descending)
        skill_totals.sort(key=lambda x: x[1], reverse=True)

        # Extract ranked skills
        ranked_skills = [skill for skill, _ in skill_totals]
        best_skill = ranked_skills[0]

        self.logger.info(
            "skills_compared",
            total_skills=len(skills),
            best_skill=best_skill.name,
            best_score=skill_totals[0][1],
        )

        return ComparisonResult(
            ranked_skills=ranked_skills,
            best_skill=best_skill,
            dimension_scores=all_dimension_scores,
        )

    def _check_compatibility(
        self,
        skill: Skill,
        target_context: "TargetContext"
    ) -> tuple[bool, str]:
        """Check if skill is compatible with target context."""

        if not skill.code_example:
            return True, "No code to check"

        code = skill.code_example

        # REMOVED: async/sync check - SkillApplier can convert sync to async
        # We accept both sync and async skills for async targets

        # Check library compatibility (soft check - SkillApplier can adapt)
        skill_libraries = set()
        if "httpx" in code:
            skill_libraries.add("httpx")
        if "aiohttp" in code:
            skill_libraries.add("aiohttp")
        if "requests" in code:
            skill_libraries.add("requests")
        if "urllib" in code:
            skill_libraries.add("urllib")

        # Soft library check - we prefer matching libraries but don't reject mismatches
        # SkillApplier can convert requests -> httpx, urllib -> httpx
        # Just log a warning if libraries don't match
        if skill_libraries and target_context.libraries:
            if not skill_libraries.intersection(target_context.libraries):
                self.logger.debug(
                    "library_mismatch_will_adapt",
                    skill=skill.name,
                    skill_libraries=list(skill_libraries),
                    target_libraries=list(target_context.libraries)
                )

        # Check error handling compatibility (soft check)
        if "sys.exit(" in code and target_context.error_style == "raise":
            self.logger.debug(
                "error_style_mismatch_will_adapt",
                skill=skill.name,
                skill_style="sys.exit",
                target_style="raise"
            )

        return True, "Compatible"

    async def compare_with_context(
        self,
        skills: list[Skill],
        target_context: "TargetContext"
    ) -> ComparisonResult:
        """
        Compare skills considering target context.

        Filters out incompatible skills before comparison.

        Args:
            skills: List of skills to compare
            target_context: Context of target file

        Returns:
            ComparisonResult with only compatible skills
        """
        if not skills:
            self.logger.info("no_skills_to_compare")
            return ComparisonResult()

        # Filter compatible skills
        compatible_skills = []
        for skill in skills:
            is_compatible, reason = self._check_compatibility(skill, target_context)
            if is_compatible:
                compatible_skills.append(skill)
            else:
                self.logger.info(
                    "skill_filtered_incompatible",
                    skill=skill.name,
                    source=skill.source_repo,
                    reason=reason
                )

        if not compatible_skills:
            self.logger.warning(
                "no_compatible_skills",
                total_skills=len(skills),
                target_async=target_context.is_async,
                target_libraries=list(target_context.libraries),
                target_error_style=target_context.error_style
            )
            return ComparisonResult()

        self.logger.info(
            "skills_filtered",
            total=len(skills),
            compatible=len(compatible_skills),
            filtered_out=len(skills) - len(compatible_skills)
        )

        # Score each compatible skill with domain-specific weighting
        for skill in compatible_skills:
            # Generic quality score (0-100)
            dimension_scores = self._score_all_dimensions(skill)
            quality_score = sum(dimension_scores.values()) / len(dimension_scores)

            # Domain relevance score (0-100)
            domain_score = self._score_domain_relevance(skill, target_context.subagent_name)

            # Combined score: 70% domain + 30% quality
            # Domain relevance is MORE important than code quality
            combined_score = (domain_score * 0.7) + (quality_score * 0.3)

            skill.quality_score = combined_score

            # Log detailed scoring breakdown
            self.logger.info(
                "skill_scored",
                skill_name=skill.name,
                source=skill.source_repo,
                domain_score=round(domain_score, 2),
                quality_score=round(quality_score, 2),
                combined_score=round(combined_score, 2),
                code_length=len(skill.code_example) if skill.code_example else 0,
            )

        # Sort by combined score
        ranked = sorted(compatible_skills, key=lambda s: s.quality_score, reverse=True)

        self.logger.info(
            "skills_compared",
            total_skills=len(ranked),
            best_skill=ranked[0].name if ranked else None,
            best_score=ranked[0].quality_score if ranked else None
        )

        return ComparisonResult(
            ranked_skills=ranked,
            best_skill=ranked[0] if ranked else None,
            dimension_scores={}
        )

    def _score_all_dimensions(self, skill: Skill) -> dict[str, float]:
        """
        Score skill across all dimensions.

        Args:
            skill: Skill to score

        Returns:
            Dict mapping dimension name to score (0-100)
        """
        return {
            "quality": self._score_quality(skill),
            "completeness": self._score_completeness(skill),
            "maintainability": self._score_maintainability(skill),
            "performance": self._score_performance(skill),
        }

    def _score_quality(self, skill: Skill) -> float:
        """
        Score code quality.

        Factors:
        - Base quality score from SkillSelector
        - Error handling presence
        - Type hints usage
        - Code structure

        Args:
            skill: Skill to score

        Returns:
            Quality score (0-100)
        """
        # Start with base quality score
        score = skill.quality_score

        # Bonus for error handling
        if skill.code_example and ("try" in skill.code_example or "except" in skill.code_example):
            score += 5.0

        # Bonus for type hints
        if skill.code_example and "->" in skill.code_example:
            score += 5.0

        # Cap at 100
        return min(score, 100.0)

    def _score_completeness(self, skill: Skill) -> float:
        """
        Score feature completeness.

        Factors:
        - Description length (more detailed = more complete)
        - Code example presence and length
        - Pattern coverage

        Args:
            skill: Skill to score

        Returns:
            Completeness score (0-100)
        """
        score = 50.0  # Base score

        # Bonus for detailed description
        if len(skill.description) > 100:
            score += 20.0
        elif len(skill.description) > 50:
            score += 10.0

        # Bonus for code example
        if skill.code_example:
            if len(skill.code_example) > 200:
                score += 20.0
            elif len(skill.code_example) > 100:
                score += 10.0

        # Bonus for pattern coverage (if available)
        patterns = getattr(skill, "patterns", None)
        if patterns:
            score += min(len(patterns) * 5.0, 20.0)

        # Cap at 100
        return min(score, 100.0)

    def _score_maintainability(self, skill: Skill) -> float:
        """
        Score maintainability.

        Factors:
        - Documentation quality (description length)
        - Code readability (example structure)
        - Best practices (patterns used)

        Args:
            skill: Skill to score

        Returns:
            Maintainability score (0-100)
        """
        score = 50.0  # Base score

        # Bonus for good documentation
        if len(skill.description) > 150:
            score += 25.0
        elif len(skill.description) > 75:
            score += 15.0

        # Bonus for code example (shows how to use)
        if skill.code_example:
            score += 15.0

        # Bonus for best practices (patterns, if available)
        patterns = getattr(skill, "patterns", None)
        if patterns:
            score += min(len(patterns) * 5.0, 15.0)

        # Cap at 100
        return min(score, 100.0)

    def _score_performance(self, skill: Skill) -> float:
        """
        Score performance characteristics.

        Factors:
        - Async usage (better performance)
        - Caching patterns
        - Rate limiting (prevents overload)
        - Circuit breaker (resilience)

        Args:
            skill: Skill to score

        Returns:
            Performance score (0-100)
        """
        score = 50.0  # Base score

        if not skill.code_example:
            return score

        code = skill.code_example.lower()

        # Bonus for async
        if "async" in code or "await" in code:
            score += 15.0

        # Bonus for performance patterns
        if "cache" in code or "cached" in code:
            score += 15.0

        if "rate" in code and "limit" in code:
            score += 10.0

        if "circuit" in code and "breaker" in code:
            score += 10.0

        # Cap at 100
        return min(score, 100.0)
