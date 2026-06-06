"""
Tests for SkillApplier.

Tests:
- Code application to files
- Dependency management
- Test generation
- File creation/modification tracking
"""

from pathlib import Path

import pytest

from src.aim.teacher.skills.skill_applier import (
    ApplicationResult,
    SkillApplier,
)
from src.aim.teacher.skills.skill_extractor import ExtractedImplementation


@pytest.fixture
def applier(tmp_path):
    """Create SkillApplier instance with temp project root."""
    return SkillApplier(project_root=tmp_path)


@pytest.fixture
def sample_implementation():
    """Create sample extracted implementation."""
    return ExtractedImplementation(
        code="""
import asyncio
from pathlib import Path

class SampleClient:
    def __init__(self):
        self.name = "sample"

    async def fetch_data(self):
        return {"status": "ok"}
""",
        dependencies=["httpx>=0.27.0", "structlog>=24.1.0"],
        integration_instructions="Add to subagents directory",
        suggested_path=Path("AIM/src/aim/subagents/sample_client.py"),
    )


class TestCodeApplication:
    """Test code application to files."""

    @pytest.mark.asyncio
    async def test_apply_creates_file(self, applier, sample_implementation):
        """Should create new file with code."""
        result = await applier.apply(
            sample_implementation,
            subagent_name="test",
        )

        assert result.success
        assert len(result.files_created) == 1
        assert result.files_created[0].exists()

    @pytest.mark.asyncio
    async def test_apply_adds_header(self, applier, sample_implementation):
        """Should add header comment to file."""
        result = await applier.apply(
            sample_implementation,
            subagent_name="test",
        )

        created_file = result.files_created[0]
        content = created_file.read_text()

        assert '"""' in content
        assert "Teacher Agent" in content
        assert "Test" in content

    @pytest.mark.asyncio
    async def test_apply_preserves_code(self, applier, sample_implementation):
        """Should preserve original code structure."""
        result = await applier.apply(
            sample_implementation,
            subagent_name="test",
        )

        created_file = result.files_created[0]
        content = created_file.read_text()

        assert "class SampleClient" in content
        assert "async def fetch_data" in content

    @pytest.mark.asyncio
    async def test_apply_with_custom_path(self, applier, sample_implementation, tmp_path):
        """Should use custom target path."""
        custom_path = Path("custom/location/client.py")

        result = await applier.apply(
            sample_implementation,
            target_path=custom_path,
            subagent_name="test",
        )

        assert result.success
        expected_path = tmp_path / custom_path
        assert expected_path.exists()

    @pytest.mark.asyncio
    async def test_apply_modifies_existing_file(self, applier, sample_implementation, tmp_path):
        """Should modify existing file."""
        target_path = tmp_path / sample_implementation.suggested_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text("# Existing content")

        result = await applier.apply(
            sample_implementation,
            subagent_name="test",
        )

        assert result.success
        assert len(result.files_modified) == 1
        assert len(result.files_created) == 0


class TestDependencyManagement:
    """Test dependency management."""

    @pytest.mark.asyncio
    async def test_add_dependencies_to_requirements(self, applier, sample_implementation, tmp_path):
        """Should add dependencies to requirements.txt."""
        result = await applier.apply(
            sample_implementation,
            subagent_name="test",
        )

        requirements_path = tmp_path / "requirements.txt"
        assert requirements_path.exists()

        content = requirements_path.read_text()
        assert "httpx>=0.27.0" in content
        assert "structlog>=24.1.0" in content

    @pytest.mark.asyncio
    async def test_skip_duplicate_dependencies(self, applier, sample_implementation, tmp_path):
        """Should skip dependencies that already exist."""
        # Create requirements.txt with existing dependency
        requirements_path = tmp_path / "requirements.txt"
        requirements_path.write_text("httpx>=0.27.0\n")

        result = await applier.apply(
            sample_implementation,
            subagent_name="test",
        )

        # Should only add structlog (httpx already exists)
        assert len(result.dependencies_added) == 1
        assert "structlog>=24.1.0" in result.dependencies_added

    @pytest.mark.asyncio
    async def test_add_comment_for_new_dependencies(self, applier, sample_implementation, tmp_path):
        """Should add comment when adding dependencies."""
        result = await applier.apply(
            sample_implementation,
            subagent_name="test",
        )

        requirements_path = tmp_path / "requirements.txt"
        content = requirements_path.read_text()

        assert "# Added by Teacher Agent" in content


class TestTestGeneration:
    """Test test file generation."""

    @pytest.mark.asyncio
    async def test_generate_test_file(self, applier, sample_implementation):
        """Should generate test file."""
        result = await applier.apply(
            sample_implementation,
            subagent_name="test",
        )

        assert len(result.tests_created) == 1
        test_file = result.tests_created[0]
        assert test_file.exists()
        assert "test_" in test_file.name

    @pytest.mark.asyncio
    async def test_test_file_has_imports(self, applier, sample_implementation):
        """Should include proper imports in test file."""
        result = await applier.apply(
            sample_implementation,
            subagent_name="test",
        )

        test_file = result.tests_created[0]
        content = test_file.read_text()

        assert "import pytest" in content
        assert "from" in content
        assert "import" in content

    @pytest.mark.asyncio
    async def test_test_file_has_test_class(self, applier, sample_implementation):
        """Should generate test class for detected classes."""
        result = await applier.apply(
            sample_implementation,
            subagent_name="test",
        )

        test_file = result.tests_created[0]
        content = test_file.read_text()

        assert "class TestSampleClient" in content
        assert "test_sampleclient_creation" in content

    @pytest.mark.asyncio
    async def test_test_file_has_async_markers(self, applier, sample_implementation):
        """Should add pytest.mark.asyncio for async tests."""
        result = await applier.apply(
            sample_implementation,
            subagent_name="test",
        )

        test_file = result.tests_created[0]
        content = test_file.read_text()

        assert "@pytest.mark.asyncio" in content


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_handle_empty_code(self, applier, tmp_path):
        """Should handle empty code gracefully."""
        empty_impl = ExtractedImplementation(
            code="",
            dependencies=[],
            integration_instructions="",
            suggested_path=Path("test.py"),
        )

        result = await applier.apply(empty_impl, subagent_name="test")

        # Should still succeed (creates empty file)
        assert result.success

    @pytest.mark.asyncio
    async def test_handle_no_target_path(self, applier):
        """Should fail if no target path specified."""
        impl = ExtractedImplementation(
            code="print('test')",
            dependencies=[],
            integration_instructions="",
            suggested_path=None,  # No path
        )

        result = await applier.apply(impl, target_path=None, subagent_name="test")

        assert not result.success
        assert result.error == "No target path specified"


class TestCodeAdaptation:
    """Test code adaptation to project conventions."""

    @pytest.mark.asyncio
    async def test_adapt_indented_code(self, applier, tmp_path):
        """Should dedent indented code."""
        impl = ExtractedImplementation(
            code="""
    def test():
        return True
""",
            dependencies=[],
            integration_instructions="",
            suggested_path=Path("test.py"),
        )

        result = await applier.apply(impl, subagent_name="test")

        created_file = result.files_created[0]
        content = created_file.read_text()

        # Code should be dedented
        assert "def test():" in content
        assert "    return True" in content

    @pytest.mark.asyncio
    async def test_add_missing_imports(self, applier, tmp_path):
        """Should add basic imports if missing."""
        impl = ExtractedImplementation(
            code="""
async def fetch():
    path = Path("/tmp")
    return path
""",
            dependencies=[],
            integration_instructions="",
            suggested_path=Path("test.py"),
        )

        result = await applier.apply(impl, subagent_name="test")

        created_file = result.files_created[0]
        content = created_file.read_text()

        # Should add asyncio and Path imports
        assert "import asyncio" in content or "from pathlib import Path" in content
