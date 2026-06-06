"""
Integration test for full teaching workflow (Steps 1-8).

Tests the complete end-to-end teaching process:
1. Research and clone repos
2. Extract skills
3. Compare and rank
4. Extract best implementation
5. Apply to codebase
6. Run tests
7. Git commit
"""

import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.aim.teacher.skills.skill_teacher import SkillTeacher


@pytest.mark.asyncio
async def test_teach_subagent_end_to_end(tmp_path):
    """Test complete teaching workflow Steps 1-8."""
    # Setup git repo
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    # Create initial commit (git requires at least one commit)
    readme = tmp_path / "README.md"
    readme.write_text("# Test Project")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    # Setup teacher
    teacher = SkillTeacher(project_root=tmp_path)

    # Mock the research and clone step (Step 1)
    mock_repo_path = tmp_path / "mock_repo"
    mock_repo_path.mkdir()
    (mock_repo_path / "circuit_breaker.py").write_text(
        """
class CircuitBreaker:
    def __init__(self):
        self.failures = 0

    def call(self, func):
        try:
            return func()
        except Exception:
            self.failures += 1
            raise
"""
    )

    with patch.object(
        teacher.selector,
        "research_and_clone",
        return_value={"https://github.com/test/repo": mock_repo_path},
    ):
        # Mock skill extraction (Step 2)
        from src.aim.teacher.skills.skill_selector import Skill

        mock_skill = Skill(
            name="circuit_breaker",
            description="Circuit breaker pattern",
            code_example="class CircuitBreaker:\n    pass",
            quality_score=85.0,
            source_repo="https://github.com/test/repo",
            file_path=str(mock_repo_path / "circuit_breaker.py"),
        )

        with patch.object(
            teacher.selector, "extract_skills", return_value=[mock_skill]
        ):
            # Mock comparison (Step 3)
            from src.aim.teacher.skills.skill_comparator import ComparisonResult

            mock_comparison = ComparisonResult(
                ranked_skills=[mock_skill],
                best_skill=mock_skill,
                dimension_scores={},
            )

            with patch.object(
                teacher.comparator, "compare", return_value=mock_comparison
            ):
                # Mock extraction (Step 4)
                from src.aim.teacher.skills.skill_extractor import (
                    ExtractedImplementation,
                )

                mock_implementation = ExtractedImplementation(
                    code="class CircuitBreaker:\n    pass",
                    dependencies=["pybreaker>=1.0.0"],
                    integration_instructions="Add to error handling",
                    suggested_path=tmp_path / "circuit_breaker.py",
                )

                with patch.object(
                    teacher.extractor, "extract", return_value=mock_implementation
                ):
                    # Mock application (Step 5)
                    from src.aim.teacher.skills.skill_applier import (
                        ApplicationResult,
                    )

                    test_file = tmp_path / "test_circuit_breaker.py"
                    test_file.write_text("def test_pass(): assert True")

                    mock_application = ApplicationResult(
                        success=True,
                        files_created=[tmp_path / "circuit_breaker.py"],
                        files_modified=[],
                        dependencies_added=["pybreaker>=1.0.0"],
                        tests_created=[test_file],
                        error=None,
                    )

                    # Create the files that application claims to create
                    (tmp_path / "circuit_breaker.py").write_text(
                        "class CircuitBreaker:\n    pass"
                    )

                    with patch.object(
                        teacher.applier, "apply", return_value=mock_application
                    ):
                        # Execute full workflow
                        import os

                        original_cwd = os.getcwd()
                        os.chdir(tmp_path)

                        try:
                            report = await teacher.teach_subagent("test", "test domain")

                            # Verify Steps 1-6
                            assert report.repos_found == 1
                            assert report.repos_cloned == 1
                            assert report.skills_extracted == 1
                            assert report.best_skill is not None
                            assert report.best_skill.name == "circuit_breaker"
                            assert len(report.files_created) == 1
                            assert len(report.tests_created) == 1

                            # Verify Step 7 (Test)
                            assert report.test_results is not None
                            assert report.test_results.success
                            assert "test_circuit_breaker.py" in report.test_results.output

                            # Verify Step 8 (Commit)
                            assert report.commit_hash is not None
                            assert len(report.commit_hash) == 40  # Git SHA-1
                            assert report.success

                            # Verify git commit exists
                            result = subprocess.run(
                                ["git", "log", "--oneline", "-1"],
                                cwd=tmp_path,
                                capture_output=True,
                                text=True,
                            )
                            assert "teach(test)" in result.stdout

                        finally:
                            os.chdir(original_cwd)
