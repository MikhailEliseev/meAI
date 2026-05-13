"""
Skill Comparator - Compare GitHub skills with our implementations.

Scoring dimensions:
- Completeness (0-100): How complete is the implementation
- Quality (0-100): Code quality, error handling, tests
- Performance (0-100): Efficiency, optimization
- Maintainability (0-100): Documentation, structure
- Security (0-100): Input validation, error handling
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog

from AIM.src.aim.teacher.skills.skill_extractor import ExtractedSkill, SkillType

logger = structlog.get_logger()


@dataclass
class SkillScore:
    """Score for a skill implementation."""
    skill_type: SkillType
    source: str  # "github" or "ours"
    completeness: float  # 0-100
    quality: float  # 0-100
    performance: float  # 0-100
    maintainability: float  # 0-100
    security: float  # 0-100
    total_score: float  # 0-100 (weighted average)
    strengths: list[str]
    weaknesses: list[str]
    metadata: dict[str, Any]


@dataclass
class ComparisonResult:
    """Result of comparing GitHub skill with ours."""
    skill_type: SkillType
    github_score: SkillScore
    our_score: SkillScore
    recommendation: str  # "adopt", "improve", "keep_ours"
    gap_analysis: str
    action_items: list[str]


class SkillComparator:
    """
    Compare GitHub skills with our implementations.

    Scoring weights (medical context):
    - Security: 30% (critical for medical data)
    - Quality: 25% (reliability is key)
    - Completeness: 20% (feature coverage)
    - Maintainability: 15% (long-term support)
    - Performance: 10% (important but not critical)
    """

    def __init__(
        self,
        weights: dict[str, float] | None = None,
    ):
        """
        Initialize SkillComparator.

        Args:
            weights: Custom scoring weights (default: medical context weights)
        """
        self.weights = weights or {
            "security": 0.30,
            "quality": 0.25,
            "completeness": 0.20,
            "maintainability": 0.15,
            "performance": 0.10,
        }
        logger.info("skill_comparator_initialized", weights=self.weights)

    async def compare_skills(
        self,
        github_skill: ExtractedSkill,
        our_skill: ExtractedSkill | None,
    ) -> ComparisonResult:
        """
        Compare GitHub skill with our implementation.

        Args:
            github_skill: Skill extracted from GitHub
            our_skill: Our current implementation (None if we don't have it)

        Returns:
            Comparison result with recommendation
        """
        logger.info(
            "comparing_skills",
            skill_type=github_skill.skill_type,
            has_our_implementation=our_skill is not None,
        )

        # Score GitHub skill
        github_score = await self._score_skill(
            skill=github_skill,
            source="github",
        )

        # Score our skill (or create empty score)
        if our_skill:
            our_score = await self._score_skill(
                skill=our_skill,
                source="ours",
            )
        else:
            our_score = self._create_empty_score(github_skill.skill_type)

        # Generate recommendation
        recommendation = self._generate_recommendation(
            github_score=github_score,
            our_score=our_score,
        )

        # Gap analysis
        gap_analysis = self._analyze_gaps(
            github_score=github_score,
            our_score=our_score,
        )

        # Action items
        action_items = self._generate_action_items(
            github_skill=github_skill,
            github_score=github_score,
            our_score=our_score,
            recommendation=recommendation,
        )

        logger.info(
            "comparison_complete",
            skill_type=github_skill.skill_type,
            recommendation=recommendation,
            github_total=github_score.total_score,
            our_total=our_score.total_score,
        )

        return ComparisonResult(
            skill_type=github_skill.skill_type,
            github_score=github_score,
            our_score=our_score,
            recommendation=recommendation,
            gap_analysis=gap_analysis,
            action_items=action_items,
        )

    async def _score_skill(
        self,
        skill: ExtractedSkill,
        source: str,
    ) -> SkillScore:
        """
        Score a skill implementation.

        Returns:
            Skill score with breakdown
        """
        # Score each dimension
        completeness = self._score_completeness(skill)
        quality = self._score_quality(skill)
        performance = self._score_performance(skill)
        maintainability = self._score_maintainability(skill)
        security = self._score_security(skill)

        # Calculate weighted total
        total_score = (
            completeness * self.weights["completeness"]
            + quality * self.weights["quality"]
            + performance * self.weights["performance"]
            + maintainability * self.weights["maintainability"]
            + security * self.weights["security"]
        )

        # Identify strengths and weaknesses
        scores = {
            "completeness": completeness,
            "quality": quality,
            "performance": performance,
            "maintainability": maintainability,
            "security": security,
        }
        strengths = [k for k, v in scores.items() if v >= 80]
        weaknesses = [k for k, v in scores.items() if v < 60]

        return SkillScore(
            skill_type=skill.skill_type,
            source=source,
            completeness=completeness,
            quality=quality,
            performance=performance,
            maintainability=maintainability,
            security=security,
            total_score=total_score,
            strengths=strengths,
            weaknesses=weaknesses,
            metadata={
                "confidence": skill.confidence,
                "dependencies": skill.dependencies,
                "file_path": skill.file_path,
            },
        )

    def _score_completeness(self, skill: ExtractedSkill) -> float:
        """
        Score completeness (0-100).

        Checks:
        - Has implementation (not just interface)
        - Has error handling
        - Has configuration options
        - Has documentation
        """
        score = 0.0

        code = skill.code_snippet.lower()

        # Has implementation (not just pass/raise)
        if "pass" not in code and len(code) > 50:
            score += 40

        # Has error handling
        if "try" in code or "except" in code or "raise" in code:
            score += 20

        # Has configuration (parameters, settings)
        if "=" in code and ("self." in code or "config" in code):
            score += 20

        # Has documentation
        if '"""' in skill.code_snippet or "'''" in skill.code_snippet:
            score += 20

        return min(score, 100.0)

    def _score_quality(self, skill: ExtractedSkill) -> float:
        """
        Score quality (0-100).

        Checks:
        - Type hints
        - Error handling
        - Logging
        - Validation
        """
        score = 0.0

        code = skill.code_snippet

        # Type hints
        if "->" in code or ": " in code:
            score += 25

        # Error handling
        if "try" in code.lower() and "except" in code.lower():
            score += 25

        # Logging
        if "log" in code.lower() or "logger" in code.lower():
            score += 25

        # Validation
        if "if" in code.lower() and ("raise" in code.lower() or "return" in code.lower()):
            score += 25

        return min(score, 100.0)

    def _score_performance(self, skill: ExtractedSkill) -> float:
        """
        Score performance (0-100).

        Checks:
        - Async/await usage
        - Caching
        - Batch operations
        - Resource cleanup
        """
        score = 50.0  # Base score

        code = skill.code_snippet.lower()

        # Async/await
        if "async" in code and "await" in code:
            score += 20

        # Caching
        if "cache" in code or "@cached" in code:
            score += 15

        # Batch operations
        if "batch" in code or "bulk" in code:
            score += 10

        # Resource cleanup
        if "close" in code or "cleanup" in code or "finally" in code:
            score += 5

        return min(score, 100.0)

    def _score_maintainability(self, skill: ExtractedSkill) -> float:
        """
        Score maintainability (0-100).

        Checks:
        - Documentation
        - Clear naming
        - Modular structure
        - Dependencies
        """
        score = 0.0

        code = skill.code_snippet

        # Documentation
        if '"""' in code or "'''" in code:
            score += 30

        # Clear naming (not single letters)
        lines = code.split("\n")
        clear_names = sum(1 for line in lines if "def " in line and len(line.split("def ")[1].split("(")[0]) > 2)
        if clear_names > 0:
            score += 25

        # Modular (multiple functions/methods)
        if code.count("def ") > 1:
            score += 25

        # Minimal dependencies
        if len(skill.dependencies) <= 2:
            score += 20

        return min(score, 100.0)

    def _score_security(self, skill: ExtractedSkill) -> float:
        """
        Score security (0-100).

        Checks:
        - Input validation
        - Error handling
        - No hardcoded secrets
        - Safe operations
        """
        score = 50.0  # Base score

        code = skill.code_snippet.lower()

        # Input validation
        if "if" in code and ("raise" in code or "assert" in code):
            score += 20

        # Error handling
        if "try" in code and "except" in code:
            score += 15

        # No hardcoded secrets (check for common patterns)
        secret_patterns = ["password", "api_key", "token", "secret", "apikey"]
        has_secrets = any(pattern in code and "=" in code for pattern in secret_patterns)
        if not has_secrets:
            score += 10
        else:
            score -= 40  # Stronger penalty for hardcoded secrets

        # Safe operations (no eval, exec, shell)
        if not any(pattern in code for pattern in ["eval(", "exec(", "shell=true", "os.system"]):
            score += 5
        else:
            score -= 30  # Penalty for unsafe operations

        return max(min(score, 100.0), 0.0)

    def _create_empty_score(self, skill_type: SkillType) -> SkillScore:
        """Create empty score for missing implementation."""
        return SkillScore(
            skill_type=skill_type,
            source="ours",
            completeness=0.0,
            quality=0.0,
            performance=0.0,
            maintainability=0.0,
            security=0.0,
            total_score=0.0,
            strengths=[],
            weaknesses=["completeness", "quality", "performance", "maintainability", "security"],
            metadata={},
        )

    def _generate_recommendation(
        self,
        github_score: SkillScore,
        our_score: SkillScore,
    ) -> str:
        """
        Generate recommendation based on scores.

        Rules:
        - adopt: GitHub significantly better (>20 points)
        - improve: GitHub better but close (<20 points)
        - keep_ours: Our implementation is better
        """
        diff = github_score.total_score - our_score.total_score

        if diff > 20:
            return "adopt"
        elif diff > 0:
            return "improve"
        else:
            return "keep_ours"

    def _analyze_gaps(
        self,
        github_score: SkillScore,
        our_score: SkillScore,
    ) -> str:
        """
        Analyze gaps between GitHub and our implementation.

        Returns:
            Gap analysis text
        """
        gaps = []

        # Check each dimension
        dimensions = ["completeness", "quality", "performance", "maintainability", "security"]
        for dim in dimensions:
            github_val = getattr(github_score, dim)
            our_val = getattr(our_score, dim)
            diff = github_val - our_val

            if diff > 15:
                gaps.append(f"- {dim.title()}: GitHub {github_val:.0f} vs Ours {our_val:.0f} (+{diff:.0f})")

        if not gaps:
            return "No significant gaps found."

        return "Gaps found:\n" + "\n".join(gaps)

    def _generate_action_items(
        self,
        github_skill: ExtractedSkill,
        github_score: SkillScore,
        our_score: SkillScore,
        recommendation: str,
    ) -> list[str]:
        """
        Generate action items based on comparison.

        Returns:
            List of action items
        """
        actions = []

        if recommendation == "adopt":
            actions.append(f"Adopt GitHub implementation from {github_skill.file_path}")
            actions.append(f"Install dependencies: {', '.join(github_skill.dependencies)}")
            actions.append("Test integration with Event Bus")
            actions.append("Update documentation")

        elif recommendation == "improve":
            # Focus on weaknesses
            for weakness in our_score.weaknesses:
                if weakness in github_score.strengths:
                    actions.append(f"Improve {weakness} (learn from GitHub)")

            # Add specific improvements
            if "security" in our_score.weaknesses:
                actions.append("Add input validation and error handling")
            if "quality" in our_score.weaknesses:
                actions.append("Add type hints and logging")
            if "performance" in our_score.weaknesses:
                actions.append("Add caching and async operations")

        else:  # keep_ours
            actions.append("Keep our implementation")
            # But still learn from GitHub strengths
            for strength in github_score.strengths:
                if strength not in our_score.strengths:
                    actions.append(f"Consider adopting {strength} pattern from GitHub")

        return actions
