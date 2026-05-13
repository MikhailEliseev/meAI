"""
Tests for SkillExtractor.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from AIM.src.aim.teacher.skills.skill_extractor import (
    SkillExtractor,
    SkillType,
    ExtractedSkill,
)


@pytest.fixture
def skill_extractor():
    """Create SkillExtractor instance."""
    return SkillExtractor()


@pytest.fixture
def temp_repo():
    """Create temporary repository directory."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def create_python_file(repo_path: Path, filename: str, content: str) -> Path:
    """Create Python file in repository."""
    file_path = repo_path / filename
    file_path.write_text(content)
    return file_path


@pytest.mark.asyncio
async def test_extract_circuit_breaker_with_pybreaker(skill_extractor, temp_repo):
    """Test extracting circuit breaker with pybreaker library."""
    code = """
import pybreaker

class APIClient:
    def __init__(self):
        self.breaker = pybreaker.CircuitBreaker(
            fail_max=5,
            reset_timeout=60
        )

    async def call_api(self):
        return await self.breaker.call(self._make_request)
"""
    create_python_file(temp_repo, "client.py", code)

    skills = await skill_extractor.extract_skills(
        repo_path=temp_repo,
        skill_types=[SkillType.CIRCUIT_BREAKER],
    )

    assert len(skills) > 0
    skill = skills[0]
    assert skill.skill_type == SkillType.CIRCUIT_BREAKER
    assert skill.confidence >= 0.6
    assert "pybreaker" in skill.dependencies


@pytest.mark.asyncio
async def test_extract_retry_with_decorator(skill_extractor, temp_repo):
    """Test extracting retry pattern with decorator."""
    code = """
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def fetch_data():
    return await api.get("/data")
"""
    create_python_file(temp_repo, "fetcher.py", code)

    skills = await skill_extractor.extract_skills(
        repo_path=temp_repo,
        skill_types=[SkillType.RETRY],
    )

    assert len(skills) > 0
    skill = skills[0]
    assert skill.skill_type == SkillType.RETRY
    assert skill.confidence == 1.0
    assert "tenacity" in skill.dependencies


@pytest.mark.asyncio
async def test_extract_rate_limiting(skill_extractor, temp_repo):
    """Test extracting rate limiting pattern."""
    code = """
from aiolimiter import AsyncLimiter

class RateLimitedClient:
    def __init__(self):
        self.limiter = AsyncLimiter(max_rate=10, time_period=1)

    async def request(self):
        async with self.limiter:
            return await self._do_request()
"""
    create_python_file(temp_repo, "limiter.py", code)

    skills = await skill_extractor.extract_skills(
        repo_path=temp_repo,
        skill_types=[SkillType.RATE_LIMITING],
    )

    assert len(skills) > 0
    skill = skills[0]
    assert skill.skill_type == SkillType.RATE_LIMITING
    assert skill.confidence >= 0.6
    assert "aiolimiter" in skill.dependencies


@pytest.mark.asyncio
async def test_extract_caching_with_decorator(skill_extractor, temp_repo):
    """Test extracting caching pattern with decorator."""
    code = """
from aiocache import cached

@cached(ttl=3600)
async def get_user(user_id: int):
    return await db.fetch_user(user_id)
"""
    create_python_file(temp_repo, "cache.py", code)

    skills = await skill_extractor.extract_skills(
        repo_path=temp_repo,
        skill_types=[SkillType.CACHING],
    )

    assert len(skills) > 0
    skill = skills[0]
    assert skill.skill_type == SkillType.CACHING
    assert skill.confidence == 1.0
    assert "aiocache" in skill.dependencies


@pytest.mark.asyncio
async def test_extract_error_handling(skill_extractor, temp_repo):
    """Test extracting error handling pattern."""
    code = """
async def process_data():
    try:
        result = await fetch_data()
        return result
    except APIError as e:
        logger.error("API error", error=str(e))
        # Fallback to cache
        return await get_cached_data()
    except Exception as e:
        logger.critical("Unexpected error", error=str(e))
        raise
"""
    create_python_file(temp_repo, "processor.py", code)

    skills = await skill_extractor.extract_skills(
        repo_path=temp_repo,
        skill_types=[SkillType.ERROR_HANDLING],
    )

    assert len(skills) > 0
    skill = skills[0]
    assert skill.skill_type == SkillType.ERROR_HANDLING
    assert skill.confidence >= 0.5


@pytest.mark.asyncio
async def test_extract_multiple_skills(skill_extractor, temp_repo):
    """Test extracting multiple skill types from same file."""
    code = """
from tenacity import retry
from aiocache import cached
import pybreaker

@retry(stop_after_attempt=3)
@cached(ttl=300)
async def fetch_with_retry_and_cache():
    breaker = pybreaker.CircuitBreaker()
    return await breaker.call(api.fetch)
"""
    create_python_file(temp_repo, "multi.py", code)

    skills = await skill_extractor.extract_skills(
        repo_path=temp_repo,
        skill_types=[SkillType.RETRY, SkillType.CACHING, SkillType.CIRCUIT_BREAKER],
    )

    # Should find retry and caching (same function)
    assert len(skills) >= 2
    skill_types = {s.skill_type for s in skills}
    assert SkillType.RETRY in skill_types
    assert SkillType.CACHING in skill_types


@pytest.mark.asyncio
async def test_extract_all_skill_types(skill_extractor, temp_repo):
    """Test extracting all skill types (default)."""
    code = """
from tenacity import retry

@retry(stop_after_attempt=3)
async def fetch():
    pass
"""
    create_python_file(temp_repo, "all.py", code)

    # Don't specify skill_types (should extract all)
    skills = await skill_extractor.extract_skills(repo_path=temp_repo)

    # Should find at least retry
    assert len(skills) > 0


@pytest.mark.asyncio
async def test_extract_from_multiple_files(skill_extractor, temp_repo):
    """Test extracting skills from multiple files."""
    code1 = """
from tenacity import retry

@retry(stop_after_attempt=3)
async def fetch1():
    pass
"""
    code2 = """
from aiocache import cached

@cached(ttl=300)
async def fetch2():
    pass
"""
    create_python_file(temp_repo, "file1.py", code1)
    create_python_file(temp_repo, "file2.py", code2)

    skills = await skill_extractor.extract_skills(
        repo_path=temp_repo,
        skill_types=[SkillType.RETRY, SkillType.CACHING],
    )

    # Should find skills from both files
    assert len(skills) >= 2
    skill_types = {s.skill_type for s in skills}
    assert SkillType.RETRY in skill_types
    assert SkillType.CACHING in skill_types


@pytest.mark.asyncio
async def test_extracted_skill_structure(skill_extractor, temp_repo):
    """Test that ExtractedSkill has correct structure."""
    code = """
from tenacity import retry

@retry(stop_after_attempt=3)
async def fetch():
    pass
"""
    create_python_file(temp_repo, "test.py", code)

    skills = await skill_extractor.extract_skills(
        repo_path=temp_repo,
        skill_types=[SkillType.RETRY],
    )

    skill = skills[0]

    assert hasattr(skill, "skill_type")
    assert hasattr(skill, "name")
    assert hasattr(skill, "description")
    assert hasattr(skill, "code_snippet")
    assert hasattr(skill, "file_path")
    assert hasattr(skill, "line_start")
    assert hasattr(skill, "line_end")
    assert hasattr(skill, "confidence")
    assert hasattr(skill, "dependencies")
    assert hasattr(skill, "metadata")

    assert isinstance(skill.skill_type, SkillType)
    assert isinstance(skill.name, str)
    assert isinstance(skill.description, str)
    assert isinstance(skill.code_snippet, str)
    assert isinstance(skill.file_path, str)
    assert isinstance(skill.line_start, int)
    assert isinstance(skill.line_end, int)
    assert isinstance(skill.confidence, float)
    assert isinstance(skill.dependencies, list)
    assert isinstance(skill.metadata, dict)


@pytest.mark.asyncio
async def test_confidence_scoring(skill_extractor, temp_repo):
    """Test confidence scoring for different patterns."""
    # Perfect match: decorator + library
    code1 = """
from tenacity import retry

@retry(stop_after_attempt=3)
async def fetch():
    pass
"""
    create_python_file(temp_repo, "perfect.py", code1)

    skills = await skill_extractor.extract_skills(
        repo_path=temp_repo,
        skill_types=[SkillType.RETRY],
    )

    # Decorator usage should have confidence 1.0
    assert skills[0].confidence == 1.0


@pytest.mark.asyncio
async def test_skip_invalid_python(skill_extractor, temp_repo):
    """Test that invalid Python files are skipped."""
    # Create invalid Python file
    invalid_code = "this is not valid python {{"
    create_python_file(temp_repo, "invalid.py", invalid_code)

    # Should not crash, just skip the file
    skills = await skill_extractor.extract_skills(repo_path=temp_repo)

    # Should return empty list (no valid skills)
    assert len(skills) == 0


@pytest.mark.asyncio
async def test_empty_repository(skill_extractor, temp_repo):
    """Test extracting from empty repository."""
    skills = await skill_extractor.extract_skills(repo_path=temp_repo)

    assert len(skills) == 0


@pytest.mark.asyncio
async def test_code_snippet_extraction(skill_extractor, temp_repo):
    """Test that code snippet is correctly extracted."""
    code = """
from tenacity import retry

@retry(stop_after_attempt=3)
async def fetch():
    return await api.get()
"""
    create_python_file(temp_repo, "snippet.py", code)

    skills = await skill_extractor.extract_skills(
        repo_path=temp_repo,
        skill_types=[SkillType.RETRY],
    )

    skill = skills[0]

    # Code snippet should contain the function
    assert "@retry" in skill.code_snippet
    assert "async def fetch" in skill.code_snippet
    assert "return await api.get()" in skill.code_snippet
