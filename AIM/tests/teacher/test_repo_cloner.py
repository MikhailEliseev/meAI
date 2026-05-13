# AIM/tests/teacher/test_repo_cloner.py
import pytest
import tempfile
import shutil
from pathlib import Path
from AIM.src.aim.teacher.repo_cloner import RepoCloner


def test_clone_repo():
    """Test cloning a GitHub repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cloner = RepoCloner(base_dir=tmpdir)

        # Clone a small test repo
        result = cloner.clone("https://github.com/octocat/Hello-World")

        assert result.success
        assert result.path.exists()
        assert (result.path / ".git").exists()


def test_skip_existing_repo():
    """Test skipping already cloned repo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cloner = RepoCloner(base_dir=tmpdir)

        # Clone once
        result1 = cloner.clone("https://github.com/octocat/Hello-World")

        # Clone again (should skip)
        result2 = cloner.clone("https://github.com/octocat/Hello-World")

        assert result1.success
        assert result2.success
        assert result2.skipped
