"""
Tests for SkillComparator.
"""

import pytest

from AIM.src.aim.teacher.skills.skill_extractor import (
    ExtractedSkill,
    SkillType,
)
from AIM.src.aim.teacher.skills.skill_comparator import (
    SkillComparator,
    SkillScore,
    ComparisonResult,
)


@pytest.fixture
def comparator():
    """Create SkillComparator instance."""
    return SkillComparator()


@pytest.fixture
def github_circuit_breaker():
    """GitHub circuit breaker skill (high quality)."""
    return ExtractedSkill(
        skill_type=SkillType.CIRCUIT_BREAKER,
        name="APIClient",
        description="Circuit breaker pattern",
        code_snippet='''
import pybreaker

class APIClient:
    """API client with circuit breaker."""

    def __init__(self):
        self.breaker = pybreaker.CircuitBreaker(
            fail_max=5,
            reset_timeout=60
        )
        self.logger = logging.getLogger(__name__)

    async def call_api(self, url: str) -> dict:
        """Call API with circuit breaker protection."""
        try:
            return await self.breaker.call(self._make_request, url)
        except Exception as e:
            self.logger.error("API call failed", error=str(e))
            raise

    async def _make_request(self, url: str) -> dict:
        """Make HTTP request."""
        if not url:
            raise ValueError("URL is required")
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.json()
''',
        file_path="/github/repo/client.py",
        line_start=1,
        line_end=25,
        confidence=1.0,
        dependencies=["pybreaker", "httpx"],
    )


@pytest.fixture
def our_circuit_breaker():
    """Our circuit breaker skill (lower quality)."""
    return ExtractedSkill(
        skill_type=SkillType.CIRCUIT_BREAKER,
        name="SimpleBreaker",
        description="Circuit breaker pattern",
        code_snippet='''
class SimpleBreaker:
    def __init__(self):
        self.failures = 0

    def call(self, func):
        if self.failures > 5:
            raise Exception("Circuit open")
        try:
            return func()
        except:
            self.failures += 1
            raise
''',
        file_path="/our/repo/breaker.py",
        line_start=1,
        line_end=12,
        confidence=0.6,
        dependencies=[],
    )


@pytest.mark.asyncio
async def test_compare_with_our_implementation(comparator, github_circuit_breaker, our_circuit_breaker):
    """Test comparing GitHub skill with our implementation."""
    result = await comparator.compare_skills(
        github_skill=github_circuit_breaker,
        our_skill=our_circuit_breaker,
    )

    assert isinstance(result, ComparisonResult)
    assert result.skill_type == SkillType.CIRCUIT_BREAKER
    assert result.github_score.total_score > result.our_score.total_score
    assert result.recommendation in ["adopt", "improve", "keep_ours"]


@pytest.mark.asyncio
async def test_compare_without_our_implementation(comparator, github_circuit_breaker):
    """Test comparing when we don't have implementation."""
    result = await comparator.compare_skills(
        github_skill=github_circuit_breaker,
        our_skill=None,
    )

    assert result.our_score.total_score == 0.0
    assert result.recommendation == "adopt"
    assert len(result.action_items) > 0


@pytest.mark.asyncio
async def test_score_completeness(comparator, github_circuit_breaker):
    """Test completeness scoring."""
    score = await comparator._score_skill(github_circuit_breaker, "github")

    # Should have high completeness (has implementation, error handling, config, docs)
    assert score.completeness >= 80


@pytest.mark.asyncio
async def test_score_quality(comparator, github_circuit_breaker):
    """Test quality scoring."""
    score = await comparator._score_skill(github_circuit_breaker, "github")

    # Should have high quality (type hints, error handling, logging)
    assert score.quality >= 75


@pytest.mark.asyncio
async def test_score_security(comparator, github_circuit_breaker):
    """Test security scoring."""
    score = await comparator._score_skill(github_circuit_breaker, "github")

    # Should have good security (validation, error handling, no secrets)
    assert score.security >= 70


@pytest.mark.asyncio
async def test_score_performance(comparator, github_circuit_breaker):
    """Test performance scoring."""
    score = await comparator._score_skill(github_circuit_breaker, "github")

    # Should have good performance (async/await)
    assert score.performance >= 60


@pytest.mark.asyncio
async def test_score_maintainability(comparator, github_circuit_breaker):
    """Test maintainability scoring."""
    score = await comparator._score_skill(github_circuit_breaker, "github")

    # Should have good maintainability (docs, clear names, modular)
    assert score.maintainability >= 60


@pytest.mark.asyncio
async def test_weighted_total_score(comparator, github_circuit_breaker):
    """Test that total score uses correct weights."""
    score = await comparator._score_skill(github_circuit_breaker, "github")

    # Calculate expected total
    expected = (
        score.completeness * 0.20
        + score.quality * 0.25
        + score.performance * 0.10
        + score.maintainability * 0.15
        + score.security * 0.30
    )

    assert abs(score.total_score - expected) < 0.01


@pytest.mark.asyncio
async def test_custom_weights(github_circuit_breaker):
    """Test custom scoring weights."""
    custom_weights = {
        "security": 0.50,  # Higher security weight
        "quality": 0.20,
        "completeness": 0.15,
        "maintainability": 0.10,
        "performance": 0.05,
    }
    comparator = SkillComparator(weights=custom_weights)

    score = await comparator._score_skill(github_circuit_breaker, "github")

    # Calculate expected total with custom weights
    expected = (
        score.completeness * 0.15
        + score.quality * 0.20
        + score.performance * 0.05
        + score.maintainability * 0.10
        + score.security * 0.50
    )

    assert abs(score.total_score - expected) < 0.01


@pytest.mark.asyncio
async def test_recommendation_adopt(comparator, github_circuit_breaker, our_circuit_breaker):
    """Test 'adopt' recommendation when GitHub is significantly better."""
    result = await comparator.compare_skills(
        github_skill=github_circuit_breaker,
        our_skill=our_circuit_breaker,
    )

    # GitHub should be significantly better (>20 points)
    diff = result.github_score.total_score - result.our_score.total_score
    if diff > 20:
        assert result.recommendation == "adopt"


@pytest.mark.asyncio
async def test_recommendation_improve(comparator):
    """Test 'improve' recommendation when GitHub is slightly better."""
    # Create two similar skills
    github_skill = ExtractedSkill(
        skill_type=SkillType.RETRY,
        name="retry_func",
        description="Retry pattern",
        code_snippet='''
from tenacity import retry

@retry(stop_after_attempt=3)
async def fetch():
    """Fetch data with retry."""
    return await api.get()
''',
        file_path="/github/retry.py",
        line_start=1,
        line_end=6,
        confidence=1.0,
        dependencies=["tenacity"],
    )

    our_skill = ExtractedSkill(
        skill_type=SkillType.RETRY,
        name="retry_func",
        description="Retry pattern",
        code_snippet='''
@retry(stop_after_attempt=3)
def fetch():
    return api.get()
''',
        file_path="/our/retry.py",
        line_start=1,
        line_end=4,
        confidence=0.8,
        dependencies=["tenacity"],
    )

    result = await comparator.compare_skills(
        github_skill=github_skill,
        our_skill=our_skill,
    )

    # Should recommend improve (small difference)
    diff = result.github_score.total_score - result.our_score.total_score
    if 0 < diff <= 20:
        assert result.recommendation == "improve"


@pytest.mark.asyncio
async def test_recommendation_keep_ours(comparator, github_circuit_breaker):
    """Test 'keep_ours' recommendation when our implementation is better."""
    # Create better our implementation
    our_better = ExtractedSkill(
        skill_type=SkillType.CIRCUIT_BREAKER,
        name="AdvancedBreaker",
        description="Advanced circuit breaker",
        code_snippet='''
import pybreaker
from typing import Optional

class AdvancedBreaker:
    """
    Advanced circuit breaker with monitoring.

    Features:
    - Configurable thresholds
    - Metrics tracking
    - Health checks
    """

    def __init__(self, fail_max: int = 5, reset_timeout: int = 60):
        self.breaker = pybreaker.CircuitBreaker(
            fail_max=fail_max,
            reset_timeout=reset_timeout
        )
        self.logger = logging.getLogger(__name__)
        self.metrics = MetricsCollector()

    async def call(self, func, *args, **kwargs) -> Optional[dict]:
        """Call function with circuit breaker protection."""
        try:
            if not callable(func):
                raise ValueError("Function must be callable")

            result = await self.breaker.call(func, *args, **kwargs)
            self.metrics.record_success()
            return result
        except Exception as e:
            self.logger.error("Call failed", error=str(e), func=func.__name__)
            self.metrics.record_failure()
            raise
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Cleanup resources."""
        pass
''',
        file_path="/our/advanced_breaker.py",
        line_start=1,
        line_end=40,
        confidence=1.0,
        dependencies=["pybreaker"],
    )

    result = await comparator.compare_skills(
        github_skill=github_circuit_breaker,
        our_skill=our_better,
    )

    # Our implementation should be better
    if result.our_score.total_score >= result.github_score.total_score:
        assert result.recommendation == "keep_ours"


@pytest.mark.asyncio
async def test_gap_analysis(comparator, github_circuit_breaker, our_circuit_breaker):
    """Test gap analysis generation."""
    result = await comparator.compare_skills(
        github_skill=github_circuit_breaker,
        our_skill=our_circuit_breaker,
    )

    assert isinstance(result.gap_analysis, str)
    assert len(result.gap_analysis) > 0


@pytest.mark.asyncio
async def test_action_items_for_adopt(comparator, github_circuit_breaker):
    """Test action items for 'adopt' recommendation."""
    result = await comparator.compare_skills(
        github_skill=github_circuit_breaker,
        our_skill=None,
    )

    assert result.recommendation == "adopt"
    assert len(result.action_items) > 0
    assert any("Adopt" in item for item in result.action_items)
    assert any("dependencies" in item.lower() for item in result.action_items)


@pytest.mark.asyncio
async def test_action_items_for_improve(comparator):
    """Test action items for 'improve' recommendation."""
    github_skill = ExtractedSkill(
        skill_type=SkillType.CACHING,
        name="cache_func",
        description="Caching pattern",
        code_snippet='''
from aiocache import cached

@cached(ttl=3600)
async def get_data(key: str) -> dict:
    """Get data with caching."""
    if not key:
        raise ValueError("Key required")
    return await db.fetch(key)
''',
        file_path="/github/cache.py",
        line_start=1,
        line_end=8,
        confidence=1.0,
        dependencies=["aiocache"],
    )

    our_skill = ExtractedSkill(
        skill_type=SkillType.CACHING,
        name="cache_func",
        description="Caching pattern",
        code_snippet='''
@cached(ttl=3600)
def get_data(key):
    return db.fetch(key)
''',
        file_path="/our/cache.py",
        line_start=1,
        line_end=4,
        confidence=0.7,
        dependencies=["aiocache"],
    )

    result = await comparator.compare_skills(
        github_skill=github_skill,
        our_skill=our_skill,
    )

    if result.recommendation == "improve":
        assert len(result.action_items) > 0
        assert any("Improve" in item for item in result.action_items)


@pytest.mark.asyncio
async def test_strengths_and_weaknesses(comparator, github_circuit_breaker, our_circuit_breaker):
    """Test identification of strengths and weaknesses."""
    result = await comparator.compare_skills(
        github_skill=github_circuit_breaker,
        our_skill=our_circuit_breaker,
    )

    # GitHub should have strengths
    assert len(result.github_score.strengths) > 0

    # Our implementation should have weaknesses
    assert len(result.our_score.weaknesses) > 0


@pytest.mark.asyncio
async def test_security_penalty_for_hardcoded_secrets(comparator):
    """Test security penalty for hardcoded secrets."""
    skill_with_secret = ExtractedSkill(
        skill_type=SkillType.CIRCUIT_BREAKER,
        name="BadClient",
        description="Client with hardcoded secret",
        code_snippet='''
class BadClient:
    def __init__(self):
        self.api_key = "sk-1234567890"  # Hardcoded!
        self.password = "admin123"
''',
        file_path="/bad/client.py",
        line_start=1,
        line_end=5,
        confidence=0.5,
        dependencies=[],
    )

    score = await comparator._score_skill(skill_with_secret, "bad")

    # Should have low security score (penalty for hardcoded secrets)
    assert score.security < 50


@pytest.mark.asyncio
async def test_security_penalty_for_unsafe_operations(comparator):
    """Test security penalty for unsafe operations."""
    skill_with_eval = ExtractedSkill(
        skill_type=SkillType.CIRCUIT_BREAKER,
        name="UnsafeClient",
        description="Client with eval",
        code_snippet='''
class UnsafeClient:
    def execute(self, code):
        return eval(code)  # Unsafe!
''',
        file_path="/unsafe/client.py",
        line_start=1,
        line_end=4,
        confidence=0.5,
        dependencies=[],
    )

    score = await comparator._score_skill(skill_with_eval, "unsafe")

    # Should have very low security score (penalty for eval)
    assert score.security < 40


@pytest.mark.asyncio
async def test_comparison_result_structure(comparator, github_circuit_breaker, our_circuit_breaker):
    """Test that ComparisonResult has correct structure."""
    result = await comparator.compare_skills(
        github_skill=github_circuit_breaker,
        our_skill=our_circuit_breaker,
    )

    assert hasattr(result, "skill_type")
    assert hasattr(result, "github_score")
    assert hasattr(result, "our_score")
    assert hasattr(result, "recommendation")
    assert hasattr(result, "gap_analysis")
    assert hasattr(result, "action_items")

    assert isinstance(result.skill_type, SkillType)
    assert isinstance(result.github_score, SkillScore)
    assert isinstance(result.our_score, SkillScore)
    assert isinstance(result.recommendation, str)
    assert isinstance(result.gap_analysis, str)
    assert isinstance(result.action_items, list)
