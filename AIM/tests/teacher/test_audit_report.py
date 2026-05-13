# AIM/tests/teacher/test_audit_report.py
import pytest
from pathlib import Path
from AIM.src.aim.teacher.audit_report import AuditReportGenerator, AuditResult
from AIM.src.aim.teacher.gap_detector import Gap, GapSeverity


def test_generate_report():
    """Test generating audit report."""
    gaps = [
        Gap(
            pattern="circuit_breaker",
            severity=GapSeverity.CRITICAL,
            description="Missing circuit breaker",
            recommendation="Add pybreaker",
        ),
        Gap(
            pattern="retry",
            severity=GapSeverity.HIGH,
            description="Missing retry logic",
            recommendation="Add tenacity",
        ),
    ]

    result = AuditResult(
        subagent_name="content_writer_agent",
        github_repos=["user/repo1", "user/repo2"],
        gaps=gaps,
        score=60.0,
    )

    generator = AuditReportGenerator()
    report = generator.generate(result)

    assert "content_writer_agent" in report
    assert "circuit_breaker" in report
    assert "CRITICAL" in report
    assert "60.0" in report


def test_save_report():
    """Test saving report to file."""
    result = AuditResult(
        subagent_name="test_agent",
        github_repos=[],
        gaps=[],
        score=100.0,
    )

    generator = AuditReportGenerator()

    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "report.md"
        generator.save(result, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "test_agent" in content
