# AIM/tests/teacher/test_upgrade_applier.py
import pytest
import tempfile
from pathlib import Path
from src.aim.teacher.upgrade_applier import UpgradeApplier
from src.aim.teacher.gap_detector import Gap, GapSeverity


def test_apply_upgrade():
    """Test applying upgrade to subagent."""
    original_code = """
import requests

class Client:
    def __init__(self):
        self.url = "http://example.com"

    def fetch(self):
        return requests.get(self.url)
"""

    gaps = [
        Gap(
            pattern="circuit_breaker",
            severity=GapSeverity.CRITICAL,
            description="Missing circuit breaker",
            recommendation="Add pybreaker",
        ),
    ]

    github_code = """
from pybreaker import CircuitBreaker

class Client:
    def __init__(self):
        self.breaker = CircuitBreaker(fail_max=5)
"""

    applier = UpgradeApplier()

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "client.py"
        file_path.write_text(original_code)

        result = applier.apply(file_path, gaps, github_code)

        assert result.success
        updated = file_path.read_text()
        assert "from pybreaker import CircuitBreaker" in updated
        assert "self.circuit_breaker" in updated
        assert "CircuitBreaker(" in updated


def test_backup_original():
    """Test backing up original file."""
    applier = UpgradeApplier()

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.py"
        file_path.write_text("original")

        backup_path = applier.backup(file_path)

        assert backup_path.exists()
        assert backup_path.read_text() == "original"
        assert ".backup" in str(backup_path)
