"""
Tests for FileStructureAnalyzer.

Tests:
- Directory scanning
- File type identification
- Entry point detection
- Configuration file detection
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.aim.teacher.architecture.file_structure_analyzer import (
    FileStructure,
    FileStructureAnalyzer,
)


@pytest.fixture
def analyzer():
    """Create FileStructureAnalyzer instance."""
    return FileStructureAnalyzer()


@pytest.fixture
def sample_repo(tmp_path):
    """Create sample repository structure."""
    repo = tmp_path / "sample_repo"
    repo.mkdir()

    # Entry points
    (repo / "__init__.py").write_text("# Package init")
    (repo / "main.py").write_text("# Main entry point")

    # Clients
    (repo / "api_client.py").write_text("# API client")
    (repo / "http_client.py").write_text("# HTTP client")

    # Models
    (repo / "models.py").write_text("# Data models")
    (repo / "schema.py").write_text("# Schema definitions")

    # Tests
    tests_dir = repo / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_client.py").write_text("# Client tests")
    (tests_dir / "test_models.py").write_text("# Model tests")

    # Config
    (repo / "settings.py").write_text("# Settings")
    (repo / "config.py").write_text("# Configuration")

    # Utils
    utils_dir = repo / "utils"
    utils_dir.mkdir()
    (utils_dir / "helpers.py").write_text("# Helper functions")

    return repo


class TestFileScanning:
    """Test directory scanning."""

    @pytest.mark.asyncio
    async def test_scan_directory_structure(self, analyzer, sample_repo):
        """Should scan all files in directory."""
        structure = await analyzer.analyze(sample_repo)

        assert isinstance(structure, FileStructure)
        assert len(structure.entry_points) > 0
        assert len(structure.clients) > 0
        assert len(structure.models) > 0
        assert len(structure.tests) > 0
        assert len(structure.configs) > 0
        assert len(structure.utils) > 0

    @pytest.mark.asyncio
    async def test_ignore_hidden_files(self, analyzer, tmp_path):
        """Should ignore hidden files and directories."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / ".gitignore").write_text("*.pyc")
        (repo / "main.py").write_text("# Main")

        structure = await analyzer.analyze(repo)

        # Should not include .git or .gitignore
        all_files = (
            structure.entry_points
            + structure.clients
            + structure.models
            + structure.tests
            + structure.configs
            + structure.utils
        )
        assert not any(".git" in f for f in all_files)

    @pytest.mark.asyncio
    async def test_handle_empty_directory(self, analyzer, tmp_path):
        """Should handle empty directory gracefully."""
        empty_repo = tmp_path / "empty"
        empty_repo.mkdir()

        structure = await analyzer.analyze(empty_repo)

        assert len(structure.entry_points) == 0
        assert len(structure.clients) == 0
        assert len(structure.models) == 0
        assert len(structure.tests) == 0
        assert len(structure.configs) == 0
        assert len(structure.utils) == 0


class TestFileTypeIdentification:
    """Test file type identification."""

    @pytest.mark.asyncio
    async def test_identify_entry_points(self, analyzer, sample_repo):
        """Should identify entry point files."""
        structure = await analyzer.analyze(sample_repo)

        assert "main.py" in structure.entry_points
        assert "__init__.py" in structure.entry_points

    @pytest.mark.asyncio
    async def test_identify_clients(self, analyzer, sample_repo):
        """Should identify client files."""
        structure = await analyzer.analyze(sample_repo)

        assert "api_client.py" in structure.clients
        assert "http_client.py" in structure.clients

    @pytest.mark.asyncio
    async def test_identify_models(self, analyzer, sample_repo):
        """Should identify model files."""
        structure = await analyzer.analyze(sample_repo)

        assert "models.py" in structure.models
        assert "schema.py" in structure.models

    @pytest.mark.asyncio
    async def test_identify_tests(self, analyzer, sample_repo):
        """Should identify test files."""
        structure = await analyzer.analyze(sample_repo)

        assert any("test_client.py" in t for t in structure.tests)
        assert any("test_models.py" in t for t in structure.tests)

    @pytest.mark.asyncio
    async def test_identify_configs(self, analyzer, sample_repo):
        """Should identify configuration files."""
        structure = await analyzer.analyze(sample_repo)

        assert "settings.py" in structure.configs
        assert "config.py" in structure.configs

    @pytest.mark.asyncio
    async def test_identify_utils(self, analyzer, sample_repo):
        """Should identify utility files."""
        structure = await analyzer.analyze(sample_repo)

        assert any("helpers.py" in u for u in structure.utils)


class TestPatternMatching:
    """Test file pattern matching."""

    @pytest.mark.asyncio
    async def test_match_client_patterns(self, analyzer, tmp_path):
        """Should match various client file patterns."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "api_client.py").write_text("# API")
        (repo / "http_api.py").write_text("# HTTP API")
        (repo / "rest_client.py").write_text("# REST")

        structure = await analyzer.analyze(repo)

        assert len(structure.clients) == 3

    @pytest.mark.asyncio
    async def test_match_model_patterns(self, analyzer, tmp_path):
        """Should match various model file patterns."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "models.py").write_text("# Models")
        (repo / "schema.py").write_text("# Schema")
        (repo / "data_model.py").write_text("# Data model")

        structure = await analyzer.analyze(repo)

        assert len(structure.models) == 3

    @pytest.mark.asyncio
    async def test_match_test_patterns(self, analyzer, tmp_path):
        """Should match various test file patterns."""
        repo = tmp_path / "repo"
        repo.mkdir()
        tests_dir = repo / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_api.py").write_text("# Test")
        (tests_dir / "test_models.py").write_text("# Test")
        (repo / "api_test.py").write_text("# Test")

        structure = await analyzer.analyze(repo)

        assert len(structure.tests) == 3


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handle_nonexistent_directory(self, analyzer, tmp_path):
        """Should handle nonexistent directory."""
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError):
            await analyzer.analyze(nonexistent)

    @pytest.mark.asyncio
    async def test_handle_file_instead_of_directory(self, analyzer, tmp_path):
        """Should handle file path instead of directory."""
        file_path = tmp_path / "file.py"
        file_path.write_text("# File")

        with pytest.raises(NotADirectoryError):
            await analyzer.analyze(file_path)

    @pytest.mark.asyncio
    async def test_handle_deeply_nested_structure(self, analyzer, tmp_path):
        """Should handle deeply nested directory structure."""
        repo = tmp_path / "repo"
        deep_path = repo / "a" / "b" / "c" / "d"
        deep_path.mkdir(parents=True)
        (deep_path / "deep_client.py").write_text("# Deep client")

        structure = await analyzer.analyze(repo)

        assert any("deep_client.py" in c for c in structure.clients)
