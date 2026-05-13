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

import structlog

from AIM.src.aim.teacher.skills.skill_selector import Skill

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
