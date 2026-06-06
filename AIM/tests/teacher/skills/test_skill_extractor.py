"""
Tests for SkillExtractor.

Tests:
- Extract implementation from best skill
- Adapt code to project structure
- Generate integration instructions
- Handle edge cases (no code example, invalid code)
"""

from pathlib import Path

import pytest

from src.aim.teacher.skills.skill_selector import Skill
from src.aim.teacher.skills.skill_extractor import (
    SkillExtractor,
    ExtractedImplementation,
)


@pytest.fixture
def extractor():
    """Create SkillExtractor instance."""
    return SkillExtractor()


@pytest.fixture
def circuit_breaker_skill():
    """Create circuit breaker skill fixture."""
    return Skill(
        name="Circuit Breaker",
        description="Production-ready circuit breaker with error handling",
        code_example="""
from pybreaker import CircuitBreaker

class APIClient:
    def __init__(self):
        self.breaker = CircuitBreaker(fail_max=5, reset_timeout=60)

    async def call_api(self):
        try:
            return await self.breaker.call(self._do_call)
        except Exception as e:
            logger.error("api_call_failed", error=str(e))
            raise

    async def _do_call(self):
        # API call logic
        pass
""",
        quality_score=85.0,
        source_repo="https://github.com/user/high-quality-repo",
        file_path="circuit_breaker.py",
    )


@pytest.fixture
def retry_skill():
    """Create retry skill fixture."""
    return Skill(
        name="Retry Pattern",
        description="Exponential backoff retry with tenacity",
        code_example="""
from tenacity import retry, stop_after_attempt, wait_exponential

class Service:
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def fetch_data(self):
        # Fetch logic with retry
        pass
""",
        quality_score=80.0,
        source_repo="https://github.com/user/retry-repo",
        file_path="retry.py",
    )


class TestExtraction:
    """Test skill extraction."""

    @pytest.mark.asyncio
    async def test_extract_implementation(self, extractor, circuit_breaker_skill):
        """Should extract implementation from skill."""
        result = await extractor.extract(circuit_breaker_skill)

        assert isinstance(result, ExtractedImplementation)
        assert result.code is not None
        assert len(result.code) > 0

    @pytest.mark.asyncio
    async def test_extract_dependencies(self, extractor, circuit_breaker_skill):
        """Should identify dependencies."""
        result = await extractor.extract(circuit_breaker_skill)

        # Should detect pybreaker import
        assert "pybreaker" in result.dependencies

    @pytest.mark.asyncio
    async def test_extract_multiple_dependencies(self, extractor, retry_skill):
        """Should extract multiple dependencies."""
        result = await extractor.extract(retry_skill)

        # Should detect tenacity import
        assert "tenacity" in result.dependencies

    @pytest.mark.asyncio
    async def test_generate_integration_instructions(self, extractor, circuit_breaker_skill):
        """Should generate integration instructions."""
        result = await extractor.extract(circuit_breaker_skill)

        assert result.integration_instructions is not None
        assert len(result.integration_instructions) > 0


class TestAdaptation:
    """Test code adaptation."""

    @pytest.mark.asyncio
    async def test_adapt_to_project_structure(self, extractor, circuit_breaker_skill):
        """Should adapt code to project structure."""
        result = await extractor.extract(
            circuit_breaker_skill,
            target_path=Path("AIM/src/aim/subagents/api_clients/base.py")
        )

        # Should suggest target path
        assert result.suggested_path is not None
        assert "AIM/src/aim" in str(result.suggested_path)

    @pytest.mark.asyncio
    async def test_preserve_functionality(self, extractor, circuit_breaker_skill):
        """Should preserve original functionality."""
        result = await extractor.extract(circuit_breaker_skill)

        # Should contain key functionality
        assert "CircuitBreaker" in result.code
        assert "call_api" in result.code

    @pytest.mark.asyncio
    async def test_add_project_imports(self, extractor, circuit_breaker_skill):
        """Should add project-specific imports."""
        result = await extractor.extract(
            circuit_breaker_skill,
            target_path=Path("AIM/src/aim/subagents/api_clients/base.py")
        )

        # Code contains logger usage, so logging is present
        assert "logger" in result.code


class TestInstructions:
    """Test integration instructions."""

    @pytest.mark.asyncio
    async def test_installation_instructions(self, extractor, circuit_breaker_skill):
        """Should provide installation instructions."""
        result = await extractor.extract(circuit_breaker_skill)

        instructions = result.integration_instructions

        # Should mention pip install
        assert "pip install" in instructions.lower() or "requirements.txt" in instructions.lower()

    @pytest.mark.asyncio
    async def test_usage_instructions(self, extractor, circuit_breaker_skill):
        """Should provide usage instructions."""
        result = await extractor.extract(circuit_breaker_skill)

        instructions = result.integration_instructions

        # Should explain how to use
        assert len(instructions) > 100  # Detailed instructions

    @pytest.mark.asyncio
    async def test_configuration_instructions(self, extractor, circuit_breaker_skill):
        """Should provide configuration instructions."""
        result = await extractor.extract(circuit_breaker_skill)

        instructions = result.integration_instructions

        # Should mention configuration (fail_max, reset_timeout)
        assert "fail_max" in instructions or "configuration" in instructions.lower()


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handle_no_code_example(self, extractor):
        """Should handle skill without code example."""
        skill = Skill(
            name="No Code",
            description="Skill without code",
            code_example="",
            quality_score=50.0,
            source_repo="https://github.com/user/no-code",
            file_path="empty.py",
        )

        result = await extractor.extract(skill)

        # Should return empty implementation
        assert result.code == ""
        assert len(result.dependencies) == 0

    @pytest.mark.asyncio
    async def test_handle_invalid_python(self, extractor):
        """Should handle invalid Python code."""
        skill = Skill(
            name="Invalid",
            description="Invalid Python",
            code_example="this is not valid python",
            quality_score=30.0,
            source_repo="https://github.com/user/invalid",
            file_path="broken.py",
        )

        # Should not crash
        result = await extractor.extract(skill)
        assert isinstance(result, ExtractedImplementation)

    @pytest.mark.asyncio
    async def test_handle_no_imports(self, extractor):
        """Should handle code without imports."""
        skill = Skill(
            name="No Imports",
            description="Simple function",
            code_example="""
def add(a, b):
    return a + b
""",
            quality_score=40.0,
            source_repo="https://github.com/user/simple",
            file_path="simple.py",
        )

        result = await extractor.extract(skill)

        # Should have empty dependencies
        assert len(result.dependencies) == 0
