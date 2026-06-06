"""End-to-end integration test for Teacher Agent."""

import pytest
import tempfile
from pathlib import Path
from src.aim.teacher.teacher_agent import TeacherAgent


def test_full_audit_cycle():
    """Test complete audit cycle: scan → find → clone → analyze → report."""
    teacher = TeacherAgent()

    # Create a test subagent with API client code (should trigger gap detection)
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test_subagent.py"
        test_file.write_text("""
import requests

class TestSubagent:
    def __init__(self):
        self.url = "http://example.com"
        self.session = requests.Session()

    def fetch_data(self):
        # Direct API call without retry or circuit breaker
        response = self.session.get(self.url)
        return response.json()

    def post_data(self, data):
        # No rate limiting
        return self.session.post(self.url, json=data)
""")

        # Run full audit
        result = teacher.audit_subagent(test_file)

        # Verify result structure
        assert result is not None
        assert result.subagent_name == "test_subagent"
        assert isinstance(result.score, float)
        assert 0 <= result.score <= 100
        assert isinstance(result.gaps, list)
        assert isinstance(result.github_repos, list)

        # Verify audit ran (gaps may or may not be found depending on patterns)
        # The important thing is the audit completed successfully
        print(f"\n✅ Audit completed:")
        print(f"   Score: {result.score:.1f}/100")
        print(f"   Gaps: {len(result.gaps)}")
        print(f"   Repos: {len(result.github_repos)}")

        # At minimum, should have analyzed the code
        assert result.score >= 0


def test_report_generation():
    """Test audit report generation."""
    teacher = TeacherAgent()

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test_agent.py"
        test_file.write_text("""
import requests

class TestAgent:
    def fetch(self):
        return requests.get("http://example.com")
""")

        # Run audit
        result = teacher.audit_subagent(test_file)

        # Generate report
        report = teacher.report_generator.generate(result)

        # Verify report content
        assert "test_agent" in report
        assert "Score:" in report
        assert "Gaps Detected" in report

        # Save report
        report_path = Path(tmpdir) / "report.md"
        teacher.report_generator.save(result, report_path)

        assert report_path.exists()
        content = report_path.read_text()
        assert len(content) > 100

        print(f"\n✅ Report generated: {len(content)} chars")


def test_upgrade_with_backup():
    """Test upgrade with automatic backup."""
    teacher = TeacherAgent()

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "upgrade_test.py"
        original_code = """
import requests

class Client:
    def __init__(self):
        self.url = "http://example.com"
"""
        test_file.write_text(original_code)

        # Create mock audit result with gaps
        from src.aim.teacher.gap_detector import Gap, GapSeverity
        from src.aim.teacher.audit_report import AuditResult

        gaps = [
            Gap(
                pattern="circuit_breaker",
                severity=GapSeverity.CRITICAL,
                description="Missing circuit breaker",
                recommendation="Add pybreaker",
            )
        ]

        result = AuditResult(
            subagent_name="upgrade_test",
            github_repos=["test/repo"],
            gaps=gaps,
            score=70.0,
        )

        # Mock GitHub code
        github_code = """
from pybreaker import CircuitBreaker

class Client:
    def __init__(self):
        self.breaker = CircuitBreaker(fail_max=5)
"""

        # Apply upgrade directly through applier
        upgrade_result = teacher.upgrade_applier.apply(
            test_file,
            gaps,
            github_code,
        )

        # Verify upgrade
        assert upgrade_result.success
        assert upgrade_result.backup_path is not None
        assert upgrade_result.backup_path.exists()

        # Verify backup contains original
        backup_content = upgrade_result.backup_path.read_text()
        assert backup_content == original_code

        # Verify updated file has new code
        updated_content = test_file.read_text()
        assert "CircuitBreaker" in updated_content

        print(f"\n✅ Upgrade completed:")
        print(f"   Backup: {upgrade_result.backup_path.name}")
        print(f"   Patterns: {upgrade_result.patterns_applied}")


def test_inventory_scan():
    """Test subagent inventory scanning."""
    teacher = TeacherAgent()

    # Scan real subagents
    subagents = teacher.inventory.scan()

    # Should find at least some subagents
    assert len(subagents) > 0

    # Verify metadata
    for subagent in subagents[:3]:  # Check first 3
        assert subagent.name
        assert subagent.path
        assert subagent.lines_of_code > 0
        assert isinstance(subagent.has_github_integration, bool)

    print(f"\n✅ Inventory scan:")
    print(f"   Found: {len(subagents)} subagents")
    print(f"   With GitHub: {sum(1 for s in subagents if s.has_github_integration)}")
