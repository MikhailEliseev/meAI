# AIM/tests/teacher/test_teacher_agent.py
import pytest
import tempfile
import logging
import sys
from pathlib import Path
from AIM.src.aim.teacher.teacher_agent import TeacherAgent
import structlog

# Enable debug logging for tests
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.DEBUG,
)

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


def test_audit_subagent():
    """Test auditing a single subagent."""
    teacher = TeacherAgent()

    # Create a simple subagent file
    with tempfile.TemporaryDirectory() as tmpdir:
        subagent_file = Path(tmpdir) / "test_agent.py"
        subagent_file.write_text("""
import requests

class TestAgent:
    def __init__(self):
        self.url = "http://example.com"

    def fetch(self):
        return requests.get(self.url)
""")

        result = teacher.audit_subagent(subagent_file)

        assert result is not None
        assert hasattr(result, "subagent_name")
        assert hasattr(result, "score")
        assert hasattr(result, "gaps")


def test_audit_all():
    """Test auditing all subagents."""
    teacher = TeacherAgent()

    # Mock the inventory to return only one subagent for faster testing
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test_subagent.py"
        test_file.write_text("# Test subagent\nclass TestAgent:\n    pass\n")

        # Mock inventory.scan() to return just our test file
        from unittest.mock import Mock
        mock_subagent = Mock()
        mock_subagent.name = "test_subagent"
        mock_subagent.path = str(test_file)
        teacher.inventory.scan = Mock(return_value=[mock_subagent])

        results = teacher.audit_all()

        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0].subagent_name == "test_subagent"


@pytest.mark.asyncio
async def test_teach_subagent():
    """Test teaching ci-content subagent with detailed scoring logs."""
    teacher = TeacherAgent()

    # Path to ci-content subagent
    subagent_path = Path("AIM/src/aim/subagents/ci_content.py")

    # Step 1: Deep audit to find skills
    skills = await teacher.deep_audit_subagent(
        subagent_path=subagent_path,
        subagent_name="ci-content",
        domain="content extraction and SEO analysis"
    )

    print(f"\n=== Skills Found ===")
    print(f"Total skills: {len(skills)}")

    # Skip if no skills (GitHub rate limit)
    if len(skills) == 0:
        print("No skills found (GitHub rate limit). Using cached results from /tmp/teacher_repos")
        # Re-extract from already cloned repos
        import asyncio

        repos_dir = Path("/tmp/teacher_repos/ci-content")
        if repos_dir.exists():
            for repo_dir in repos_dir.iterdir():
                if repo_dir.is_dir():
                    extracted = await teacher.skill_selector.extract_skills(repo_dir, "ci-content")
                    for skill in extracted:
                        skill.source_repo = f"https://github.com/.../{repo_dir.name}"
                    skills.extend(extracted)

        print(f"Re-extracted skills: {len(skills)}")

    # Step 2: Create target context
    from AIM.src.aim.teacher.skills.skill_applier import TargetContext
    target_context = TargetContext(
        subagent_name="ci-content",
        is_async=False,
        libraries={"requests", "httpx"},
        error_style="raise",
        base_classes=[],
        imports=set(),
    )

    print(f"\n=== Target Context ===")
    print(f"Subagent: {target_context.subagent_name}")
    print(f"Is async: {target_context.is_async}")
    print(f"Libraries: {target_context.libraries}")
    print(f"Error style: {target_context.error_style}")

    # Step 3: Compare solutions with context
    comparison = await teacher.skill_comparator.compare_with_context(skills, target_context)

    print(f"\n=== Comparison Result ===")
    print(f"Best skill: {comparison.best_skill.name if comparison.best_skill else 'None'}")
    print(f"Best score: {comparison.best_skill.quality_score if comparison.best_skill else 0}")
    print(f"Source: {comparison.best_skill.source_repo if comparison.best_skill else 'None'}")

    # Show top 5 skills
    print(f"\n=== Top 5 Skills ===")
    for i, skill in enumerate(comparison.ranked_skills[:5], 1):
        print(f"{i}. {skill.name} (score: {skill.quality_score:.2f}) - {skill.source_repo}")

    assert comparison.best_skill is not None
    assert len(comparison.ranked_skills) > 0


