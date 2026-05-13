"""
Skill Selector - Select best skills based on comparison results.

Selection strategy:
- Threshold-based filtering (min score to adopt)
- Priority-based ranking (security > quality > completeness)
- Conflict resolution (multiple skills for same type)
- Budget constraints (max skills to adopt)
"""

from dataclasses import dataclass
from typing import Any

import structlog

from AIM.src.aim.teacher.skills.skill_comparator import ComparisonResult
from AIM.src.aim.teacher.skills.skill_extractor import SkillType

logger = structlog.get_logger()


@dataclass
class SelectionCriteria:
    """Criteria for skill selection."""
    min_score_threshold: float = 70.0  # Min total score to consider
    min_improvement_threshold: float = 10.0  # Min improvement over ours
    max_skills_per_type: int = 3  # Max skills to select per type
    prioritize_security: bool = True  # Prioritize high security scores
    budget_limit: int | None = None  # Max total skills to adopt


@dataclass
class SelectedSkill:
    """Selected skill with selection rationale."""
    comparison: ComparisonResult
    selection_score: float  # 0-100 (priority score)
    selection_reason: str
    priority: int  # 1 (highest) to N (lowest)
    metadata: dict[str, Any]


class SkillSelector:
    """
    Select best skills based on comparison results.

    Selection algorithm:
    1. Filter by threshold (min score, min improvement)
    2. Rank by priority (security weight, total score)
    3. Resolve conflicts (best per skill type)
    4. Apply budget (top N skills)
    """

    def __init__(
        self,
        criteria: SelectionCriteria | None = None,
    ):
        """
        Initialize SkillSelector.

        Args:
            criteria: Selection criteria (default: medical context)
        """
        self.criteria = criteria or SelectionCriteria()
        logger.info(
            "skill_selector_initialized",
            min_score=self.criteria.min_score_threshold,
            min_improvement=self.criteria.min_improvement_threshold,
        )

    async def select_skills(
        self,
        comparisons: list[ComparisonResult],
    ) -> list[SelectedSkill]:
        """
        Select best skills from comparison results.

        Args:
            comparisons: List of comparison results

        Returns:
            List of selected skills (sorted by priority)
        """
        logger.info(
            "selecting_skills",
            total_comparisons=len(comparisons),
        )

        # Step 1: Filter by threshold
        filtered = self._filter_by_threshold(comparisons)
        logger.info(
            "filtered_by_threshold",
            remaining=len(filtered),
        )

        # Step 2: Rank by priority
        ranked = self._rank_by_priority(filtered)
        logger.info(
            "ranked_by_priority",
            total=len(ranked),
        )

        # Step 3: Resolve conflicts (best per type)
        resolved = self._resolve_conflicts(ranked)
        logger.info(
            "conflicts_resolved",
            remaining=len(resolved),
        )

        # Step 4: Apply budget
        selected = self._apply_budget(resolved)
        logger.info(
            "budget_applied",
            selected=len(selected),
        )

        # Assign priorities
        for i, skill in enumerate(selected, start=1):
            skill.priority = i

        logger.info(
            "selection_complete",
            selected_count=len(selected),
        )

        return selected

    def _filter_by_threshold(
        self,
        comparisons: list[ComparisonResult],
    ) -> list[ComparisonResult]:
        """
        Filter comparisons by threshold.

        Keeps only:
        - GitHub score >= min_score_threshold
        - Improvement >= min_improvement_threshold
        - Recommendation is "adopt" or "improve"
        """
        filtered = []

        for comp in comparisons:
            github_score = comp.github_score.total_score
            our_score = comp.our_score.total_score
            improvement = github_score - our_score

            # Check thresholds
            if github_score < self.criteria.min_score_threshold:
                logger.debug(
                    "filtered_low_score",
                    skill_type=comp.skill_type,
                    score=github_score,
                )
                continue

            if improvement < self.criteria.min_improvement_threshold:
                logger.debug(
                    "filtered_low_improvement",
                    skill_type=comp.skill_type,
                    improvement=improvement,
                )
                continue

            # Check recommendation
            if comp.recommendation not in ["adopt", "improve"]:
                logger.debug(
                    "filtered_recommendation",
                    skill_type=comp.skill_type,
                    recommendation=comp.recommendation,
                )
                continue

            filtered.append(comp)

        return filtered

    def _rank_by_priority(
        self,
        comparisons: list[ComparisonResult],
    ) -> list[tuple[ComparisonResult, float]]:
        """
        Rank comparisons by priority score.

        Priority calculation:
        - Base: GitHub total score (0-100)
        - Bonus: Security score * 0.5 (if prioritize_security)
        - Bonus: Improvement over ours * 0.2
        """
        ranked = []

        for comp in comparisons:
            github_score = comp.github_score.total_score
            security_score = comp.github_score.security
            improvement = github_score - comp.our_score.total_score

            # Calculate priority score
            priority_score = github_score

            if self.criteria.prioritize_security:
                priority_score += security_score * 0.5  # Increased from 0.3

            priority_score += improvement * 0.2

            ranked.append((comp, priority_score))

        # Sort by priority score (descending)
        ranked.sort(key=lambda x: x[1], reverse=True)

        return ranked

    def _resolve_conflicts(
        self,
        ranked: list[tuple[ComparisonResult, float]],
    ) -> list[tuple[ComparisonResult, float]]:
        """
        Resolve conflicts (multiple skills per type).

        Keeps only top N skills per type (max_skills_per_type).
        """
        # Group by skill type
        by_type: dict[SkillType, list[tuple[ComparisonResult, float]]] = {}
        for comp, score in ranked:
            if comp.skill_type not in by_type:
                by_type[comp.skill_type] = []
            by_type[comp.skill_type].append((comp, score))

        # Keep top N per type
        resolved = []
        for skill_type, skills in by_type.items():
            top_n = skills[:self.criteria.max_skills_per_type]
            resolved.extend(top_n)

            if len(skills) > self.criteria.max_skills_per_type:
                logger.info(
                    "conflict_resolved",
                    skill_type=skill_type,
                    total=len(skills),
                    kept=len(top_n),
                )

        # Re-sort by priority score
        resolved.sort(key=lambda x: x[1], reverse=True)

        return resolved

    def _apply_budget(
        self,
        ranked: list[tuple[ComparisonResult, float]],
    ) -> list[SelectedSkill]:
        """
        Apply budget limit (max skills to adopt).

        Returns:
            List of selected skills
        """
        # Apply budget
        if self.criteria.budget_limit:
            ranked = ranked[:self.criteria.budget_limit]
            logger.info(
                "budget_limit_applied",
                limit=self.criteria.budget_limit,
                selected=len(ranked),
            )

        # Convert to SelectedSkill
        selected = []
        for comp, priority_score in ranked:
            reason = self._generate_selection_reason(comp, priority_score)

            selected_skill = SelectedSkill(
                comparison=comp,
                selection_score=priority_score,
                selection_reason=reason,
                priority=0,  # Will be assigned later
                metadata={
                    "github_score": comp.github_score.total_score,
                    "our_score": comp.our_score.total_score,
                    "improvement": comp.github_score.total_score - comp.our_score.total_score,
                    "recommendation": comp.recommendation,
                },
            )
            selected.append(selected_skill)

        return selected

    def _generate_selection_reason(
        self,
        comp: ComparisonResult,
        priority_score: float,
    ) -> str:
        """
        Generate selection reason.

        Returns:
            Human-readable reason
        """
        github_score = comp.github_score.total_score
        our_score = comp.our_score.total_score
        improvement = github_score - our_score

        reasons = []

        # High score
        if github_score >= 85:
            reasons.append(f"Excellent quality ({github_score:.0f}/100)")
        elif github_score >= 70:
            reasons.append(f"Good quality ({github_score:.0f}/100)")

        # Significant improvement
        if improvement >= 30:
            reasons.append(f"Major improvement (+{improvement:.0f} points)")
        elif improvement >= 20:
            reasons.append(f"Significant improvement (+{improvement:.0f} points)")
        elif improvement >= 10:
            reasons.append(f"Notable improvement (+{improvement:.0f} points)")

        # Security strength
        if comp.github_score.security >= 80:
            reasons.append(f"Strong security ({comp.github_score.security:.0f}/100)")

        # Quality strength
        if comp.github_score.quality >= 80:
            reasons.append(f"High code quality ({comp.github_score.quality:.0f}/100)")

        if not reasons:
            reasons.append("Meets selection criteria")

        return "; ".join(reasons)

    def format_selection_report(
        self,
        selected: list[SelectedSkill],
    ) -> str:
        """
        Format selection report as markdown.

        Args:
            selected: List of selected skills

        Returns:
            Markdown report
        """
        lines = [
            "# Skill Selection Report",
            "",
            f"**Selected:** {len(selected)} skills",
            f"**Criteria:** Score ≥ {self.criteria.min_score_threshold}, Improvement ≥ {self.criteria.min_improvement_threshold}",
            "",
            "## Selected Skills",
            "",
        ]

        for skill in selected:
            comp = skill.comparison
            lines.extend([
                f"### {skill.priority}. {comp.skill_type.value.replace('_', ' ').title()}",
                "",
                f"**Priority Score:** {skill.selection_score:.1f}",
                f"**Reason:** {skill.selection_reason}",
                "",
                f"**Scores:**",
                f"- GitHub: {comp.github_score.total_score:.0f}/100",
                f"- Ours: {comp.our_score.total_score:.0f}/100",
                f"- Improvement: +{skill.metadata['improvement']:.0f} points",
                "",
                f"**Recommendation:** {comp.recommendation}",
                "",
                f"**Action Items:**",
            ])

            for item in comp.action_items:
                lines.append(f"- {item}")

            lines.append("")

        return "\n".join(lines)
