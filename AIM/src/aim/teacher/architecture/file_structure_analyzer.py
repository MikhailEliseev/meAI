"""
FileStructureAnalyzer - Analyze repository file structure.

Scans directory structure and identifies file types:
- Entry points (main.py, __init__.py)
- Clients (*_client.py, *_api.py)
- Models (*_model.py, *schema.py)
- Tests (test_*.py, *_test.py)
- Configs (settings.py, config.py)
- Utils (utils/, helpers/)
"""

from dataclasses import dataclass
from pathlib import Path

import structlog

logger = structlog.get_logger()


@dataclass
class FileStructure:
    """Repository file structure analysis result."""

    entry_points: list[str]  # main.py, __init__.py
    clients: list[str]  # *client.py, *api.py
    models: list[str]  # *model.py, *schema.py
    tests: list[str]  # test_*.py
    configs: list[str]  # settings.py, config.py
    utils: list[str]  # utils/, helpers/


class FileStructureAnalyzer:
    """
    Analyze repository file structure.

    Responsibilities:
    - Scan directory structure recursively
    - Identify file types by patterns
    - Categorize files by purpose
    - Ignore hidden files and directories
    """

    def __init__(self):
        self.logger = logger.bind(component="file_structure_analyzer")

        # File patterns for identification
        self.entry_point_patterns = ["main.py", "__init__.py", "app.py", "run.py"]
        self.client_patterns = ["*client.py", "*api.py", "*_client.py", "*_api.py"]
        self.model_patterns = [
            "*model.py",
            "*schema.py",
            "*_model.py",
            "*_schema.py",
            "models.py",
        ]
        self.test_patterns = ["test_*.py", "*_test.py"]
        self.config_patterns = [
            "settings.py",
            "config.py",
            "configuration.py",
            ".env",
            "*.yaml",
            "*.yml",
            "*.toml",
        ]
        self.util_patterns = ["utils/", "helpers/", "common/", "lib/"]

    async def analyze(self, repo_path: Path) -> FileStructure:
        """
        Analyze repository file structure.

        Args:
            repo_path: Path to repository root

        Returns:
            FileStructure with categorized files

        Raises:
            FileNotFoundError: If repo_path does not exist
            NotADirectoryError: If repo_path is not a directory
        """
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {repo_path}")

        if not repo_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {repo_path}")

        self.logger.info("analyzing_file_structure", repo_path=str(repo_path))

        # Scan all Python files
        all_files = self._scan_python_files(repo_path)

        # Categorize files
        entry_points = self._find_entry_points(all_files)
        clients = self._find_clients(all_files)
        models = self._find_models(all_files)
        tests = self._find_tests(all_files)
        configs = self._find_configs(all_files)
        utils = self._find_utils(all_files)

        self.logger.info(
            "file_structure_analyzed",
            entry_points=len(entry_points),
            clients=len(clients),
            models=len(models),
            tests=len(tests),
            configs=len(configs),
            utils=len(utils),
        )

        return FileStructure(
            entry_points=entry_points,
            clients=clients,
            models=models,
            tests=tests,
            configs=configs,
            utils=utils,
        )

    def _scan_python_files(self, repo_path: Path) -> list[Path]:
        """
        Scan all Python files in repository.

        Args:
            repo_path: Repository root path

        Returns:
            List of Python file paths (relative to repo_path)
        """
        python_files = []

        for file_path in repo_path.rglob("*.py"):
            # Skip hidden files and directories
            if any(part.startswith(".") for part in file_path.parts):
                continue

            # Skip __pycache__
            if "__pycache__" in file_path.parts:
                continue

            # Store relative path
            relative_path = file_path.relative_to(repo_path)
            python_files.append(relative_path)

        return python_files

    def _find_entry_points(self, files: list[Path]) -> list[str]:
        """Find entry point files."""
        entry_points = []

        for file_path in files:
            file_name = file_path.name
            if file_name in self.entry_point_patterns:
                entry_points.append(file_name)

        return entry_points

    def _find_clients(self, files: list[Path]) -> list[str]:
        """Find client files."""
        clients = []

        for file_path in files:
            file_name = file_path.name
            # Check if matches any client pattern
            if any(
                self._match_pattern(file_name, pattern)
                for pattern in self.client_patterns
            ):
                clients.append(file_name)

        return clients

    def _find_models(self, files: list[Path]) -> list[str]:
        """Find model files."""
        models = []

        for file_path in files:
            file_name = file_path.name
            # Check if matches any model pattern
            if any(
                self._match_pattern(file_name, pattern)
                for pattern in self.model_patterns
            ):
                models.append(file_name)

        return models

    def _find_tests(self, files: list[Path]) -> list[str]:
        """Find test files."""
        tests = []

        for file_path in files:
            file_name = file_path.name
            # Check if matches any test pattern
            if any(
                self._match_pattern(file_name, pattern) for pattern in self.test_patterns
            ):
                tests.append(str(file_path))

        return tests

    def _find_configs(self, files: list[Path]) -> list[str]:
        """Find configuration files."""
        configs = []

        for file_path in files:
            file_name = file_path.name
            # Check if matches any config pattern
            if any(
                self._match_pattern(file_name, pattern)
                for pattern in self.config_patterns
            ):
                configs.append(file_name)

        return configs

    def _find_utils(self, files: list[Path]) -> list[str]:
        """Find utility files."""
        utils = []

        for file_path in files:
            # Check if file is in utils directory
            if any(util_dir in file_path.parts for util_dir in ["utils", "helpers", "common", "lib"]):
                utils.append(str(file_path))

        return utils

    def _match_pattern(self, file_name: str, pattern: str) -> bool:
        """
        Match file name against pattern.

        Supports wildcards:
        - *client.py matches api_client.py, http_client.py
        - test_*.py matches test_api.py, test_models.py

        Args:
            file_name: File name to match
            pattern: Pattern with wildcards

        Returns:
            True if matches, False otherwise
        """
        if "*" not in pattern:
            return file_name == pattern

        # Simple wildcard matching
        if pattern.startswith("*"):
            suffix = pattern[1:]
            return file_name.endswith(suffix)
        elif pattern.endswith("*"):
            prefix = pattern[:-1]
            return file_name.startswith(prefix)
        else:
            # Pattern like *_client.py
            parts = pattern.split("*")
            if len(parts) == 2:
                prefix, suffix = parts
                return file_name.startswith(prefix) and file_name.endswith(suffix)

        return False
