# AIM/tests/teacher/test_teacher_agent.py
import pytest
import tempfile
from pathlib import Path
from AIM.src.aim.teacher.teacher_agent import TeacherAgent


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
